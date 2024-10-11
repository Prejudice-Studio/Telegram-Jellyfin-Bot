# Telegram-Jellyfin-Bot
A Easy Telegram Jellyfin Bot

Use Docker

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
- 生成注册码，包含使用次数与数量
- 可选参数: validity_hours
- 到期时间，留空默认为永久

## /op TelegramUserID
- 添加Bot管理员
- !!!!仅Bot Owner可用
