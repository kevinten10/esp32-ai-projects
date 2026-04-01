/*
 * OLED 显示组件实现
 */

#include "oled_display.h"

OLEDDisplay::OLEDDisplay(int sdaPin, int sclPin)
    : _display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET),
      _sdaPin(sdaPin), _sclPin(sclPin) {
}

bool OLEDDisplay::begin() {
    Wire.begin(_sdaPin, _sclPin);
    
    if (!_display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
        Serial.println("SSD1306 初始化失败");
        return false;
    }
    
    _display.clearDisplay();
    _display.setTextSize(1);
    _display.setTextColor(SSD1306_WHITE);
    _display.display();
    
    Serial.println("OLED 初始化成功");
    return true;
}

void OLEDDisplay::clear() {
    _display.clearDisplay();
}

void OLEDDisplay::display() {
    _display.display();
}

void OLEDDisplay::setTextSize(uint8_t size) {
    _display.setTextSize(size);
}

void OLEDDisplay::setCursor(int x, int y) {
    _display.setCursor(x, y);
}

void OLEDDisplay::print(const char* text) {
    _display.print(text);
}

void OLEDDisplay::println(const char* text) {
    _display.println(text);
}

void OLEDDisplay::showStatus(const char* status) {
    _display.clearDisplay();
    _display.setTextSize(1);
    _display.setCursor(0, 0);
    _display.println("状态:");
    _display.setTextSize(2);
    _display.setCursor(0, 16);
    _display.print(status);
    _display.display();
}

void OLEDDisplay::showData(const char* label, float value, const char* unit) {
    _display.clearDisplay();
    _display.setTextSize(1);
    _display.setCursor(0, 0);
    _display.print(label);
    _display.setTextSize(2);
    _display.setCursor(0, 16);
    _display.print(value, 1);
    _display.setTextSize(1);
    _display.print(unit);
    _display.display();
}
