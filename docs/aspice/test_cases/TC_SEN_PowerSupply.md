# Software Test Specification: DC Power Supply to Sensor

*Automotive SPICE® PAM v4.0 Compliant | CL2 Ready | SWE.4*

---

## Configuration

| Parameter          | Value  | Description                                                |
|--------------------|--------|------------------------------------------------------------|
| NOMINAL_VOLTAGE    | 12.0V  | Standard operating supply voltage                          |
| UNDERVOLTAGE_LEVEL | 8.0V   | Supply voltage used for under-voltage fault tests          |
| OVERVOLTAGE_LEVEL  | 16.0V  | Supply voltage used for over-voltage fault tests           |
| VOLTAGE_TOLERANCE  | 0.5V   | Max acceptable delta between supply set and sensor reading |
| STARTUP_DELAY      | 200ms  | Settle time after supply enabled                           |
| FAULT_SETTLE_TIME  | 100ms  | Settle time after fault condition applied                  |
| RECOVERY_DELAY     | 200ms  | Settle time after voltage restored from fault              |

---

## TC_SEN_001: Nominal Supply Voltage Accepted by Sensor

| Field          | Value                                                              |
|----------------|--------------------------------------------------------------------|
| ID             | TC_SEN_001                                                         |
| Objective      | Verify sensor operates and reports correct voltage under nominal supply |
| Requirements   | REQ-SEN-001, REQ-SEN-010                                           |
| Priority       | High                                                               |
| Preconditions  | Supply is off, sensor is powered down, no faults present           |
| Postconditions | Supply set to 0V, sensor powered down                              |

| Step | Action                                   | Expected Result                                          |
|------|------------------------------------------|----------------------------------------------------------|
| 1    | SET supply_voltage TO {NOMINAL_VOLTAGE}  | supply_voltage EQUALS {NOMINAL_VOLTAGE}                  |
| 2    | TRIGGER supply_on                        | sensor_status IS ACTIVE                                  |
| 3    | WAIT FOR {STARTUP_DELAY}                 | sensor_status IS ACTIVE                                  |
| 4    | READ sensor_voltage                      | sensor_voltage IS WITHIN {VOLTAGE_TOLERANCE} OF {NOMINAL_VOLTAGE} |
| 5    | READ sensor_status                       | sensor_status EQUALS NOMINAL                             |

---

## TC_SEN_002: Under-Voltage Fault Detected by Sensor

| Field          | Value                                                              |
|----------------|--------------------------------------------------------------------|
| ID             | TC_SEN_002                                                         |
| Objective      | Verify sensor detects and reports an under-voltage fault condition |
| Requirements   | REQ-SEN-020, REQ-SEN-021                                           |
| Priority       | High                                                               |
| Preconditions  | Supply is on at {NOMINAL_VOLTAGE}, sensor is active, no faults present |
| Postconditions | Supply restored to {NOMINAL_VOLTAGE}, fault cleared, sensor powered down |

| Step | Action                                        | Expected Result                                                      |
|------|-----------------------------------------------|----------------------------------------------------------------------|
| 1    | READ sensor_status                            | sensor_status EQUALS NOMINAL                                         |
| 2    | SET supply_voltage TO {UNDERVOLTAGE_LEVEL}    | supply_voltage EQUALS {UNDERVOLTAGE_LEVEL}                           |
| 3    | WAIT FOR {FAULT_SETTLE_TIME}                  | sensor_status IS ACTIVE                                              |
| 4    | READ sensor_status                            | sensor_status EQUALS UNDERVOLTAGE_FAULT                              |
| 5    | READ sensor_voltage                           | sensor_voltage IS WITHIN {VOLTAGE_TOLERANCE} OF {UNDERVOLTAGE_LEVEL} |
| 6    | READ fault_flag                               | fault_flag IS TRUE                                                   |

---

## TC_SEN_003: Over-Voltage Fault Detected by Sensor

| Field          | Value                                                              |
|----------------|--------------------------------------------------------------------|
| ID             | TC_SEN_003                                                         |
| Objective      | Verify sensor detects and reports an over-voltage fault condition  |
| Requirements   | REQ-SEN-022, REQ-SEN-023                                           |
| Priority       | High                                                               |
| Preconditions  | Supply is on at {NOMINAL_VOLTAGE}, sensor is active, no faults present |
| Postconditions | Supply restored to {NOMINAL_VOLTAGE}, fault cleared, sensor powered down |

| Step | Action                                       | Expected Result                                                     |
|------|----------------------------------------------|---------------------------------------------------------------------|
| 1    | READ sensor_status                           | sensor_status EQUALS NOMINAL                                        |
| 2    | SET supply_voltage TO {OVERVOLTAGE_LEVEL}    | supply_voltage EQUALS {OVERVOLTAGE_LEVEL}                           |
| 3    | WAIT FOR {FAULT_SETTLE_TIME}                 | sensor_status IS ACTIVE                                             |
| 4    | READ sensor_status                           | sensor_status EQUALS OVERVOLTAGE_FAULT                              |
| 5    | READ sensor_voltage                          | sensor_voltage IS WITHIN {VOLTAGE_TOLERANCE} OF {OVERVOLTAGE_LEVEL} |
| 6    | READ fault_flag                              | fault_flag IS TRUE                                                  |

---

## TC_SEN_004: Sensor Recovers from Under-Voltage Fault on Voltage Restoration

| Field          | Value                                                              |
|----------------|--------------------------------------------------------------------|
| ID             | TC_SEN_004                                                         |
| Objective      | Verify sensor clears fault and returns to NOMINAL when supply is restored |
| Requirements   | REQ-SEN-020, REQ-SEN-030                                           |
| Priority       | High                                                               |
| Preconditions  | Supply is on at {UNDERVOLTAGE_LEVEL}, sensor is in UNDERVOLTAGE_FAULT state |
| Postconditions | Supply set to 0V, sensor powered down                              |

| Step | Action                                   | Expected Result                                          |
|------|------------------------------------------|----------------------------------------------------------|
| 1    | READ sensor_status                       | sensor_status EQUALS UNDERVOLTAGE_FAULT                  |
| 2    | READ fault_flag                          | fault_flag IS TRUE                                       |
| 3    | SET supply_voltage TO {NOMINAL_VOLTAGE}  | supply_voltage EQUALS {NOMINAL_VOLTAGE}                  |
| 4    | WAIT FOR {RECOVERY_DELAY}                | sensor_status IS ACTIVE                                  |
| 5    | READ sensor_status                       | sensor_status EQUALS NOMINAL                             |
| 6    | READ fault_flag                          | fault_flag IS FALSE                                      |
| 7    | READ sensor_voltage                      | sensor_voltage IS WITHIN {VOLTAGE_TOLERANCE} OF {NOMINAL_VOLTAGE} |

---

## TC_SEN_005: Sensor Voltage Measurement Accuracy at Boundary Condition

| Field          | Value                                                              |
|----------------|--------------------------------------------------------------------|
| ID             | TC_SEN_005                                                         |
| Objective      | Verify sensor measurement accuracy near the under-voltage threshold |
| Requirements   | REQ-SEN-025                                                        |
| Priority       | Medium                                                             |
| Preconditions  | Supply is on at {NOMINAL_VOLTAGE}, sensor is active                |
| Postconditions | Supply set to 0V, sensor powered down                              |
| Parameters     | VOLTAGE_TOLERANCE=0.2V, STARTUP_DELAY=500ms                        |

| Step | Action                                   | Expected Result                                          |
|------|------------------------------------------|----------------------------------------------------------|
| 1    | SET supply_voltage TO 9.5V               | supply_voltage EQUALS 9.5V                               |
| 2    | WAIT FOR {STARTUP_DELAY}                 | sensor_status IS ACTIVE                                  |
| 3    | READ sensor_voltage                      | sensor_voltage IS WITHIN {VOLTAGE_TOLERANCE} OF 9.5V     |
| 4    | READ sensor_status                       | sensor_status EQUALS NOMINAL                             |
