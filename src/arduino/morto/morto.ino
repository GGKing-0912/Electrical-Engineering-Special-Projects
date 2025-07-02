void setup() {
  // put your setup code here, to run once:
 int time = 0;
  Serial.begin(9600);
 
 digitalWrite(3,HIGH);
 digitalWrite(4,HIGH);
 pinMode(3,OUTPUT);
 pinMode(4,OUTPUT);
 pinMode(5,INPUT);
}

void loop() {
  // put your main code here, to run repeatedly:

//  digitalWrite(3,LOW);
//  Serial.println("3H");
//  delay(2000);
//  digitalWrite(3,HIGH);
//  Serial.println("3L");
//  delay(2000);
//  digitalWrite(4,LOW);
//  Serial.println("4H");
//  delay(2000);
//  digitalWrite(4,HIGH);
//  Serial.println("4L");

    
    
    Serial.println(digitalRead(5));
    
    delay(2000);
}
