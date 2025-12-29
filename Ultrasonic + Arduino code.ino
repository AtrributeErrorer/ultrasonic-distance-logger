

int SENDSIG = YOUR TRIG VALUE HERE; //YOUR TRIG VALUE HERE
int ECHO = YOUR ECHO VALUE HERE; // YOUR ECHO VALUE HERE
unsigned long duration = 1;
float distance;

void setup() {
  Serial.begin(9600);

  //Setting pinModes, sending signal to output and recieving signal (echo) to input
  pinMode(SENDSIG, OUTPUT);
  pinMode(ECHO, INPUT);

  //ensuring no signal is sent on startup
  digitalWrite(SENDSIG, LOW);

}

// the loop function runs over and over again forever
void loop() {
  digitalWrite(SENDSIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(SENDSIG, LOW);
  
  //measure the duration of how long it takes for the sound to be sent and returned
  duration = pulseIn(ECHO, HIGH, 30000); // Around 5 meters max~
  
  if(duration > 0) {
    Serial.println(duration);
  } else {
    Serial.println("Did not recieve echo");    
  }
  
  delay(60);
}
