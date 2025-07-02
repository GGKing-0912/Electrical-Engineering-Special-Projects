int Str_for = 3;
int Str_back = 4;
int m_p =8;
int f_p =9;
int b_p =7;
char case_mode=0; 

void setup() {
  digitalWrite(3,HIGH);
  digitalWrite(4,HIGH);
  pinMode(Str_for,OUTPUT);
  pinMode(Str_back,OUTPUT);
  pinMode(b_p,INPUT);
  pinMode(m_p,INPUT);
  pinMode(f_p,INPUT);
  Serial.begin(9600);

}

void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available()>0) {
    case_mode=Serial.read();
  }
  switch(case_mode){
    case 'a':
             
            to_back_point();
              delay(10000);
                
             
              stop_Str();
              case_mode=0;
              break;
    case '2':
              
                 to_for_point();
               delay(10000);
                
              stop_Str();
              case_mode=0;
              break;
    case 'c':
              while((digitalRead(b_p)==LOW)&&(digitalRead(m_p)==LOW)){
                to_back_point();
              }
              stop_Str();
              if (digitalRead(m_p)==HIGH){
                to_back_point();
                delay(50);
              }
              stop_Str();
              while(digitalRead(m_p)==LOW){
                to_for_point();
              }
              stop_Str();
              case_mode=0;
              break;
    default:
              case_mode=0;
              break;
  }

}

void to_back_point(){
   digitalWrite(Str_for, HIGH);
   digitalWrite(Str_back, LOW);
}
void to_for_point(){
   digitalWrite(Str_back, HIGH);
   digitalWrite(Str_for, LOW);
}
void stop_Str(){
  digitalWrite(Str_for, HIGH);
  digitalWrite(Str_back, HIGH);
}
