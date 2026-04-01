/*
 * 普中-ESP32 引脚配置文件
 * 
 * 开发板：普中 ESP32 (基于 ESP32-WROOM-32)
 * PlatformIO board: esp32dev
 * 
 * ⚠️ 重要提示：
 * - GPIO 6-11: 连接内部 Flash，不可用
 * - GPIO 34-39: 仅输入，无内部上拉
 * - GPIO 34-39: 无 ADC 功能
 * - ADC2 引脚 (GPIO 0, 2, 4, 12-15): WiFi 启用时不可用
 * - 推荐使用 ADC1 引脚 (GPIO 32-39)
 */

#ifndef PIN_CONFIG_H
#define PIN_CONFIG_H

// ==================== I2C 引脚 ====================
// 普中 ESP32 默认 I2C 引脚
#define I2C_SDA_PIN     21      // 默认 SDA
#define I2C_SCL_PIN     22      // 默认 SCL

// 备用 I2C 引脚（如需要第二个 I2C 总线）
#define I2C_SDA_ALT     26
#define I2C_SCL_ALT     25

// ==================== SPI 引脚 ====================
// VSPI (默认)
#define VSPI_MOSI       23
#define VSPI_MISO       19
#define VSPI_SCK        18
#define VSPI_CS         5

// HSPI (备用)
#define HSPI_MOSI       13
#define HSPI_MISO       12
#define HSPI_SCK        14
#define HSPI_CS         15

// ==================== UART 引脚 ====================
// UART0 (USB 调试，不可更改)
#define UART0_TX        1
#define UART0_RX        3

// UART1 (可用)
#define UART1_TX        17
#define UART1_RX        16

// UART2 (可用)
#define UART2_TX        4
#define UART2_RX        36      // GPIO36 = VP

// ==================== ADC 引脚 ====================
// ADC1 (推荐，不受 WiFi 影响)
#define ADC1_CH0        36      // VP
#define ADC1_CH1        37
#define ADC1_CH2        38
#define ADC1_CH3        39      // VN
#define ADC1_CH4        32
#define ADC1_CH5        33
#define ADC1_CH6        34
#define ADC1_CH7        35

// ADC2 (WiFi 启用时不可用)
#define ADC2_CH0        4
#define ADC2_CH1        0
#define ADC2_CH2        2
#define ADC2_CH3        15
#define ADC2_CH4        13
#define ADC2_CH5        12
#define ADC2_CH6        14
#define ADC2_CH7        27
#define ADC2_CH8        25
#define ADC2_CH9        26

// ==================== PWM 引脚 ====================
// 推荐 PWM 引脚（功能完整）
#define PWM_LED_1       2
#define PWM_LED_2       4
#define PWM_LED_3       12
#define PWM_LED_4       13
#define PWM_LED_5       14
#define PWM_LED_6       15

// ==================== 常用外设默认引脚 ====================

// OLED (SSD1306 I2C)
#define OLED_SDA        I2C_SDA_PIN
#define OLED_SCL        I2C_SCL_PIN
#define OLED_RESET      -1      // 无复位引脚

// DHT22 温湿度传感器
#define DHT_PIN         4       // GPIO4 (ADC2_CH0, 注意 WiFi 冲突)

// 按钮
#define BUTTON_1        35      // GPIO35 (仅输入，推荐)
#define BUTTON_2        34      // GPIO34 (仅输入，推荐)

// 继电器/舵机
#define RELAY_1         26
#define RELAY_2         27
#define SERVO_1         18      // 也可用作 SPI SCK

// 蜂鸣器
#define BUZZER_PIN      2

// ==================== 特殊功能引脚 ====================

// 板载 LED (如果有的话)
#define LED_BUILTIN     2       // 大多数 ESP32 开发板

// Flash 引脚 (不可用!)
#define FLASH_CS        6       // ⚠️ 不可用
#define FLASH_CLK       7       // ⚠️ 不可用
#define FLASH_D0        8       // ⚠️ 不可用
#define FLASH_D1        9       // ⚠️ 不可用
#define FLASH_D2        10      // ⚠️ 不可用
#define FLASH_D3        11      // ⚠️ 不可用

// ==================== 引脚使用建议 ====================
/*
 * ✅ 推荐使用的通用 GPIO:
 *    GPIO 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27
 *
 * ⚠️ 需要注意的引脚:
 *    GPIO 0: 启动模式选择 (拉低进入下载模式)
 *    GPIO 2: 板载 LED, 启动时需要浮空
 *    GPIO 4: ADC2, WiFi 冲突
 *    GPIO 5: SPI CS, 启动时输出
 *    GPIO 12: ADC2, 启动时采样
 *    GPIO 34-39: 仅输入，无上拉
 *
 * ❌ 不可使用的引脚:
 *    GPIO 6-11: 内部 Flash
 */

#endif // PIN_CONFIG_H
