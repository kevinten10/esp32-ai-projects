/*
 * OLED 显示组件 (SSD1306)
 *
 * 功能：
 * - 文本显示
 * - 图形绘制
 * - 多页面管理
 */

#ifndef OLED_DISPLAY_H
#define OLED_DISPLAY_H

#include <Adafruit_SSD1306.h>
#include <pin-config.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

class OLEDDisplay {
public:
    OLEDDisplay(int sdaPin = OLED_SDA, int sclPin = OLED_SCL);
    
    bool begin();
    void clear();
    void display();
    
    // 文本显示
    void setTextSize(uint8_t size);
    void setCursor(int x, int y);
    void print(const char* text);
    void println(const char* text);
    
    // 快捷显示
    void showStatus(const char* status);
    void showData(const char* label, float value, const char* unit);
    
private:
    Adafruit_SSD1306 _display;
    int _sdaPin;
    int _sclPin;
};

#endif // OLED_DISPLAY_H
