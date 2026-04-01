/*
 * WiFi 管理器组件
 * 
 * 功能：
 * - 自动连接已知网络
 * - 连接失败时创建 AP
 * - 网络状态管理
 */

#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>

class WiFiManager {
public:
    WiFiManager(const char* ssid, const char* password);
    
    bool connect();
    bool isConnected();
    String getIPAddress();
    void disconnect();
    
private:
    const char* _ssid;
    const char* _password;
    int _retryCount;
};

#endif // WIFI_MANAGER_H
