# Telegram-Jellyfin-Bot
A Easy Telegram Jellyfin Bot

Use Docker Python Jellyfin-ApiClient-Python Python-Telegram-Bot

# 功能如下

## /reg JellyfinUsername JellyfinPassword RegCode
- 注册新的Jellyfin账号并自动与当前Telegram账号绑定

## /info
- 查看当前账号的基本信息

## /bind JellyfinUsername JellyfinPassword
- 将当前Telegram账号绑定至已有的Jellyfin账号

## /unbind JellyfinUsername JellyfinPassword
- 将Telegram账号与当前绑定的Jellyfin账号解绑

## /sign
- 签到，随机获取1-10积分(分数范围可根据源码修改)，积分暂无用处，可自行添加

## /delete
- 删除当前Telegram账号绑定的Jellyfin账号

# 管理员指令

## /checkinfo [TelegramUserID/JellyfinUsername]
- 查询对应TelegramUserID/JellyfinUsername的相关信息(包含密码)

## deleteAccountBy [TelegramUserID/JellyfinUsername]
- 删除对应TelegramUserID/JellyfinUsername的Jellyfin账号

## /regcodes
- 查看当前所有注册码

## /summon use_limit count
- 生成注册码，包含可使用次数与注册码数量
- 可选参数: validity_hours
- 到期时间，留空默认为永久，单位为小时

## /op TelegramUserID
- 添加Bot管理员
- !!!!仅Bot Owner可用

# 使用方法

## 0.Telegram无法以中国大陆网络环境直连，请确保你的运行环境能够连接至Telegram

## 1.确保安装了Docker

## 2.下载该项目的Zip文件

## 3.将Zip文件解压至任意空文件夹

## 4.进入文件夹内，修改如下内容
```
server_url = 'http/https://YOUR_SERVER_IP:PORT' 替换为你的Jellyfin服务器IP
# account = 'Administrators Username' 替换为你的Jellyfin服务器管理员用户名
# password = 'Administrators Password' 替换为你的Jellyfin服务器管理员用户名对应密码
access_token = 'Your_Jellyfin_App_Token' 替换为你的Jellyfin应用密钥Token(自行寻找创建方式)
```
```
token("Your_Telegram_Bot_Api_Token") 替换为你的Telegram Bot Api Token
```

## 5.打开终端，进入该项目文件夹内

## 6.先后执行以下命令，回车
```
docker-compose build
docker-compose up -d
```

## 7.运行成功
控制台显示 Bot Started，则代表Bot成功启动

## 8.关闭Bot
打开终端，进入该文件夹
输入以下指令，回车
```
docker-compose down
```
