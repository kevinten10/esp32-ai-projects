/*
 * 传感器工具组件实现
 */

#include "sensor_utils.h"

SensorUtils::SensorUtils(int dataPin)
    : _dht(dataPin, DHT_TYPE),
      _lastTemp(0), _lastHumidity(0), _lastReadTime(0) {
}

bool SensorUtils::begin() {
    _dht.begin();
    
    // 检查传感器是否可用
    if (isnan(_dht.readTemperature())) {
        Serial.println("DHT 传感器初始化失败");
        return false;
    }
    
    Serial.println("DHT 传感器初始化成功");
    return true;
}

float SensorUtils::readTemperature() {
    unsigned long now = millis();
    
    // 每 2 秒读取一次
    if (now - _lastReadTime < 2000) {
        return _lastTemp;
    }
    
    float temp = _dht.readTemperature();
    
    if (!isnan(temp)) {
        _lastTemp = temp;
        _lastReadTime = now;
    }
    
    return _lastTemp;
}

float SensorUtils::readHumidity() {
    unsigned long now = millis();
    
    if (now - _lastReadTime < 2000) {
        return _lastHumidity;
    }
    
    float hum = _dht.readHumidity();
    
    if (!isnan(hum)) {
        _lastHumidity = hum;
        _lastReadTime = now;
    }
    
    return _lastHumidity;
}

float SensorUtils::readHeatIndex() {
    float temp = readTemperature();
    float hum = readHumidity();
    return _dht.computeHeatIndex(temp, hum, false);
}

float SensorUtils::celsiusToFahrenheit(float celsius) {
    return (celsius * 9.0 / 5.0) + 32.0;
}

float SensorUtils::fahrenheitToCelsius(float fahrenheit) {
    return (fahrenheit - 32.0) * 5.0 / 9.0;
}
