/**
 * @file uart_driver.h
 * @brief Public interface for the UART peripheral driver.
 */

#ifndef UART_DRIVER_H
#define UART_DRIVER_H

#include <stdint.h>
#include <stdbool.h>

/* Status codes returned by UART functions */
typedef enum {
    UART_OK           = 0,
    UART_ERR_PARAM    = -1,
    UART_ERR_NOT_INIT = -2,
    UART_ERR_TIMEOUT  = -3,
} uart_status_t;

/* Configuration structure passed to uart_init() */
typedef struct {
    uint32_t baud_rate;    /* Baud rate in bits/s; 0 = use default 115200 */
    uint8_t  data_bits;    /* Data bits: 7 or 8 */
    uint8_t  stop_bits;    /* Stop bits: 1 or 2 */
    bool     parity_even;  /* true = even parity; false = no parity */
} uart_cfg_t;

/* Public API */
uart_status_t uart_init(const uart_cfg_t *p_cfg);
int32_t       uart_transmit(const uint8_t *p_data, uint16_t len);
uint16_t      uart_tx_available(void);

#endif /* UART_DRIVER_H */
