const byte adcPin = 0;  // A0

const int MAX_RESULTS = 256;

volatile int results [MAX_RESULTS];
volatile int resultNumber;

void setup ()
  {
  Serial.begin (1000000);
  Serial.println ();

  // reset Timer 1
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1 = 0;
  TCCR1B = bit (CS11) | bit (WGM12);  // CTC, prescaler of 8
  TIMSK1 = bit (OCIE1B);
  OCR1A = 99;    
  OCR1B = 99;   // 20 uS - sampling frequency 20 kHz

  ADCSRA =  bit (ADEN) | bit (ADIE) | bit (ADIF);   // turn ADC on, want interrupt on completion
  ADCSRA |= bit (ADPS2);  // Prescaler of 16
//  ADCSRA |= (1 << ADPS1) | (1 << ADPS0);    // 8 prescaler for 153.8 KHz
  ADMUX = 0x60; // left adjust, adc0, internal vcc
  ADCSRB = bit (ADTS0) | bit (ADTS2);  // Timer/Counter1 Compare Match B
  ADCSRA |= bit (ADATE);   // turn on automatic triggering

}

// ADC complete ISR
ISR (ADC_vect)
{
    results[resultNumber++] = ADCH; // Read left adjusted top 8 bits
    if(resultNumber == MAX_RESULTS)
    {
      ADCSRA = 0;  // turn off ADC
    }
} 

EMPTY_INTERRUPT (TIMER1_COMPB_vect);

void loop () {

  while (resultNumber < MAX_RESULTS)
    { }

  for (int i = 0; i < MAX_RESULTS; i++)
  {
    // int adcValue = results [i];
    // int convertedValue = map(adcValue, 0, pow(2, 10) - 1, 0, pow(2, 8) - 1);
    Serial.write (results [i]);
  }
  resultNumber = 0; 
  ADCSRA =  bit (ADEN) | bit (ADIE) | bit (ADIF)| bit (ADPS2) | bit (ADATE);   
   // turn ADC back on
}