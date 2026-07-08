/**
 * @file sensor_manager.h
 * @brief Public interface for the sensor manager module.
 */

#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <stdint.h>
#include <stdbool.h>
#include <string.h>

/* Sensor state - passed to the callback by value */
typedef struct {
    uint16_t last_temp_raw;   /* Last raw temperature ADC reading */
    uint16_t last_press_raw;  /* Last raw pressure ADC reading */
    uint32_t last_temp_ms;    /* Tick at which last temp was sampled */
    uint32_t last_press_ms;   /* Tick at which last pressure was sampled */
    bool     temp_valid;      /* True when last_temp_raw holds a valid value */
    bool     press_valid;     /* True when last_press_raw holds a valid value */

    /* Internal - not for external use */
    void    *p_callback;
} sensor_state_t;

/* Callback type: invoked when both temperature and pressure are fresh */
typedef void (*sensor_callback_t)(const sensor_state_t *p_state);

/* Public API */
void sensor_manager_init(sensor_callback_t p_cb);
void sensor_manager_tick(uint32_t now_ms);

#endif /* SENSOR_MANAGER_H */
