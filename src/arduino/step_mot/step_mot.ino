int PUL_PIN=8;  // 脈衝腳
int DIR_PIN=9; // 方向腳
char control_mode=0;
char function_mode=0;
void setup() {
  // put your setup code here, to run once:
  pinMode(PUL_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  
  digitalWrite(DIR_PIN, LOW); //控制方向
  digitalWrite(PUL_PIN, LOW); 

  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  

   
  if (Serial.available() > 0) {
    function_mode = Serial.read();  // 主模式切換
  }

  switch (function_mode){
     
    case '1':
      Serial.println("手控模式");
      if (Serial.available() > 0) {
        control_mode = Serial.read();  // 控制細項模式
      }

      switch (control_mode) {
        case '1':
          Serial.println("持續往前");
          while (true)
          {
            step_mot_pos(PUL_PIN, DIR_PIN);
            if (Serial.available() > 0)
            {
              control_mode = Serial.read();
              if (control_mode == '0') break;
            }
          }
          break;

        case '2':
          Serial.println("持續向後");
          while (true) {
            step_mot_neg(PUL_PIN, DIR_PIN);
            if (Serial.available() > 0) 
            {
              control_mode = Serial.read();
              if (control_mode == '0') break;
            }
          }
          break;

        case '3':
          Serial.println("往前一段");
          for (int i = 0; i < 300; i++) {
            step_mot_pos(PUL_PIN, DIR_PIN);
          }
          control_mode = '0';
          break;

        case '4':
          Serial.println("向後一段");
          for (int i = 0; i < 300; i++) {
            step_mot_neg(PUL_PIN, DIR_PIN);
          }
          control_mode = '0';
          break;

        default:
          break;
      }
      break;

    case '2':
      Serial.println("自動模式");
      break;

    default:
      break;
  }
}
void step_mot_pos(int PUL, int DIR){
  digitalWrite(DIR, HIGH);
  step_mot_mov(PUL);
}

void step_mot_neg(int PUL, int DIR){
  digitalWrite(DIR, LOW);
  step_mot_mov(PUL);
}


void step_mot_mov(int PUL){
  digitalWrite(PUL, HIGH);
  delayMicroseconds(3000);  
  digitalWrite(PUL, LOW);
  delayMicroseconds(3000);
}
