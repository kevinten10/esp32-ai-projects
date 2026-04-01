/*
 * 传感器工具组件
 *
 * 功能：
 * - DHT 温湿度读取
 * - 数据滤波
 * - 单位转换
 */

#ifndef SENSOR_UTILS_H
#define SENSOR_UTILS_H

#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <pin-config.h>

#define DHT_TYPE DHT22

class SensorUtils {
public:
    SensorUtils(int dataPin = DHT_PIN);
    
    bool begin();
    float readTemperature();
    float readHumidity();
    float readHeatIndex();
    
    // 工具函数
    static float celsiusToFahrenheit(float celsius);
    static float fahrenheitToCelsius(float fahrenheit);
    
private:
    DHT _dht;
    float _lastTemp;
    float _lastHumidity;
    unsigned long _lastReadTime;
};

#endif // SENSOR_UTILS_H
