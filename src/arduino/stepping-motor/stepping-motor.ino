#define PUL_PIN 8  // 脈衝腳
#define DIR_PIN 9 // 方向腳
void setup() {
  // put your setup code here, to run once:
  pinMode(PUL_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  
  digitalWrite(DIR_PIN, LOW); //控制方向
}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(PUL_PIN, HIGH);
  delayMicroseconds(3000);    // 高電平持續時間（可調速度）
  digitalWrite(PUL_PIN, LOW);
  delayMicroseconds(3000);    // 低電平持續時間（可調速度）
                              //一個脈衝動一次
}
