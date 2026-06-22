#include "Oscillator.h"
#include <Servo.h>

int middle_amplitude = 10; // Middle motor needs a small amplitude (5-15)

unsigned int A = 20; // Amplitude (higher -> longer steps) set 10-40
unsigned int T = 1500;//, T_old; // Period (lower -> faster moves)
Oscillator osc_middle, osc_right, osc_left;

int lightPin = 1;


char val = '0';
int flag = 0;
String str1 = "";
String str2 = "";

int ajuste_direccion = 0; // ESTO CALIBRA LA DIRECCIÓN
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

  // Mantener parado 3 segundos para comprobar posicion patas
  while(millis() < 3000) {
    osc_middle.refresh();
    osc_right.refresh();
    osc_left.refresh();
  }

  osc_middle.SetA(middle_amplitude);
  osc_right.SetA(A + ajuste_direccion);
  osc_left.SetA(A);

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

int lastTime = 0;
void loop() {
  osc_middle.refresh();
  osc_right.refresh();
  osc_left.refresh();

  unsigned char reading = map(analogRead(lightPin), 0,1023, 0,255);
  if(millis() > lastTime+100) {
    Serial.write(reading); // Send as a single byte 0-255
    lastTime = millis();
  }

  if (Serial.available() >= 1) {
    val = Serial.read();

    if (flag == 0) {
      if (val != ',') {
        if (val == '\n') {
          str2 = "";
          str1 = "";
        } else {
          str1 += val;
        }
      } else {
        flag = 1;
      }
      
    } else {
      if (val == '\n') {
        T = str2.toInt();
        A = str1.toInt();

        if (A > 40) {
          A = 40;
        } else if (A < 1) {
          str2 = "";
          str1 = "";
          flag = 0;

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

        A_aux = A + ajuste_direccion;
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

        str2 = "";
        str1 = "";
        flag = 0;
      } else {
        str2 += val;
      }
    }
  }

}
