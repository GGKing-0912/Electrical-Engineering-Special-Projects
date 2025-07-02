// 創建腳位
int GAS_PUL_PIN=3;  // 油門脈衝腳
int GAS_DIR_PIN=4; // 油門方向腳

int BREAK_PUL_PIN=5; // 煞車脈衝腳
int BREAK_DIR_PIN=6; // 煞車方向腳

int FRONT_PIN=7; // 電動缸前進
int BACKWARD_PIN=8;  // 電動缸後退

int LEFT_DETECT_PIN=9; //左側觸發開關
int MID_DETECT_PIN=10; //中間觸發開關
int RIGHT_DETECT_PIN=11; //右側觸發開關

// 創建char
char function_mode=1; // 手動(2);自動(3) 模式
char control_mode=1; // 控制選項 油門(1) 煞車(2) 電缸(3)
char return_state=1; // 復歸

unsigned long pressStartTime = 0;
bool isPressed = false;
bool hasTriggered = false;

void setup() {
  // 宣告腳位
  pinMode(GAS_PUL_PIN, OUTPUT); //油門pin宣告
  pinMode(GAS_DIR_PIN, OUTPUT);
  
  pinMode(BREAK_PUL_PIN, OUTPUT); //煞車pin宣告
  pinMode(BREAK_DIR_PIN, OUTPUT);
  
  pinMode(FRONT_PIN, OUTPUT);     //電缸pin宣告
  pinMode(BACKWARD_PIN, OUTPUT);  
  
  pinMode(RIGHT_DETECT_PIN, INPUT); //觸發開關pin宣告(input)
  pinMode(LEFT_DETECT_PIN, INPUT);
  pinMode(MID_DETECT_PIN, INPUT);

  //歸零輸出
  digitalWrite(GAS_PUL_PIN, LOW); //油門脈衝
  digitalWrite(GAS_DIR_PIN, LOW); //油門方向

  digitalWrite(BREAK_PUL_PIN, LOW); //煞車脈衝
  digitalWrite(BREAK_DIR_PIN, LOW); //煞車方向

  digitalWrite(FRONT_PIN, LOW); //電缸前進
  digitalWrite(BACKWARD_PIN, LOW); //電缸後退
  
  //龅率設定
  Serial.begin(9600);

  //設定參數
  return_state=1 ;
}

void loop() {
  // 復歸:電動缸回到中位;油門和煞車全鬆[預設(DIR_PIN,HIGH)是順時鐘並且為壓緊]
  // 如果復歸未完成
  if (return_state == 1) 
  {
    resetToMiddle(); // 執行復歸
  } 
  else 
  {
    // 顯示選單
    Serial.println("請選擇模式: 手動(2) / 自動(3)");
    while (Serial.available() == 0);
    function_mode = Serial.read();
    
    if (function_mode == '2') {
      Serial.println("手動模式操控中，請輸入需求：");
      manualControl();
    } 
    else if (function_mode == '3') {
      Serial.println("進入自動模式（尚未實作自動控制）");
      // 自動模式的邏輯可自行擴展
    }
  }
}

void resetToMiddle()
{
  // 電缸前進到中間偵測位
  Serial.println("復歸中...");
  while (true) 
  {
    digitalWrite(FRONT_PIN,HIGH );
    digitalWrite(BACKWARD_PIN, LOW);
    if(digitalRead(LEFT_DETECT_PIN) == HIGH) 
    {
      if (!isPressed) 
      {
        isPressed = true;
        pressStartTime = millis(); // 記錄第一次按下的時間
        hasTriggered = false;      // 尚未觸發動作
      } 
      else 
      {
        if (!hasTriggered && (millis() - pressStartTime >= 50)) 
        {
          Serial.println("✅ 開關已按住超過 1 秒");
          hasTriggered = true; // 只觸發一次
          digitalWrite(BACKWARD_PIN, HIGH);
          digitalWrite(FRONT_PIN, HIGH);
          delay(10);
          Serial.println("復歸中A");
          break;
        }
      }
    }
    else 
    {
      // 放開按鍵，重置狀態
      isPressed = false;
      pressStartTime = 0;
      hasTriggered = false;
    }
  }

   while (true) 
   {
      digitalWrite(FRONT_PIN,LOW );
      digitalWrite(BACKWARD_PIN, HIGH);
      if(digitalRead(MID_DETECT_PIN) == HIGH) 
      {
        if (!isPressed) 
        {
          isPressed = true;
          pressStartTime = millis(); // 記錄第一次按下的時間
          hasTriggered = false;      // 尚未觸發動作
        } 
        else 
        {
          if (!hasTriggered && (millis() - pressStartTime >= 50)) 
          {
          Serial.println("✅ 開關已按住超過 1 秒");
          hasTriggered = true; // 只觸發一次
          digitalWrite(BACKWARD_PIN, HIGH);
          digitalWrite(FRONT_PIN, HIGH);
          delay(10);
          Serial.println("復歸中b");
          break;
          }
        }
      }
      else 
      {
        // 放開按鍵，重置狀態
        isPressed = false;
        pressStartTime = 0;
        hasTriggered = false;
      }
    }
    return_state=2;
}
 

   




void manualControl() {
  while (true) {
    if (Serial.available()) {
      char input = Serial.read();
      switch (input) {
        case 'W': // 油門按下一定量
          Serial.println("油門加速");
          pulseOutput(GAS_PUL_PIN, GAS_DIR_PIN, 5);
          break;
        case 'S': // 油門放鬆一定量
          Serial.println("油門放鬆");
          pulseOutput(GAS_PUL_PIN, !GAS_DIR_PIN, 5);
          break;
        case 'D': // 電缸前進
          Serial.println("電缸前進");
          moveActuator(FRONT_PIN);
          break;
        case 'A': // 電缸後退
          Serial.println("電缸後退");
          moveActuator(BACKWARD_PIN);
          break;
        case ' ': // 空白鍵：煞車（油門鬆到底，煞車按下）
          Serial.println("煞車中...");
          pulseOutput(GAS_PUL_PIN, !GAS_DIR_PIN, 10); // 完全鬆油門
          pulseOutput(BREAK_PUL_PIN, BREAK_DIR_PIN, 10); // 煞車啟動
          delay(3000); // 假設車停了
          pulseOutput(BREAK_PUL_PIN, !BREAK_DIR_PIN, 10); // 鬆開煞車
          Serial.println("煞車完成");
          break;
        case 'P': // 結束手動控制
          Serial.println("退出手動模式");
          return;
        default:
          Serial.println("無效輸入");
      }
    }
  }
}

void pulseOutput(int pulPin, int dirPin, int count)
{
  digitalWrite(dirPin, HIGH); // 預設方向為 HIGH，可依需求改
  for (int i = 0; i < count; i++) {
    digitalWrite(pulPin, HIGH);
    delay(50);
    digitalWrite(pulPin, LOW);
    delay(50);
  }
}

void moveActuator(int dirPin) 
{
  digitalWrite(FRONT_PIN, HIGH);
  digitalWrite(BACKWARD_PIN, HIGH);
  digitalWrite(dirPin, LOW);
  delay(2000); // 動作時間
  digitalWrite(dirPin, HIGH);
}
