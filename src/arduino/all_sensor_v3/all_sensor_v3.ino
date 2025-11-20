#include <Wire.h>
#include <QMC5883LCompass.h>
#include <AltSoftSerial.h> // 取代 SoftwareSerial
#include <TinyGPSPlus.h>

float wc = 80.2; // 80.2 cm

// ===========================
// 霍爾變數
// ===========================
int hallACounter = 0, hallBCounter = 0, hallCCounter = 0;
int hallALast = 0, hallBLast = 0, hallCLast = 0;
unsigned long lastMicrosA = 0, lastMicrosB = 0, lastMicrosC = 0;
float rpsA = 0, rpsB = 0, rpsC = 0;

// ===========================
// 超音波變數
// ===========================
const int NUM_SENSORS = 5;
const int trigPins[NUM_SENSORS] = {2, 3, 4, 5, 6};
const int echoPins[NUM_SENSORS] = {7, 10, 11, 12, 13};
float HR_04_D[NUM_SENSORS] = {0, 0, 0, 0, 0};
int hr04_index = 0;

// ===========================
// 羅盤變數
// ===========================
float FacingAngle = 0;
QMC5883LCompass compass;

// 校正值
float x_offset = 200, y_offset = 1089.5, z_offset = -1137.5;
float x_scale = 0.75, y_scale = 0.71, z_scale = 3.97;

// ===========================
// GPS變數
// ===========================
static const uint32_t GPSBaud = 9600;
AltSoftSerial gpsSerial; // RX=8, TX=9
TinyGPSPlus gps;
double GPS_LAT = 0, GPS_LNG = 0;
unsigned long lastFixTime = 0;
const unsigned long timeout = 5000;

// ===========================
// GPS 校正 + 濾波變數
// ===========================
#define GPS_BUF_SIZE 5
double gpsLatBuf[GPS_BUF_SIZE] = {0};
double gpsLngBuf[GPS_BUF_SIZE] = {0};
int gpsBufIndex = 0;

// 靜態校正值（測量後設定）
double deltaLat = 0;
double deltaLng = 0;

// ---------------------------
// GPS 校正 + 移動平均副程式
// ---------------------------
void GPS_Filter(double rawLat, double rawLng, double hdop, double* outLat, double* outLng) {
    if (hdop <= 2.0) {
        double correctedLat = rawLat + deltaLat;
        double correctedLng = rawLng + deltaLng;

        gpsLatBuf[gpsBufIndex] = correctedLat;
        gpsLngBuf[gpsBufIndex] = correctedLng;
        gpsBufIndex = (gpsBufIndex + 1) % GPS_BUF_SIZE;

        double latSum = 0, lngSum = 0;
        for (int i = 0; i < GPS_BUF_SIZE; i++) {
            latSum += gpsLatBuf[i];
            lngSum += gpsLngBuf[i];
        }

        *outLat = latSum / GPS_BUF_SIZE;
        *outLng = lngSum / GPS_BUF_SIZE;
    } else {
        *outLat = gpsLatBuf[(gpsBufIndex + GPS_BUF_SIZE - 1) % GPS_BUF_SIZE];
        *outLng = gpsLngBuf[(gpsBufIndex + GPS_BUF_SIZE - 1) % GPS_BUF_SIZE];
    }
}

// ---------------------------
// 讀取 GPS
// ---------------------------
void GetGPS(double* GPS_lat , double* GPS_lng){
    while (gpsSerial.available() > 0) {
        gps.encode(gpsSerial.read());
    }

    if (gps.location.isValid()) {
        double rawLat = gps.location.lat();
        double rawLng = gps.location.lng();
        double hdop = gps.hdop.isValid() ? gps.hdop.value() / 100.0 : 10.0;

        GPS_Filter(rawLat, rawLng, hdop, GPS_lat, GPS_lng);
        lastFixTime = millis();
    }
}

// ---------------------------
// 霍爾感測器
// ---------------------------
void HallRead(int* hallCounter, int* hallLast ,float* rps ,unsigned long* lastMicros ,int *sensor) {
    if ((*hallLast == 0) && (*sensor > 512)) {
        *hallLast = 1;
        (*hallCounter)++;
        *rps = calculateRPS(lastMicros);
    } else if ((*hallLast == 1) && (*sensor < 512)) {
        *hallLast = 0;
    }
}

float calculateRPS(unsigned long* lastMicros) {
    unsigned long currentMicros = micros();
    unsigned long deltaMicros = currentMicros - *lastMicros;
    *lastMicros = currentMicros;

    if (deltaMicros == 0) return 0;
    float revPerMicros = 1.0 / (deltaMicros * 30);
    return revPerMicros * 1000000.0;
}

// ---------------------------
// 超音波
// ---------------------------
float readDistance(int trigPin, int echoPin) {
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    float duration = pulseIn(echoPin, HIGH, 12000); // timeout 12ms
    float distance = duration * 0.034 / 2;
    return distance;
}

// ---------------------------
// 羅盤
// ---------------------------
float readCompass(){
    compass.read();

    float x_corr = (compass.getX() - x_offset) * x_scale;
    float y_corr = (compass.getY() - y_offset) * y_scale;
    float z_corr = (compass.getZ() - z_offset) * z_scale;

    float heading = atan2(y_corr, x_corr) * 180.0 / PI;
    heading = 90.0 - heading;

    if (heading < 0) heading += 360;
    if (heading >= 360) heading -= 360;

    return heading;
}

// ============================
// setup
// ============================
void setup() {
    Serial.begin(9600);

    for (int i = 0; i < NUM_SENSORS; i++) {
        pinMode(trigPins[i], OUTPUT);
        pinMode(echoPins[i], INPUT);
    }

    Wire.begin();
    compass.init();
    gpsSerial.begin(GPSBaud);
}

// ============================
// loop
// ============================
void loop() {
    int sensorA = analogRead(A0);
    int sensorB = analogRead(A1);
    int sensorC = analogRead(A2);

    HallRead(&hallACounter, &hallALast , &rpsA , &lastMicrosA , &sensorA);
    HallRead(&hallBCounter, &hallBLast , &rpsB , &lastMicrosB , &sensorB);
    HallRead(&hallCCounter, &hallCLast , &rpsC , &lastMicrosC , &sensorC);

    HR_04_D[hr04_index] = readDistance(trigPins[hr04_index], echoPins[hr04_index]);
    if (hr04_index < 4) hr04_index++;
    else hr04_index = 0;

    FacingAngle = readCompass();
    GetGPS(&GPS_LAT, &GPS_LNG);

    static unsigned long lastPrint = 0;
    if (millis() - lastPrint >= 100) {
        unsigned long now = micros();
        if (now - lastMicrosA > 250000) rpsA = 0;
        if (now - lastMicrosB > 250000) rpsB = 0;
        if (now - lastMicrosC > 250000) rpsC = 0;

        float aSpeed = rpsA * wc / 16 * 7 ;
        float bSpeed = rpsB * wc / 16 * 7 ;
        float cSpeed = rpsC * wc / 16 * 7 ;
        float averageSpeed = (aSpeed + bSpeed + cSpeed) / 3;

        Serial.print("gps,");
        Serial.print(GPS_LAT ,10);
        Serial.print(",");
        Serial.print(GPS_LNG, 10);
        Serial.print(",");
        Serial.print("campass,");
        Serial.print(FacingAngle);
        Serial.print(",");
        Serial.print("hall,");
        Serial.print(averageSpeed);
        Serial.print(",");
        Serial.print(aSpeed);
        Serial.print(",");
        Serial.print(bSpeed);
        Serial.print(",");
        Serial.print(cSpeed);
        Serial.print(",");
        Serial.print("hr-04,");
        Serial.print(HR_04_D[0]);
        Serial.print(",");
        Serial.print(HR_04_D[1]);
        Serial.print(",");
        Serial.print(HR_04_D[2]);
        Serial.print(",");
        Serial.print(HR_04_D[3]);
        Serial.print(",");
        Serial.println(HR_04_D[4]);
        lastPrint = millis();
    }
}
