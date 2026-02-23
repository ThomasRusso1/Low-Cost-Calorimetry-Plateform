#include <Adafruit_MAX31865.h>
#include <LiquidCrystal_I2C.h>
#include <PID_v1.h>

// --- Pin Definitions & Constants ---
#define HEATER_RELAY_PIN 13
#define POT_RELAY_PIN 8
#define RREF 4300.0      // For PT1000 with a 4.3k Ohm reference resistor
#define RNOMINAL 1000.0  // For a PT1000 sensor

// --- System Objects ---
Adafruit_MAX31865 local_rtd = Adafruit_MAX31865(3);  // Local RTD for absolute water temp
LiquidCrystal_I2C lcd(0x27, 20, 4);

// --- PID Configuration ---
double Setpoint, Input, Output;
double Kp = 18, Ki = 5, Kd = 8;
PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, P_ON_M, DIRECT);
int windowSize = 2000;
unsigned long windowStartTime;

// --- Temperature & State Variables ---
float tempWater_RTD = 0.0;      // Absolute temperature from the local RTD sensor
float tc_temp_water = 0.0;      // Temperature from the water thermocouple (from Linduino)
float tc_temp_mortar = 0.0;     // Temperature from the mortar thermocouple (from Linduino)
// Variables for Water Sensor
const int SAMPLE_COUNT = 30;  // Number of samples to average
float tempHistory_water[SAMPLE_COUNT];
float total_water = 0.0;
int currentIndex_water = 0;


// --- System Mode Flags ---
bool is_running = true;
bool was_running = true;
bool matchingMode = false;
bool calibrationMode = false;
bool rampTest = false;
double gap = 0.0;
unsigned long lastLinduinoMessageTime = 0;
bool LinduinoConnection = true;
bool rampingUp = true;

const int final_setpoint = 70;
const int final_setpoint_ramp = 26;
// Timing variables
unsigned long currentTime, previousTime, startTime;
double elapsedTime;  // For measuring time elapsed in seconds
unsigned long setpointCheck;

float Peltier_cell_1;
float Peltier_cell_2;

// =================================================================
//  FORWARD DECLARATIONS
// =================================================================
void read_sensors();
void process_commands();
void update_pid_and_setpoint();
void control_heater();
void update_display();
float get_corrected_thermocouple_temp(float raw_tc_temp);
int find_closest_index(int value_to_find);
int heat=0;

// =================================================================
//  SETUP
// =================================================================
void setup() {
  Serial.begin(9600);   // To PC / RPi
  Serial1.begin(9600);  // To Linduino

  pinMode(HEATER_RELAY_PIN, OUTPUT);
  pinMode(POT_RELAY_PIN, OUTPUT);

  lcd.init();
  lcd.backlight();
  lcd.print("System Starting...");

  local_rtd.begin(MAX31865_3WIRE);
  float initial_temp_water = local_rtd.temperature(RNOMINAL, RREF);
  for (int i = 0; i < SAMPLE_COUNT; i++) {
    tempHistory_water[i] = initial_temp_water;
    total_water += initial_temp_water;
  }
  tempWater_RTD = total_water / SAMPLE_COUNT;

  myPID.SetOutputLimits(100, windowSize);
  myPID.SetMode(AUTOMATIC);

  Input = 20.0;
  Setpoint = 18.0;

  windowStartTime = millis();
  delay(1500);
  lcd.clear();
}

// =================================================================
//  MAIN LOOP
// =================================================================
void loop() {
  unsigned long currentTime = millis();
  elapsedTime = (currentTime - startTime) / 1000.0;
  read_sensors();
  process_commands();

  if (is_running) {
    update_pid_and_setpoint();
    control_heater();
    digitalWrite(POT_RELAY_PIN, HIGH);
  } else {
    digitalWrite(HEATER_RELAY_PIN, LOW);
    digitalWrite(POT_RELAY_PIN, LOW);
  }

  update_display();
  delay(100);
}

// =================================================================
//  HELPER FUNCTIONS
// =================================================================

/**
 * Reads data from the local RTD sensor and from the Linduino.
 */
void read_sensors() {
  // --- Update Water Sensor Reading (same logic) ---
  total_water = total_water - tempHistory_water[currentIndex_water];
  tempHistory_water[currentIndex_water] = local_rtd.temperature(RNOMINAL, RREF);
  total_water = total_water + tempHistory_water[currentIndex_water];
  tempWater_RTD = total_water / SAMPLE_COUNT;
  currentIndex_water++;
  if (currentIndex_water >= SAMPLE_COUNT) {
    currentIndex_water = 0;
  }
  if (Serial1.available() > 0) {
    lastLinduinoMessageTime = millis();
    String dataFromLinduino = Serial1.readStringUntil('\n');
    
    // Debugging: Uncomment the line below to see exactly what arrives
    // Serial.print("RAW DATA: "); Serial.println(dataFromLinduino);
    // Find all three commas
    int comma1 = dataFromLinduino.indexOf(',');
    int comma2 = dataFromLinduino.indexOf(',', comma1 + 1);
    int comma3 = dataFromLinduino.indexOf(',', comma2 + 1);
    // Ensure we found all 3 commas before parsing
    if (comma1 > 0 && comma2 > 0 && comma3 > 0) {
        // 1. Water Temp (Start to 1st comma)
        tc_temp_water = dataFromLinduino.substring(0, comma1).toFloat();
              // 2. Mortar Temp (Between 1st and 2nd comma)
        tc_temp_mortar = dataFromLinduino.substring(comma1 + 1, comma2).toFloat();
              // 3. Peltier 1 (Between 2nd and 3rd comma)
        Peltier_cell_1 = dataFromLinduino.substring(comma2 + 1, comma3).toFloat();
        // 4. Peltier 2 (After 3rd comma to end)
        Peltier_cell_2 = dataFromLinduino.substring(comma3 + 1).toFloat();
    }
  }
}

/**
 * Checks for commands from the PC/RPi and updates the system mode.
 */
void process_commands() {
  // This function is where you will place your logic for reading commands
  // from the PC to change modes (e.g., switch to matchingMode).
  // Example:
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    if (command.startsWith("R")) {
      Serial.print(tc_temp_mortar);
      Serial.print(",");
      Serial.print(tc_temp_water);
      Serial.print(",");
      Serial.print(Setpoint);
      Serial.print(",");
      Serial.print(tempWater_RTD);
      Serial.print(",");
      Serial.print(Peltier_cell_1,6);
      Serial.print(",");
      Serial.println(Peltier_cell_2,6);
    } else if (command.startsWith("S")) {
      matchingMode = false;
      calibrationMode = false;
      rampTest = false;
      is_running = true;         // Re-enable the process
      LinduinoConnection = true; // Reset the connection status for the new run
      Setpoint = command.substring(1).toFloat();
    } else if (command.startsWith("M")) {
      matchingMode = true;
      rampTest = false;
      calibrationMode = false;
      is_running = true;         // Re-enable the process
      LinduinoConnection = true; // Reset the connection status for the new run
      gap = command.substring(1).toFloat();
    } else if (command.startsWith("C")) {
      matchingMode = false;
      rampTest = false;
      calibrationMode = true;
      Setpoint = 24.5;
      is_running = true;         // Re-enable the process
      LinduinoConnection = true; // Reset the connection status for the new run
    } else if (command.startsWith("P")) {
      matchingMode = false;
      calibrationMode = false;
      rampTest = true;
      rampingUp = true;
      Setpoint = 18;
      setpointCheck = elapsedTime;
      is_running = true;         // Re-enable the process
      LinduinoConnection = true; // Reset the connection status for the new run
    }
  }
}
/**
 * Sets the PID Input and Setpoint based on the current operational mode.
 */
void update_pid_and_setpoint() {
  // --- SAFETY CHECK ---
  if (millis() - lastLinduinoMessageTime > 10000) { // 10-second timeout
    is_running = false;
    LinduinoConnection = false;
    digitalWrite(HEATER_RELAY_PIN, LOW);
    digitalWrite(POT_RELAY_PIN, LOW);
    return;
  }
  // --- In Matching Mode, use the differential thermocouple system with RTD-based correction ---
  if (matchingMode) {
    //Avec les PT100, on voit que Tw-Tm=0.12
    const float m = 0;
    const float c = 0.12;
    const float safety = 0.03;
    float tc_offset = (m * tc_temp_water) + c;
    Input = tc_temp_water;
    Setpoint = tc_temp_mortar + tc_offset - safety;

  } else {
    // --- In all OTHER modes (Static, Calibration, Ramp), use the local absolute RTD system ---
    // The PID Input is the absolute temperature of the water from the local RTD.
    Input = tc_temp_water;
  }
  // The Setpoint is determined by the logic for these other modes
  // (e.g., a fixed value from an 'S' command, or a ramping value).
  if (calibrationMode) {
    if ((elapsedTime - setpointCheck) >= 600) {
      Setpoint += 0.5;
      setpointCheck = elapsedTime;
    }
    if (Setpoint > final_setpoint) {
      is_running=false;
    }
    // Add your setpoint ramping logic for calibration here
  } else if (rampTest) {
    // Check if 2 hours (7200 seconds) have passed
    // Note: 3600 * 2 = 7200 seconds
    if ((elapsedTime - setpointCheck) >= 21600) {
      
      setpointCheck = elapsedTime; // Reset timer for the next 2-hour wait

      if (rampingUp) {
        // --- LOGIC FOR RAMPING UP ---
        
        // Only increase if we haven't reached the top yet
        if (Setpoint < final_setpoint_ramp) {
           Setpoint += 1; 
        }

        // Check if we have reached the peak (30 degrees)
        // We use >= to handle potential small floating point differences
        if (Setpoint >= final_setpoint_ramp) {
          rampingUp = false; // Switch direction! Next step will be down.
        }
      } 
      else {
        // --- LOGIC FOR RAMPING DOWN ---
        Setpoint -= 1;

        // Check if we have reached the bottom (25 degrees)
        if (Setpoint <= 17.0) {
          is_running = false; // Stop the test
        }
      }
    }
  }
}

/**
 * Runs the PID computation and controls the heater relay.
 */
void control_heater() {
  unsigned long now = millis();
  myPID.Compute();

  if (now - windowStartTime > windowSize) {
    windowStartTime += windowSize;
  }

  if (Output < (now - windowStartTime)) {
    digitalWrite(HEATER_RELAY_PIN, LOW);
    heat = 0;
  } else if (Input < Setpoint) {
    digitalWrite(HEATER_RELAY_PIN, HIGH);
    heat = 1;
  }
}

/**
 * Updates all information on the LCD screen.
 */
void update_display() {
  if (is_running){
    lcd.setCursor(0, 0);
    lcd.print("RTD: ");
    lcd.print(tempWater_RTD, 2);
    lcd.print("  ");
    lcd.print("H: ");
    lcd.print(heat);

    lcd.setCursor(0, 1);
    lcd.print("M: ");
    lcd.print(tc_temp_mortar, 2);
    lcd.print(" W: ");
    lcd.print(tc_temp_water, 2);
    lcd.print("   ");

    lcd.setCursor(0, 2);
    lcd.print("Targ:");
    lcd.print(Setpoint, 2);
    lcd.print(" In: ");
    lcd.print(Input, 2);

    lcd.setCursor(0, 3);
    lcd.print(" P:");
    lcd.print((Output / windowSize) * 100, 0);
    lcd.print("%     ");
  }
  else {
    if (was_running){
      if (LinduinoConnection) {
        lcd.clear();
        lcd.print("TEST FINISHED"); 
      }
      else {
        lcd.clear();
        lcd.print("Linduino Link LOST!");
      }
    }
  }
  was_running = is_running;
}