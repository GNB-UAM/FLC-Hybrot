#include "Oscillator.h"
#include <Servo.h>


unsigned int A = 20; // Amplitude (higher -> longer steps) set 10-40
unsigned int T = 1500, T_old; // Period (lower -> faster moves)
Oscillator osc_middle, osc_right, osc_left;

int lightPin = 1;

char last = '2';
char to_send = '1';

char val = '0';
int flag = 0;
String str1 = "";
String str2 = "";

int ajuste_direccion = -6; // ESTO CALIBRA LA DIRECCIÓN
// Valores negativos hacen que vaya para la derecha
int A_aux;

void setup() {
  Serial.begin(19200); //El Bluetooth solo funciona a 19200
  delay(1000); // Small startup delay, replace with start-button press (if present)

  //-- Attach the oscillators to the servos
  osc_middle.attach(2); // 2,3 and 4 are the digital pins
  osc_right.attach(4);
  osc_left.attach(3);
  delay(100);
  osc_middle.refresh();
  osc_right.refresh();
  osc_left.refresh();
  //delay(10000); // 10 segundos de espera en la posición  central


  // NO CALIBRAR AQUÍ, tan solo colocar las patas están físicamente en la posición central
  //-- Set the parameters
  //osc_middle.SetO(0); // Correction for the offset of the servos
  //osc_right.SetO(-5); //Grande 3, -30, 10
  //osc_left.SetO(-5);  // Pequeno 10, -5, 5

  osc_middle.SetO(0); // Correction for the offset of the servos
  osc_right.SetO(-55); //Grande 3, -30, 10
  osc_left.SetO(-5);  // Pequeno 10, -5, 5

  osc_middle.SetA(10); // Middle motor needs a small amplitude (5-15)
  //osc_middle.SetA(20); // Middle motor needs a small amplitude (5-15)
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

void loop() {
  osc_middle.refresh();
  osc_right.refresh();
  osc_left.refresh();

  int reading  = analogRead(lightPin);
  if (reading >= 900) { // UMBRAL LUZ
    to_send = '3';
  } else {
    to_send = '1';
  }


  if (to_send != last) {
    Serial.print(to_send);
    last = to_send;
  }

  /*if (Serial.available() >= 1) {
    val = Serial.read();

    if (val != '\n') {
      str1 += val;
    } else {
      T = str1.toInt() * 2;
      //Serial.println(str1);
      str1 = "";

      osc_middle.SetT(T);
      osc_right.SetT(T);
      osc_left.SetT(T);
    }
    }*/

  if (Serial.available() >= 1) {
    val = Serial.read();
    //mySerial.println(val, HEX);
    //Serial.println(val);
    //Serial.print(to_send);

    if (flag == 0) {
      if (val != '\t') {
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
        T_old = T;
        T = str2.toInt();
        A = str1.toInt();

        if (A > 40) {
          A = 40;
        } else if (A < 5) {
          str2 = "";
          str1 = "";
          flag = 0;

          return;
        }

        
        if (T > T_old * 4) {
          T = T_old;
        } else if (T < 500) {
          T = 500;
        }


        //mySerial.print(str1+" ");
        //mySerial.println(str2);

        A_aux = A + ajuste_direccion;
        if (A_aux < 0) {
           A_aux = 0;
        } else if (A_aux > 40) {
          A_aux = 40;
        }
        osc_right.SetA(A_aux);
        osc_left.SetA(A);

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
