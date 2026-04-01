/*
 * 按钮处理组件
 *
 * 功能：
 * - 消抖处理
 * - 单击/双击/长按检测
 * - 事件回调
 */

#ifndef BUTTON_HANDLER_H
#define BUTTON_HANDLER_H

#include <Arduino.h>
#include <pin-config.h>

// 按钮事件类型
enum ButtonEvent {
    BUTTON_EVENT_NONE,
    BUTTON_EVENT_CLICK,
    BUTTON_EVENT_DOUBLE_CLICK,
    BUTTON_EVENT_LONG_PRESS
};

// 回调函数类型
typedef void (*ButtonCallback)(ButtonEvent event);

class ButtonHandler {
public:
    ButtonHandler(int pin = BUTTON_1, ButtonCallback callback = nullptr);
    
    void begin();
    void loop();
    
    // 配置
    void setLongPressDuration(unsigned long duration);
    void setDoubleClickWindow(unsigned long window);
    
private:
    int _pin;
    ButtonCallback _callback;
    
    bool _lastState;
    bool _currentState;
    unsigned long _pressTime;
    unsigned long _lastClickTime;
    int _clickCount;
    
    unsigned long _longPressDuration;
    unsigned long _doubleClickWindow;
    
    bool _longPressed;
    
    ButtonEvent detectEvent();
};

#endif // BUTTON_HANDLER_H
