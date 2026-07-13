/**
 * @file uart_driver.c
 * @brief UART peripheral driver - Barr-C / MISRA-C compliant example.
 *
 * Demonstrates idiomatic embedded C patterns that CStyleCheck accepts.
 * Used as a stable scan target for trend-analysis metrics.
 */

#include "uart_driver.h"
#include <stddef.h>
#include <string.h>

/* Module-level configuration constants */
#define UART_BAUD_DEFAULT  115200U
#define UART_BUF_SIZE      256U
#define UART_TIMEOUT_MS    100U

/* Ring-buffer state */
static uint8_t  g_uart_tx_buf[UART_BUF_SIZE];
static uint32_t g_uart_tx_head = 0U;
static uint32_t g_uart_tx_tail = 0U;
static bool     g_uart_initialised = false;

/**
 * @brief Initialise the UART peripheral.
 * @param p_cfg  Pointer to caller-supplied configuration; must not be NULL.
 * @return UART_OK on success, UART_ERR_PARAM if p_cfg is NULL.
 */
uart_status_t uart_init(const uart_cfg_t *p_cfg)
{
    if (NULL == p_cfg) {
        return UART_ERR_PARAM;
    }

    /* Reset ring-buffer pointers */
    g_uart_tx_head = 0U;
    g_uart_tx_tail = 0U;

    /* Apply baud rate - fall back to default if zero */
    uint32_t baud_rate = (0U != p_cfg->baud_rate) ? p_cfg->baud_rate
                                                   : UART_BAUD_DEFAULT;
    (void)baud_rate; /* platform write omitted in this example */

    g_uart_initialised = true;
    return UART_OK;
}

/**
 * @brief Transmit a buffer of bytes over UART.
 * @param p_data  Pointer to data buffer.
 * @param len     Number of bytes to transmit.
 * @return Number of bytes queued, or negative on error.
 */
int32_t uart_transmit(const uint8_t *p_data, uint16_t len)
{
    if ((NULL == p_data) || (0U == len)) {
        return (int32_t)UART_ERR_PARAM;
    }

    if (!g_uart_initialised) {
        return (int32_t)UART_ERR_NOT_INIT;
    }

    uint16_t queued = 0U;
    for (uint16_t i = 0U; i < len; i++) {
        uint32_t next_head = (g_uart_tx_head + 1U) % UART_BUF_SIZE;

        /* Drop byte if buffer is full */
        if (next_head == g_uart_tx_tail) {
            break;
        }

        g_uart_tx_buf[g_uart_tx_head] = p_data[i];
        g_uart_tx_head = next_head;
        queued++;
    }

    return (int32_t)queued;
}

/**
 * @brief Return number of bytes available in the TX ring buffer.
 */
uint16_t uart_tx_available(void)
{
    uint32_t head = g_uart_tx_head;
    uint32_t tail = g_uart_tx_tail;

    if (head >= tail) {
        return (uint16_t)(UART_BUF_SIZE - head + tail);
    }
    return (uint16_t)(tail - head);
}
