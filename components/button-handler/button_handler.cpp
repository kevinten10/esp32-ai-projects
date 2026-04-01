/*
 * 按钮处理组件实现
 */

#include "button_handler.h"

ButtonHandler::ButtonHandler(int pin, ButtonCallback callback)
    : _pin(pin), _callback(callback),
      _lastState(HIGH), _currentState(HIGH),
      _pressTime(0), _lastClickTime(0), _clickCount(0),
      _longPressDuration(2000), _doubleClickWindow(300),
      _longPressed(false) {
}

void ButtonHandler::begin() {
    pinMode(_pin, INPUT_PULLUP);
}

void ButtonHandler::loop() {
    ButtonEvent event = detectEvent();
    
    if (event != BUTTON_EVENT_NONE && _callback) {
        _callback(event);
    }
}

void ButtonHandler::setLongPressDuration(unsigned long duration) {
    _longPressDuration = duration;
}

void ButtonHandler::setDoubleClickWindow(unsigned long window) {
    _doubleClickWindow = window;
}

ButtonEvent ButtonHandler::detectEvent() {
    _currentState = digitalRead(_pin);
    ButtonEvent event = BUTTON_EVENT_NONE;
    
    // 按钮按下
    if (_currentState == LOW && _lastState == HIGH) {
        _pressTime = millis();
        _longPressed = false;
    }
    
    // 按钮释放
    if (_currentState == HIGH && _lastState == LOW) {
        unsigned long pressDuration = millis() - _pressTime;
        
        // 检查是否长按
        if (pressDuration >= _longPressDuration) {
            event = BUTTON_EVENT_LONG_PRESS;
            _longPressed = true;
        } else {
            _clickCount++;
            
            // 检查双击
            if (_clickCount == 1) {
                _lastClickTime = millis();
            } else if (_clickCount == 2) {
                if (millis() - _lastClickTime <= _doubleClickWindow) {
                    event = BUTTON_EVENT_DOUBLE_CLICK;
                    _clickCount = 0;
                }
            }
            
            // 超时后视为单击
            if (_clickCount == 1 && millis() - _lastClickTime > _doubleClickWindow) {
                event = BUTTON_EVENT_CLICK;
                _clickCount = 0;
            }
        }
    }
    
    // 检查长按中
    if (_currentState == LOW && !_longPressed) {
        if (millis() - _pressTime >= _longPressDuration) {
            event = BUTTON_EVENT_LONG_PRESS;
            _longPressed = true;
        }
    }
    
    _lastState = _currentState;
    return event;
}
