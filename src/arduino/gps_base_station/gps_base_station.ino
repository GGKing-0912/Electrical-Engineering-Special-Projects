#include <TinyGPSPlus.h>
#include <SoftwareSerial.h>

#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

const char* ssid = "cihciwifi";        // 改成你的 WiFi 名稱
const char* password = "ab19696a";// 改成你的 WiFi 密碼

WiFiUDP Udp;
const int port = 4210; // Python 監聽的 Port
const char* pc_ip = "192.168.50.212"; // jetson nano ip

TinyGPSPlus gps;

// SoftwareSerial(RX, TX)
// 接到 GPS 的 TX → D4（GPIO2）
// 接到 GPS 的 RX → D3（GPIO0）
SoftwareSerial gpsSerial(D4, D3);

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(9600);  // NEO-6M 預設 9600

  Serial.println("GPS 初始化中...");

  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected!");
  Serial.print("NodeMCU IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
  
  if (gps.location.isUpdated()) {
    double lat = gps.location.lat();
    double lng = gps.location.lng();

    String message = String(lat, 10) + "," + String(lng, 10);
  
    Udp.beginPacket(pc_ip, port);
    Udp.write(message.c_str());
    Udp.endPacket();
  
    Serial.println(message);
//    Serial.print(lat, 10);
//    Serial.print(", ");
//    Serial.println(lng, 10);

  }
}
