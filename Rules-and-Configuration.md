# CStyleCheck — Rules and Configuration Reference

This document describes every rule enforced by CStyleCheck, including its rule
ID, default severity, YAML configuration keys, what it checks, and annotated
C code examples showing both passing and failing code.

All rules are configured in `rules.yml`.  Every rule supports an
`enabled` key and a `severity` key.  Severity values are `error`, `warning`,
and `info`.

**Exit codes:** `0` clean · `1` one or more errors · `2` config / invocation error

---

## Table of contents

1. [File-level module prefix](#1-file-level-module-prefix)
2. [Variables](#2-variables)
   - [2.1 Scope-level case and length](#21-scope-level-case-and-length)
   - [2.2 Global variables](#22-global-variables)
   - [2.3 Static variables](#23-static-variables)
   - [2.4 Local variables](#24-local-variables)
   - [2.5 Function parameters](#25-function-parameters)
   - [2.6 Pointer prefix (`p_`)](#26-pointer-prefix-p_)
   - [2.7 Double-pointer prefix (`pp_`)](#27-double-pointer-prefix-pp_)
   - [2.8 Boolean prefix (`b_`)](#28-boolean-prefix-b_)
   - [2.9 Handle prefix (`h_`)](#29-handle-prefix-h_)
   - [2.10 No numeric in name](#210-no-numeric-in-name)
   - [2.11 Prefix ordering](#211-prefix-ordering)
3. [Constants and macros](#3-constants-and-macros)
   - [3.1 Constants (`#define` object-like)](#31-constants-define-object-like)
   - [3.2 Macros (`#define` function-like)](#32-macros-define-function-like)
4. [Functions](#4-functions)
   - [4.1 Prefix](#41-prefix)
   - [4.2 Style (Object-Verb / Verb-Object / lower\_snake)](#42-style)
   - [4.3 Length](#43-length)
   - [4.4 Static prefix](#44-static-prefix)
   - [4.5 ISR suffix](#45-isr-suffix)
5. [Typedefs](#5-typedefs)
6. [Enumerations](#6-enumerations)
7. [Structs and unions](#7-structs-and-unions)
8. [Include guards](#8-include-guards)
9. [Miscellaneous](#9-miscellaneous)
   - [9.1 Copyright header](#91-copyright-header)
   - [9.2 EOF comment](#92-eof-comment)
   - [9.3 Line length](#93-line-length)
   - [9.4 Indentation](#94-indentation)
   - [9.5 Magic numbers](#95-magic-numbers)
   - [9.6 Unsigned suffix](#96-unsigned-suffix)
   - [9.7 Block-comment spacing](#97-block-comment-spacing)
   - [9.8 Yoda conditions](#98-yoda-conditions)
10. [Reserved names](#10-reserved-names)
11. [Spell check](#11-spell-check)
12. [Sign compatibility](#12-sign-compatibility)
13. [Quick reference table](#13-quick-reference-table)

---

## 1. File-level module prefix

**Rule IDs affected:** `variable.global.prefix` · `variable.static.prefix` ·
`function.prefix` · `constant.prefix` · `macro.prefix`

**Config key:** `file_prefix`

Every identifier at file scope (globals, statics, functions, macros, constants)
must be prefixed with the module name derived from the source file's base name
(`uart_driver.c` → prefix `uart_driver_`).  Local variables and struct/union
members are exempt.

```yaml
file_prefix:
  enabled: true
  severity: error
  separator: "_"         # inserted between module name and identifier
  case: lower            # lower | upper | as_is
  exempt_main: true      # skip prefix check for main.c / main.h
  exempt_patterns:       # regex patterns exempt from the prefix rule
    - "^main$"
    - "^ISR$"
    - "^app_"            # shared namespace accepted as a valid prefix
```

**`separator`** — the character placed between the module name and the
identifier body.  Default `_`.

**`case`** — how the module name is normalised before comparison.
`lower` (default) means `Uart_Driver.c` is treated as prefix `uart_driver_`.

**`exempt_patterns`** — full Python regex patterns tested against the bare
identifier (without module prefix).  Any match is exempt from the prefix check.

```c
/* File: uart_driver.c   →   expected prefix: uart_driver_ */

/* ✓ PASS */
uint32_t uart_driver_g_baud_rate = 115200U;
void     uart_driver_BufferRead(void);
#define  UART_DRIVER_MAX_BAUD    115200U

/* ✗ FAIL — no module prefix */
uint32_t g_baud_rate = 115200U;       /* variable.global.prefix */
void     BufferRead(void);            /* function.prefix         */
#define  MAX_BAUD    115200U          /* constant.prefix         */
```

---

## 2. Variables

**Config key:** `variables`

### 2.1 Scope-level case and length

**Rule IDs:** `variable.local.case` · `variable.global.case` ·
`variable.static.case` · `variable.parameter.case` ·
`variable.min_length` · `variable.max_length`

```yaml
variables:
  enabled: true
  severity: error
  case: lower_snake        # default for all scopes unless overridden
  min_length: 3            # Barr-C 7.1.e
  max_length: 40
  allow_single_char_loop_vars: true
  allow_loop_vars_short: true
  allowed_abbreviations:   # uppercase tokens permitted inside lower_snake names
    - FIFO
    - MCU
    - UART
    # ... (add project-specific acronyms)
```

**`case`** values: `lower_snake` · `upper_snake` · `camel` · `pascal`.

**`allow_single_char_loop_vars`** — when `true`, a bare `i`, `j`, or `k` used
as a `for`-loop counter is exempt from `min_length`.

**`allow_loop_vars_short`** — broadens the exemption to any short variable that
appears only in a `for (...)` initialiser, covering two-character names like
`ix`.

**`allowed_abbreviations`** — uppercase tokens in this list are allowed inside
an otherwise `lower_snake` name without triggering a case violation.

```c
/* ✓ PASS */
uint8_t  uart_driver_g_rx_count = 0U;  /* lower_snake, length ok  */
uint16_t read_FIFO_registers;          /* FIFO is in abbreviations */
for (int i = 0; i < 10; i++) { }      /* single-char loop var     */

/* ✗ FAIL */
uint8_t  RC = 0U;          /* variable.min_length (length 2 < 3)   */
uint8_t  rxCount;          /* variable.local.case — not lower_snake */
uint8_t  this_variable_name_is_absurdly_long_and_exceeds_the_limit;
         /* variable.max_length */
```

---

### 2.2 Global variables

**Rule IDs:** `variable.global.case` · `variable.global.prefix` ·
`variable.global.g_prefix`

```yaml
variables:
  global:
    severity: error
    case: lower_snake
    require_module_prefix: true
    g_prefix:
      enabled: true
      severity: warning
      prefix: "g_"        # local part (after module prefix) must start with g_
```

Global (extern-linkage) variables must carry both the file-level module prefix
**and** a `g_` marker immediately after it.

```c
/* File: sensor.c   →   module prefix: sensor_ */

/* ✓ PASS */
uint32_t sensor_g_temperature = 0U;

/* ✗ FAIL */
uint32_t sensor_temperature = 0U;   /* variable.global.g_prefix — missing g_ */
uint32_t g_temperature = 0U;        /* variable.global.prefix   — missing module prefix */
```

---

### 2.3 Static variables

**Rule IDs:** `variable.static.case` · `variable.static.prefix` ·
`variable.static.s_prefix`

```yaml
variables:
  static:
    severity: error
    case: lower_snake
    require_module_prefix: true
    s_prefix:
      enabled: true
      severity: warning
      prefix: "s_"
```

File-scope `static` variables follow the same module-prefix rule as globals but
use `s_` instead of `g_`.

```c
/* File: motor.c   →   module prefix: motor_ */

/* ✓ PASS */
static uint16_t motor_s_pwm_duty = 0U;

/* ✗ FAIL */
static uint16_t motor_pwm_duty   = 0U;  /* variable.static.s_prefix */
static uint16_t s_pwm_duty       = 0U;  /* variable.static.prefix   */
```

---

### 2.4 Local variables

**Rule ID:** `variable.local.case`

```yaml
variables:
  local:
    severity: error
    case: lower_snake
    require_module_prefix: false
```

Local (function-body) variables do not require a module prefix.

```c
void uart_driver_Init(void)
{
    /* ✓ PASS */
    uint8_t retry_count = 0U;

    /* ✗ FAIL */
    uint8_t retryCount = 0U;   /* variable.local.case — camel, not lower_snake */
}
```

---

### 2.5 Function parameters

**Rule IDs:** `variable.parameter.case` · `variable.parameter.p_prefix`

```yaml
variables:
  parameter:
    severity: warning
    case: lower_snake
    require_module_prefix: false
    p_prefix:
      enabled: false      # off by default
      severity: warning
      prefix: "p_"
```

When `p_prefix` is enabled every parameter name must start with `p_`.  If the
parameter is also a pointer it needs both: `p_p_buffer` (parameter prefix then
pointer prefix).

```c
/* p_prefix disabled (default) */
void uart_driver_Send(uint8_t *p_data, uint16_t length)
{   /* ✓ PASS — lower_snake, pointer prefix applied, no p_ required */ }

/* p_prefix enabled */
void uart_driver_Send(uint8_t *p_p_data, uint16_t p_length)
{   /* ✓ PASS — p_p_data = param prefix + pointer prefix */ }

void uart_driver_Send(uint8_t *p_data, uint16_t length)
{   /* ✗ FAIL — length is missing p_ prefix when p_prefix is enabled */ }
```

---

### 2.6 Pointer prefix (`p_`)

**Rule ID:** `variable.pointer_prefix`

```yaml
variables:
  pointer_prefix:
    enabled: true
    severity: warning
    prefix: "p_"
```

Any variable declared with a single `*` must have the local part of its name
start with `p_`.  Applies at all scopes.

```c
/* ✓ PASS */
uint8_t *p_rx_buffer;
uint8_t *uart_driver_g_p_rx_head;

/* ✗ FAIL */
uint8_t *rx_buffer;          /* variable.pointer_prefix — missing p_ */
```

---

### 2.7 Double-pointer prefix (`pp_`)

**Rule ID:** `variable.pp_prefix`

```yaml
variables:
  pp_prefix:
    enabled: true
    severity: warning
    prefix: "pp_"
```

Double-pointer (`**`) variables must start with `pp_`.

```c
/* ✓ PASS */
uint8_t **pp_buffers;

/* ✗ FAIL */
uint8_t **p_buffers;    /* variable.pp_prefix — should be pp_, not p_ */
uint8_t **buffers;      /* variable.pp_prefix — missing pp_            */
```

---

### 2.8 Boolean prefix (`b_`)

**Rule ID:** `variable.bool_prefix`

```yaml
variables:
  bool_prefix:
    enabled: false      # off by default
    severity: warning
    prefix: "b_"
```

When enabled, any variable of type `bool` or `_Bool` must start with `b_`.
Phrasing as a question is recommended (`b_is_done`, `b_has_error`).

```c
/* bool_prefix enabled */

/* ✓ PASS */
bool b_is_initialised = false;

/* ✗ FAIL */
bool is_initialised = false;    /* variable.bool_prefix — missing b_ */
bool initialised    = false;    /* variable.bool_prefix               */
```

---

### 2.9 Handle prefix (`h_`)

**Rule ID:** `variable.handle_prefix`

```yaml
variables:
  handle_prefix:
    enabled: true
    severity: warning
    prefix: "h_"
    handle_types:
      - FILE
      - TaskHandle_t
      - QueueHandle_t
      - SemaphoreHandle_t
      # ... add project-specific handle types
```

Variables whose declared type appears in `handle_types` must start with `h_`.
Add every non-pointer handle type used in the project to this list.

```c
/* ✓ PASS */
TaskHandle_t  h_led_task;
QueueHandle_t h_uart_rx_queue;
FILE         *p_log_file;          /* FILE* is a pointer — pointer prefix applies */

/* ✗ FAIL */
TaskHandle_t  led_task;            /* variable.handle_prefix — missing h_ */
QueueHandle_t uart_rx_queue;       /* variable.handle_prefix               */
```

---

### 2.10 No numeric in name

**Rule ID:** `variable.no_numeric_in_name`

```yaml
variables:
  no_numeric_in_name:
    enabled: false      # off by default — enable for strict Barr-C compliance
    severity: warning
    exempt_patterns:
      - "^uart[0-9]+$"     # peripheral port numbers always allowed
      - "^spi[0-9]+$"
      - ".*_[0-9]+(ms|us|hz|mhz|bit|bits|byte|bytes|baud)$"
```

Barr-C 7.1.g prohibits embedding a number in a variable name when that number
is "called out elsewhere" (e.g. encodes the array size or bit width).

```c
/* ✓ PASS */
uint32_t receive_buffer[32];   /* size is in the type, not the name */
uint32_t uart2_status;         /* uart2 matches exempt_patterns      */
uint32_t delay_100ms;          /* unit suffix matches exempt_patterns */

/* ✗ FAIL (when enabled) */
uint32_t buffer32;             /* variable.no_numeric_in_name */
uint32_t array8;               /* variable.no_numeric_in_name */
```

---

### 2.11 Prefix ordering

**Rule ID:** `variable.prefix_order`

```yaml
variables:
  prefix_order:
    enabled: false      # off by default
    severity: warning
```

When multiple prefixes apply (`g_`, `p_`/`pp_`, `b_`/`h_`) they must appear in
scope → pointer → type order.

| Combination | Correct form |
|---|---|
| Global + pointer | `g_p_buffer` |
| Global + double-pointer | `g_pp_table` |
| Global + bool | `g_b_ready` |
| Pointer + bool | `p_b_flag` |
| Global + pointer + bool | `g_p_b_enabled` |

```c
/* prefix_order enabled */

/* ✓ PASS */
bool *uart_driver_g_p_b_flag;       /* g_ then p_ then b_  */

/* ✗ FAIL */
bool *uart_driver_p_g_b_flag;       /* variable.prefix_order — p_ before g_ */
```

---

## 3. Constants and macros

### 3.1 Constants (`#define` object-like)

**Rule IDs:** `constant.case` · `constant.min_length` · `constant.max_length` ·
`constant.prefix`

```yaml
constants:
  enabled: true
  severity: error
  case: upper_snake
  min_length: 2
  max_length: 60
  exempt_patterns:       # regex patterns exempt from case and prefix rules
    - "^NULL$"
    - "^TRUE$"
    - "^FALSE$"
    - "^__"              # compiler / RTOS reserved names
    - "^configUSE_"      # FreeRTOS config macros
    - "^STATIC$"
    - "^INLINE$"
```

Object-like `#define` constants must be `UPPER_SNAKE_CASE` and carry the module
prefix.  `exempt_patterns` allows well-known third-party names that cannot be
renamed.

```c
/* File: uart_driver.c */

/* ✓ PASS */
#define UART_DRIVER_MAX_BAUD_RATE    115200U
#define UART_DRIVER_RX_BUFFER_SIZE   256U

/* ✗ FAIL */
#define max_baud_rate  115200U   /* constant.case   — not upper_snake */
#define MAX_BAUD_RATE  115200U   /* constant.prefix — missing module prefix */
#define UB             115200U   /* constant.min_length — length 2 boundary */
```

---

### 3.2 Macros (`#define` function-like)

**Rule IDs:** `macro.case` · `macro.min_length` · `macro.max_length` ·
`macro.prefix`

```yaml
macros:
  enabled: true
  severity: error
  case: upper_snake
  max_length: 60
  exempt_patterns:
    - "^__"
    - "^configASSERT$"
    - "^taskENTER_CRITICAL$"
    - "^taskEXIT_CRITICAL$"
```

Function-like macros (those with a `(` immediately after the name) follow the
same `UPPER_SNAKE` + module-prefix rules as constants.

```c
/* File: crc.c */

/* ✓ PASS */
#define CRC_REFLECT_BYTE(b)    ((uint8_t)(((b) * 0x0202020202ULL) >> 32U))

/* ✗ FAIL */
#define reflectByte(b)         ...   /* macro.case   — not upper_snake */
#define REFLECT_BYTE(b)        ...   /* macro.prefix — missing crc_ prefix */
```

---

## 4. Functions

### 4.1 Prefix

**Rule ID:** `function.prefix`

Every function name must begin with the file's module prefix.  `main()` in
`main.c` and functions matching `exempt_patterns` are exempt.

```yaml
functions:
  enabled: true
  severity: error
```

```c
/* File: adc.c   →   module prefix: adc_ */

/* ✓ PASS */
void adc_ChannelRead(uint8_t channel);

/* ✗ FAIL */
void ChannelRead(uint8_t channel);   /* function.prefix */
```

---

### 4.2 Style

**Rule ID:** `function.style`

```yaml
functions:
  style: object_verb     # object_verb | verb_object | lower_snake
  object_case: pascal    # how each Object word is capitalised
  verb_case: pascal      # how each Verb word is capitalised
  allowed_abbreviations:
    - FIFO
    - ADC
    - UART
  object_exclusions:
    - Init               # segments that waive the style check entirely
    - Wr
    - Rd
```

CStyleCheck supports three function body styles (the part after the module
prefix):

| Style | Example |
|---|---|
| `object_verb` | `uart_driver_BufferRead` |
| `verb_object` | `uart_driver_ReadBuffer` |
| `lower_snake` | `uart_driver_buffer_read` |

`object_exclusions` lists body segments that disable the style check entirely —
useful for established abbreviations that act as both object and verb.

```c
/* style: object_verb */

/* ✓ PASS */
void uart_driver_BufferRead(void);
void uart_driver_StatusGet(void);
void uart_driver_Init(void);          /* Init in object_exclusions — waived */

/* ✗ FAIL */
void uart_driver_readBuffer(void);    /* function.style — verb first, lower-case */
void uart_driver_buffer_read(void);   /* function.style — lower_snake, not object_verb */
```

---

### 4.3 Length

**Rule IDs:** `function.min_length` · `function.max_length`

```yaml
functions:
  min_length: 4
  max_length: 60
```

The full function name (including module prefix) must be within these bounds.

```c
/* ✓ PASS */
void uart_driver_Init(void);      /* length = 17 */

/* ✗ FAIL */
void ab(void);                    /* function.min_length — length 2 < 4 */
void uart_driver_ReceiveAndProcessIncomingByteStreamWithFullParityCheckAndRetry(void);
                                  /* function.max_length — exceeds 60   */
```

---

### 4.4 Static prefix

**Rule ID:** `function.static_prefix`

```yaml
functions:
  static_prefix:
    enabled: false      # off by default
    prefix: "prv_"
    severity: warning
```

When enabled, every `static` function that does not already carry an ISR suffix
must have its body (after the module prefix) start with the configured prefix.
The Barr-C convention is `prv_` to indicate "private".

```c
/* File: scheduler.c  static_prefix enabled, prefix: "prv_" */

/* ✓ PASS */
static void scheduler_prv_TimerExpired(void);

/* ✗ FAIL */
static void scheduler_TimerExpired(void);   /* function.static_prefix */
```

---

### 4.5 ISR suffix

**Rule ID:** (part of `function.style` checks; configured under `isr_suffix`)

```yaml
functions:
  isr_suffix:
    enabled: true
    severity: warning
    suffix: "_IRQHandler"
```

Interrupt service routine handlers must end with the configured suffix.
Functions carrying this suffix are exempt from `static_prefix` and
`object_verb` / `verb_object` style checks.

```c
/* ✓ PASS */
void USART1_IRQHandler(void);

/* ✗ FAIL — when isr_suffix is enabled */
void USART1_Handler(void);     /* suffix mismatch */
```

---

## 5. Typedefs

**Rule IDs:** `typedef.case` · `typedef.suffix`

```yaml
typedefs:
  enabled: true
  severity: warning
  case: upper_snake
  suffix:
    enabled: true
    suffix: "_T"
```

All `typedef` aliases must be `UPPER_SNAKE_CASE` and end with `_T`.

```c
/* ✓ PASS */
typedef uint8_t        BYTE_T;
typedef struct uart_config_s UART_CONFIG_T;

/* ✗ FAIL */
typedef uint8_t        byte_t;         /* typedef.case   — not upper_snake */
typedef uint8_t        BYTE;           /* typedef.suffix — missing _T       */
typedef struct uart_config_s UartConfig;   /* typedef.case   — PascalCase  */
```

---

## 6. Enumerations

**Rule IDs:** `enum.type_case` · `enum.type_suffix` · `enum.member_case` ·
`enum.member_prefix`

```yaml
enums:
  enabled: true
  severity: error
  type_case: lower_snake
  type_suffix:
    enabled: true
    suffix: "_t"
  member_case: upper_snake
  member_prefix_from_type:
    enabled: true
    severity: warning
```

Enum type names use `lower_snake_t`; member names use `UPPER_SNAKE` and must be
prefixed with the enum type name (stripped of `_t`, converted to upper snake).

```c
/* ✓ PASS */
typedef enum
{
    UART_STATUS_OK,
    UART_STATUS_ERROR,
    UART_STATUS_TIMEOUT,
} uart_status_t;

/* ✗ FAIL */
typedef enum
{
    Ok,               /* enum.member_case   — not upper_snake          */
    STATUS_OK,        /* enum.member_prefix — missing UART_STATUS_ prefix */
} UartStatus;         /* enum.type_case / enum.type_suffix              */
```

---

## 7. Structs and unions

**Rule IDs:** `struct.tag_case` · `struct.tag_suffix` · `struct.member_case`

```yaml
structs:
  enabled: true
  severity: warning
  tag_case: lower_snake
  tag_suffix:
    enabled: true
    suffix: "_s"
  member_case: lower_snake
  allowed_abbreviations: []   # same concept as variables.allowed_abbreviations
```

Struct / union tags use `lower_snake_s`; member names use `lower_snake`.

```c
/* ✓ PASS */
typedef struct uart_config_s
{
    uint32_t baud_rate;
    uint8_t  data_bits;
    uint8_t  stop_bits;
} UART_CONFIG_T;

/* ✗ FAIL */
typedef struct UartConfig        /* struct.tag_case — PascalCase, no _s suffix */
{
    uint32_t BaudRate;           /* struct.member_case — PascalCase            */
} UART_CONFIG_T;
```

**`allowed_abbreviations`** works exactly like the variable equivalent — list
any uppercase acronyms that should be permitted in `lower_snake` member names:

```yaml
structs:
  allowed_abbreviations:
    - FIFO
    - CRC
```

```c
typedef struct dma_config_s
{
    uint16_t FIFO_depth;    /* ✓ PASS — FIFO is in allowed_abbreviations */
    uint32_t CRC_seed;      /* ✓ PASS */
} DMA_CONFIG_T;
```

---

## 8. Include guards

**Rule IDs:** `include_guard.missing` · `include_guard.format`

```yaml
include_guards:
  enabled: true
  severity: error
  pattern: "{FILENAME_UPPER}_{EXT_UPPER}_"
  allow_pragma_once: true
```

Every header file must have either an include guard in the format
`{FILENAME_UPPER}_{EXT_UPPER}_` or a `#pragma once`.

For `uart_driver.h` the expected guard is `UART_DRIVER_H_`.

```c
/* ✓ PASS — traditional guard */
#ifndef UART_DRIVER_H_
#define UART_DRIVER_H_

/* ... header content ... */

#endif /* UART_DRIVER_H_ */


/* ✓ PASS — pragma once */
#pragma once


/* ✗ FAIL — guard name does not match pattern */
#ifndef UART_DRIVER_H      /* include_guard.format — missing trailing _ */
#define UART_DRIVER_H
...
#endif

/* ✗ FAIL — no guard at all */
/* (header file with no #ifndef and no #pragma once) */
/* include_guard.missing */
```

---

## 9. Miscellaneous

### 9.1 Copyright header

**Rule ID:** `misc.copyright_header`

```yaml
misc:
  copyright_header:
    enabled: true       # active whenever --copyright FILE is supplied on the CLI
    severity: error
```

**Activated by:** `--copyright FILE` on the command line.  When this flag is
absent the rule is silently skipped.

Every C source file must begin with the copyright block comment template
contained in the given file, followed by **exactly one blank line**.  The match
is character-perfect except that the year (or year range) on the line containing
`(C) Copyright` may differ — any four-digit year or `YYYY-YYYY` range is
accepted, case-insensitively.

**Copyright template file (`src/copyright_header.txt`):**

```
/*
 * MyProject Firmware
 * (C) Copyright 2024 My Company Ltd.  All rights reserved.
 *
 * SPDX-License-Identifier: Proprietary
 */
```

**Usage:**

```bash
python src/cstylecheck.py --copyright src/copyright_header.txt source/**/*.c
```

```c
/* ✓ PASS — 2021 differs from 2024 in template; still accepted */
/*
 * MyProject Firmware
 * (C) Copyright 2021 My Company Ltd.  All rights reserved.
 *
 * SPDX-License-Identifier: Proprietary
 */

void module_Init(void) { }


/* ✗ FAIL — wrong company name */
/*
 * MyProject Firmware
 * (C) Copyright 2024 Different Corp.  All rights reserved.
 *
 * SPDX-License-Identifier: Proprietary
 */
/* misc.copyright_header — company name mismatch */


/* ✗ FAIL — missing blank line after */ */
/*
 * MyProject Firmware
 * (C) Copyright 2024 My Company Ltd.  All rights reserved.
 *
 * SPDX-License-Identifier: Proprietary
 */
void module_Init(void) { }   /* misc.copyright_header — no blank line after header */
```

---

### 9.2 EOF comment

**Rule ID:** `misc.eof_comment`

```yaml
misc:
  eof_comment:
    enabled: false      # set to true to enforce
    severity: warning
    template: "/* EOF: {filename} */"
    filename_case: lower    # lower | upper | preserve
```

When enabled, the last non-blank line of every file must exactly equal the
template string with `{filename}` replaced by the file's base name (case
adjusted per `filename_case`).  Exactly one blank line must follow.

| `filename_case` | For file `Uart_Driver.C` |
|---|---|
| `lower` (default) | `/* EOF: uart_driver.c */` |
| `upper` | `/* EOF: UART_DRIVER.C */` |
| `preserve` | `/* EOF: Uart_Driver.C */` |

```c
/* File: uart_driver.c   eof_comment enabled, filename_case: lower */

void uart_driver_Init(void) { }

/* ✓ PASS — last non-blank line correct, one blank line follows */
/* EOF: uart_driver.c */
                        ← blank line here (end of file)

/* ✗ FAIL — wrong filename */
/* EOF: uart.c */

/* ✗ FAIL — two blank lines after comment */
/* EOF: uart_driver.c */
                        ← blank line
                        ← second blank line  →  misc.eof_comment
```

---

### 9.3 Line length

**Rule ID:** `misc.line_length`

```yaml
misc:
  line_length:
    enabled: true
    severity: warning
    max: 180
```

Lines exceeding `max` characters trigger a violation.  Comment-only lines are
not exempt — all lines are checked.

```c
/* ✓ PASS */
static void uart_driver_prv_HandleError(uint8_t error_code);  /* 53 chars */

/* ✗ FAIL */
static void uart_driver_prv_HandleRecoverableTransmissionErrorWithRetryAndLogging(uint8_t error_code, uint16_t retry_limit, bool b_log_to_flash);
/* misc.line_length — exceeds 180 chars */
```

---

### 9.4 Indentation

**Rule ID:** `misc.indentation`

```yaml
misc:
  indentation:
    enabled: true
    severity: info
    style: tabs       # spaces | tabs
    width: 8
```

Every non-blank, non-comment line must begin with the configured indentation
style.  Mixing tabs and spaces triggers a violation.

```c
/* style: tabs */

/* ✓ PASS */
void uart_driver_Init(void)
{
	uint8_t retry = 0U;          /* ← tab indent */
}

/* ✗ FAIL */
void uart_driver_Init(void)
{
    uint8_t retry = 0U;          /* ← spaces used, tabs required  misc.indentation */
}
```

---

### 9.5 Magic numbers

**Rule ID:** `misc.magic_number`

```yaml
misc:
  magic_numbers:
    enabled: true
    severity: warning
    exempt_values: [0, 1, -1, 2, 8, 16, 32, 64, 128, 256, 1024, 0xFF, 0xFFFF]
```

Numeric literals that are not in `exempt_values` and do not appear in a
`#define` RHS, array subscript, or `return` statement must be replaced with a
named constant.

```c
/* ✓ PASS */
#define UART_DRIVER_MAX_RETRIES    5U
uint8_t retry_count = UART_DRIVER_MAX_RETRIES;

uint8_t buf[256];          /* 256 is in exempt_values */
return 0;                  /* return literal exempt    */

/* ✗ FAIL */
uint8_t retry_count = 5U;  /* misc.magic_number — 5 not in exempt list */
if (timeout > 1000U) { }   /* misc.magic_number — 1000 not in exempt list */
```

---

### 9.6 Unsigned suffix

**Rule ID:** `misc.unsigned_suffix`

```yaml
misc:
  unsigned_suffix:
    enabled: true
    severity: info
    require_on_unsigned_constants: true
    zero_is_neutral: true
    exempt_function_args:
      - memset
      - printf
      - snprintf
      # add project-specific functions with signed int parameters
```

Integer literals that could be assigned to an unsigned type must carry a `U` or
`u` suffix.  `zero_is_neutral: true` exempts the literal `0`.

```c
/* ✓ PASS */
uint32_t timeout   = 1000U;
uint8_t  mask      = 0xFFU;
uint16_t buf[128U];
uint8_t  init_val  = 0;       /* zero is neutral */

memset(buf, 0xFF, sizeof(buf));  /* memset exempt — int c parameter */

/* ✗ FAIL */
uint32_t timeout  = 1000;    /* misc.unsigned_suffix — missing U */
uint8_t  mask     = 0xFF;    /* misc.unsigned_suffix             */
```

---

### 9.7 Block-comment spacing

**Rule ID:** `misc.block_comment_spacing`

```yaml
misc:
  block_comment_spacing:
    enabled: false      # off by default
    severity: warning
    min_blank_lines: 1
    max_blank_lines: 2
```

After the closing `*/` of a **multi-line** block comment, the number of blank
lines before the next non-blank line must be within `[min, max]`.  Single-line
`/* ... */` comments are not checked.

```c
/* min_blank_lines: 1  max_blank_lines: 2 */

/* ✓ PASS — one blank line */
/*
 * Initialise the UART peripheral.
 */

void uart_driver_Init(void) { }


/* ✓ PASS — two blank lines */
/*
 * Initialise the UART peripheral.
 */


void uart_driver_Init(void) { }


/* ✗ FAIL — zero blank lines */
/*
 * Initialise the UART peripheral.
 */
void uart_driver_Init(void) { }   /* misc.block_comment_spacing */


/* ✗ FAIL — three blank lines */
/*
 * Initialise the UART peripheral.
 */



void uart_driver_Init(void) { }   /* misc.block_comment_spacing */
```

---

### 9.8 Yoda conditions

**Rule ID:** `misc.yoda_condition`

```yaml
misc:
  yoda_conditions:
    enabled: true
    severity: warning
```

In `==` and `!=` comparisons the constant must appear on the **left**.  This
turns an accidental `=` assignment into a compile-time error.  Directional
operators (`<`, `>`, `<=`, `>=`) are not checked.

```c
/* ✓ PASS — constant on left */
if (NULL == p_buffer)      { }
if (UART_STATUS_OK == ret) { }
while (0U == retry_count)  { }

/* ✗ FAIL — variable on left */
if (p_buffer == NULL)      { }   /* misc.yoda_condition */
if (ret == UART_STATUS_OK) { }   /* misc.yoda_condition */
```

---

## 10. Reserved names

**Rule ID:** `reserved_name`

```yaml
reserved_names:
  enabled: true
  severity: error
```

No declared variable, function, macro, or constant may shadow a C keyword, C++
keyword, or C standard library name.  The built-in lists are in
`src/c_keywords.txt` and `src/c_stdlib_names.txt`.  Additional names can be
banned at run time with `--banned-names FILE`.

```c
/* ✓ PASS */
uint32_t uart_driver_g_byte_count;
void     uart_driver_MemoryCopy(void);

/* ✗ FAIL */
uint32_t malloc;           /* reserved_name — C stdlib */
uint32_t class;            /* reserved_name — C++ keyword */
void     printf(void);     /* reserved_name — C stdlib */
#define  assert(x) (x)     /* reserved_name — C stdlib macro */
```

---

## 11. Spell check

**Rule ID:** `spell_check`

```yaml
spell_check:
  enabled: false          # set to true to enable
  severity: info
  exempt_values:
    - "FreeRTOS"
    - "CMSIS"
    - "HAL"
    - "buf"
    - "cfg"
    # ... add project abbreviations
```

When enabled, every word in every comment is checked against a built-in English
dictionary merged with the `exempt_values` list and any words supplied via
`--spell-words FILE`.

```c
/* ✓ PASS */
/* Initialise the UART peripheral with the configured baud rate. */

/* ✓ PASS — buf is in exempt_values */
/* Copy to the rx buf. */

/* ✗ FAIL */
/* Initilise the UART periferal. */   /* spell_check — Initilise, periferal */
```

**Extending the dictionary:**

```bash
# One word per line, # = comment
echo "Sensoteq" >> src/spell_words.txt
python src/cstylecheck.py --spell-words src/spell_words.txt source/**/*.c
```

---

## 12. Sign compatibility

**Rule ID:** `sign_compatibility`

```yaml
sign_compatibility:
  enabled: true
  severity: error
  plain_char_is_signed: true
```

Detects cross-file mismatches where an explicitly signed or unsigned literal is
passed to a parameter of the opposite signedness.  Type resolution follows
`typedef` chains across all files in the scan.

Argument classification:

| Literal | Classification |
|---|---|
| `100U`, `0xFFU` | UNSIGNED |
| `-1`, `(signed int)x` | SIGNED |
| `42`, `0xFF` (no suffix) | NEUTRAL — accepted by either |
| Variable / expression | UNKNOWN — skipped conservatively |

**`plain_char_is_signed`** — controls how bare `char` (without `signed` or
`unsigned`) is treated.  Most embedded toolchains default to signed char.

```c
/* header.h */
void uart_driver_Send(uint8_t length);   /* unsigned parameter */

/* caller.c */

/* ✓ PASS — neutral literal accepted for either signedness */
uart_driver_Send(10);

/* ✓ PASS — unsigned literal matches unsigned parameter */
uart_driver_Send(10U);

/* ✗ FAIL — signed literal to unsigned parameter */
uart_driver_Send(-1);    /* sign_compatibility */
```

---

## 13. Quick reference table

| Rule ID | Default severity | YAML key | Default |
|---|---|---|---|
| `variable.global.case` | error | `variables.global.case` | `lower_snake` |
| `variable.global.prefix` | error | `variables.global.require_module_prefix` | `true` |
| `variable.global.g_prefix` | warning | `variables.global.g_prefix.enabled` | `true` |
| `variable.static.case` | error | `variables.static.case` | `lower_snake` |
| `variable.static.prefix` | error | `variables.static.require_module_prefix` | `true` |
| `variable.static.s_prefix` | warning | `variables.static.s_prefix.enabled` | `true` |
| `variable.local.case` | error | `variables.local.case` | `lower_snake` |
| `variable.parameter.case` | warning | `variables.parameter.case` | `lower_snake` |
| `variable.parameter.p_prefix` | warning | `variables.parameter.p_prefix.enabled` | `false` |
| `variable.min_length` | error | `variables.min_length` | `3` |
| `variable.max_length` | error | `variables.max_length` | `40` |
| `variable.pointer_prefix` | warning | `variables.pointer_prefix.enabled` | `true` |
| `variable.pp_prefix` | warning | `variables.pp_prefix.enabled` | `true` |
| `variable.bool_prefix` | warning | `variables.bool_prefix.enabled` | `false` |
| `variable.handle_prefix` | warning | `variables.handle_prefix.enabled` | `true` |
| `variable.no_numeric_in_name` | warning | `variables.no_numeric_in_name.enabled` | `false` |
| `variable.prefix_order` | warning | `variables.prefix_order.enabled` | `false` |
| `constant.case` | error | `constants.case` | `upper_snake` |
| `constant.min_length` | error | `constants.min_length` | `2` |
| `constant.max_length` | error | `constants.max_length` | `60` |
| `constant.prefix` | error | `file_prefix.enabled` | `true` |
| `macro.case` | error | `macros.case` | `upper_snake` |
| `macro.min_length` | error | `macros.min_length` | *(from constants)* |
| `macro.max_length` | error | `macros.max_length` | `60` |
| `macro.prefix` | error | `file_prefix.enabled` | `true` |
| `function.prefix` | error | `functions.enabled` + `file_prefix.enabled` | `true` |
| `function.style` | error | `functions.style` | `object_verb` |
| `function.min_length` | error | `functions.min_length` | `4` |
| `function.max_length` | error | `functions.max_length` | `60` |
| `function.static_prefix` | warning | `functions.static_prefix.enabled` | `false` |
| `typedef.case` | warning | `typedefs.case` | `upper_snake` |
| `typedef.suffix` | warning | `typedefs.suffix.enabled` | `true` |
| `enum.type_case` | error | `enums.type_case` | `lower_snake` |
| `enum.type_suffix` | error | `enums.type_suffix.enabled` | `true` |
| `enum.member_case` | error | `enums.member_case` | `upper_snake` |
| `enum.member_prefix` | warning | `enums.member_prefix_from_type.enabled` | `true` |
| `struct.tag_case` | warning | `structs.tag_case` | `lower_snake` |
| `struct.tag_suffix` | warning | `structs.tag_suffix.enabled` | `true` |
| `struct.member_case` | warning | `structs.member_case` | `lower_snake` |
| `include_guard.missing` | error | `include_guards.enabled` | `true` |
| `include_guard.format` | error | `include_guards.pattern` | `{FILENAME_UPPER}_{EXT_UPPER}_` |
| `misc.copyright_header` | error | `misc.copyright_header.enabled` | `true` (requires `--copyright`) |
| `misc.eof_comment` | warning | `misc.eof_comment.enabled` | `false` |
| `misc.line_length` | warning | `misc.line_length.max` | `180` |
| `misc.indentation` | info | `misc.indentation.style` | `tabs` |
| `misc.magic_number` | warning | `misc.magic_numbers.enabled` | `true` |
| `misc.unsigned_suffix` | info | `misc.unsigned_suffix.enabled` | `true` |
| `misc.block_comment_spacing` | warning | `misc.block_comment_spacing.enabled` | `false` |
| `misc.yoda_condition` | warning | `misc.yoda_conditions.enabled` | `true` |
| `reserved_name` | error | `reserved_names.enabled` | `true` |
| `spell_check` | info | `spell_check.enabled` | `false` |
| `sign_compatibility` | error | `sign_compatibility.enabled` | `true` |
