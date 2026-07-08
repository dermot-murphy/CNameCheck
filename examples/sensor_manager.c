/**
 * @file sensor_manager.c
 * @brief Multi-sensor polling manager - ASPICE SWE.1 compliant example.
 *
 * Reads temperature and pressure sensors on a fixed schedule and applies
 * basic range validation before forwarding data to the application layer.
 */

#include "sensor_manager.h"

/* Sampling intervals in milliseconds */
#define TEMP_SAMPLE_INTERVAL_MS    500U
#define PRESS_SAMPLE_INTERVAL_MS  1000U

/* Sensor value limits (raw ADC counts) */
#define TEMP_ADC_MIN    100U
#define TEMP_ADC_MAX   3900U
#define PRESS_ADC_MIN   200U
#define PRESS_ADC_MAX  3800U

/* Module state */
static sensor_state_t g_sensor_state;
static bool           g_sm_initialised = false;

/* Forward declarations of private helpers */
static bool sm_read_temperature(uint16_t *p_raw_out);
static bool sm_read_pressure(uint16_t *p_raw_out);
static bool sm_validate_range(uint16_t val, uint16_t min_val, uint16_t max_val);

/**
 * @brief Initialise the sensor manager.
 * @param p_cb  Optional callback invoked when new data is available.
 */
void sensor_manager_init(sensor_callback_t p_cb)
{
    (void)memset(&g_sensor_state, 0, sizeof(g_sensor_state));
    g_sensor_state.p_callback    = p_cb;
    g_sensor_state.last_temp_ms  = 0U;
    g_sensor_state.last_press_ms = 0U;
    g_sm_initialised = true;
}

/**
 * @brief Poll sensors; call periodically from the main loop or a timer ISR.
 * @param now_ms  Current system tick in milliseconds.
 */
void sensor_manager_tick(uint32_t now_ms)
{
    if (!g_sm_initialised) {
        return;
    }

    /* Temperature sample */
    if ((now_ms - g_sensor_state.last_temp_ms) >= TEMP_SAMPLE_INTERVAL_MS) {
        uint16_t raw_val = 0U;
        if (sm_read_temperature(&raw_val)) {
            g_sensor_state.last_temp_raw = raw_val;
            g_sensor_state.last_temp_ms  = now_ms;
            g_sensor_state.temp_valid    = true;
        } else {
            g_sensor_state.temp_valid = false;
        }
    }

    /* Pressure sample */
    if ((now_ms - g_sensor_state.last_press_ms) >= PRESS_SAMPLE_INTERVAL_MS) {
        uint16_t raw_val = 0U;
        if (sm_read_pressure(&raw_val)) {
            g_sensor_state.last_press_raw = raw_val;
            g_sensor_state.last_press_ms  = now_ms;
            g_sensor_state.press_valid    = true;
        } else {
            g_sensor_state.press_valid = false;
        }
    }

    /* Invoke callback when both readings are fresh */
    if (g_sensor_state.temp_valid &&
        g_sensor_state.press_valid &&
        (NULL != g_sensor_state.p_callback)) {
        g_sensor_state.p_callback(&g_sensor_state);
    }
}

/* ---------- private helpers ---------- */

static bool sm_read_temperature(uint16_t *p_raw_out)
{
    /* Platform ADC read would go here */
    uint16_t adc_val = 2048U; /* placeholder */
    if (!sm_validate_range(adc_val, TEMP_ADC_MIN, TEMP_ADC_MAX)) {
        return false;
    }
    *p_raw_out = adc_val;
    return true;
}

static bool sm_read_pressure(uint16_t *p_raw_out)
{
    uint16_t adc_val = 2500U; /* placeholder */
    if (!sm_validate_range(adc_val, PRESS_ADC_MIN, PRESS_ADC_MAX)) {
        return false;
    }
    *p_raw_out = adc_val;
    return true;
}

static bool sm_validate_range(uint16_t val, uint16_t min_val, uint16_t max_val)
{
    return ((val >= min_val) && (val <= max_val));
}
