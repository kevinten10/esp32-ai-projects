/*
 * WiFi 管理器组件实现
 */

#include "wifi_manager.h"

WiFiManager::WiFiManager(const char* ssid, const char* password)
    : _ssid(ssid), _password(password), _retryCount(0) {
}

bool WiFiManager::connect() {
    Serial.print("正在连接 WiFi: ");
    Serial.println(_ssid);
    
    WiFi.begin(_ssid, _password);
    
    // 最多尝试 20 次
    while (WiFi.status() != WL_CONNECTED && _retryCount < 20) {
        delay(500);
        Serial.print(".");
        _retryCount++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi 连接成功!");
        Serial.print("IP 地址：");
        Serial.println(WiFi.localIP());
        return true;
    }
    
    Serial.println("\nWiFi 连接失败!");
    return false;
}

bool WiFiManager::isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

String WiFiManager::getIPAddress() {
    return WiFi.localIP().toString();
}

void WiFiManager::disconnect() {
    WiFi.disconnect();
}
