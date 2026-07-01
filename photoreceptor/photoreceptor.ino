#include "Oscillator.h"
#include <Servo.h>

int middle_amplitude = 15; // Middle motor needs a small amplitude (5-15)

int A = 20; // Amplitude (higher -> longer steps) set 10-40
int T = 1500;//, T_old; // Period (lower -> faster moves)
Oscillator osc_middle, osc_right, osc_left;

int lightPin = 1;


char val = '0';
int flag = 0;
String str1 = "";
String str2 = "";

float ajuste_direccion = 0.9; // ESTO CALIBRA LA DIRECCIÓN
int A_aux;

void setup() {
  Serial.begin(19200); //El Bluetooth solo funciona a 19200

  //-- Attach the oscillators to the servos
  osc_middle.attach(2); // 2,3 and 4 are the digital pins
  osc_right.attach(4);
  osc_left.attach(3);

  osc_middle.SetA(0);
  osc_right.SetA(0);
  osc_left.SetA(0);

  // CALIBRA LA POSICION CENTRAL DE LAS PATAS
  osc_middle.SetO(-10);
  osc_right.SetO(10);
  osc_left.SetO(-5);

  // Mantener parado 2 segundos para comprobar posicion patas
  while(millis() < 2000) {
    osc_middle.refresh();
    osc_right.refresh();
    osc_left.refresh();
  }

  osc_middle.SetT(T); // Set the period of work
  osc_right.SetT(T);
  osc_left.SetT(T);

  //-- Refresh the oscillators
  osc_middle.refresh();
  osc_right.refresh();
  osc_left.refresh();

  //-- Set the phase difference
  //-- This defines the type of movement the robot makes
  osc_middle.SetPh(DEG2RAD( 90 )); // EL SIGNO DEFINE LA DIRECCION DEL ROBOT
  osc_left.SetPh(  DEG2RAD( 0 )); //Grande 180
  osc_right.SetPh( DEG2RAD( 0 )); //Grande 180
}

void(* resetFunc) (void) = 0; //declare reset function @ address 0

int counter = 0;
void loop() {
  osc_middle.refresh();
  osc_right.refresh();
  osc_left.refresh();

  unsigned char reading = map(analogRead(lightPin), 0,1023, 0,255);
  if(counter>100) {
    Serial.write(reading); 
    digitalWrite(13,LOW); // DEBUG LED OFF
    counter=0;
  }
  counter++;

  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    if( line != NULL) {
      int result = sscanf(line.c_str(), "%d,%d", &T, &A);
      if (result == 2) {
        digitalWrite(13,HIGH); // DEBUG LED ON
        if (A > 40)
          A = 40;
        if (A <= 0)
          A = 0;
        
        if (A <= 0 && T <= 0) {
          resetFunc(); // Reset board
          osc_right.SetA(0);
          osc_left.SetA(0);
          osc_middle.SetA(0);
          return;
        }
  
        if (T > 10000) {
          T = 10000;
        } else if (T < 250) {
          T = 250;
        }
  
        A_aux = A * ajuste_direccion;
        if (A_aux < 0) {
            A_aux = 0;
        } else if (A_aux > 40) {
          A_aux = 40;
        }
        osc_right.SetA(A_aux);
        osc_left.SetA(A);
        osc_middle.SetA(middle_amplitude);
  
        osc_middle.SetT(T);
        osc_right.SetT(T);
        osc_left.SetT(T);
      }
    }
  }
  //delay(0);
}
