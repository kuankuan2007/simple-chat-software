# 消息收发简易

自制的，借助服务器互相发送消息的程序

## 使用说明

### 服务端

config.json中配置监听端口、监听地址

然后直接运行即可

### 客户端

在config.json中设置服务器的地址、端口

打开后输入用户名（内容随意，不低于2字符）

然后就可以多端发送消息啦

### 注意

客户端60s没有消息视为下线，删除用户（即其他人可以使用该用户名）

传输使用aes加密，秘钥为登录时服务端向客户端分发，期间不可修改


