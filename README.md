# Telegram-Jellyfin-Bot
一个简单的Telegram Jellyfin Bot

Use Docker Python Jellyfin-ApiClient-Python Python-Telegram-Bot

Other Language Introduction: [English](README_EN.md)

开发者: 
- [MoYuanCN](https://github.com/MoYuanCN/)
- [Enlysure](https://github.com/Rovniced/)

# 功能如下
# 用户指令

| 指令                                               | 描述                                      |
|--------------------------------------------------|-----------------------------------------|
| `/reg JellyfinUsername JellyfinPassword RegCode` | 注册新的Jellyfin账号并自动与当前Telegram账号绑定        |
| `/info`                                          | 查看当前账号的基本信息                             |
| `/bind JellyfinUsername JellyfinPassword`        | 将当前Telegram账号绑定至已有的Jellyfin账号           |
| `/unbind JellyfinUsername JellyfinPassword`      | 将Telegram账号与当前绑定的Jellyfin账号解绑           |
| `/sign`                                          | 签到，随机获取1-10积分(分数范围可根据源码修改)，积分暂无用处，可自行添加 |
| `/delete`                                        | 删除当前Telegram账号绑定的Jellyfin账号             |
| `/changepassword JellyfinOldPassword JellyfinNewPassword`      | 修改当前Telegram账号绑定的Jellyfin账号的密码             |
| `/checkpassword`                                        | 查看当前Telegram账号绑定的Jellyfin账号的密码             |

# 管理员指令

| 指令                                                   | 描述                                                         |
|------------------------------------------------------|------------------------------------------------------------|
| `/checkinfo [TelegramUserID/JellyfinUsername]`       | 查询对应TelegramUserID/JellyfinUsername的相关信息(包含密码)             |
| `/deleteAccountBy [TelegramUserID/JellyfinUsername]` | 删除对应TelegramUserID/JellyfinUsername的Jellyfin账号             |
| `/regcodes`                                          | 查看当前所有注册码                                                  |
| `/summon use_limit count`                            | 生成注册码，包含可使用次数与注册码数量，可选参数：validity_hours 到期时间，留空默认为永久，单位为小时 |
| `/op TelegramUserID`                                 | 添加Bot管理员，!!!!仅Bot Owner可用                                  |

# 使用方法

## 如果你的运行环境无法连接至Telegram,请在config.toml中配置代理，或者使用自定义Telegram base url，或将运行环境切换至可以连接至Telegram的网络环境。

## （推荐）使用Docker Compose 构建部署
```
wget -O docker-compose.yml https://raw.githubusercontent.com/Prejudice-Studio/Telegram-Jellyfin-Bot/refs/heads/emby/docker-compose.yml && \
wget -O Dockerfile https://raw.githubusercontent.com/Prejudice-Studio/Telegram-Jellyfin-Bot/refs/heads/emby/Dockerfile && \
docker-compose build && \
docker-compose up -d
```

## 一、Docker 一键部署
    
#### 1.确保安装了Docker

#### 2.下载`config.production.toml`文件，修改文件名为`config.toml`，并修改其中配置项

#### 3.在同目录下执行以下命令
```
docker run -d --name Telegram-Jellyfin-Bot --restart always \
  -v $(pwd)/config.toml:/app/config.toml \
  enlysure/telegram-jellyfin-bot:latest
```

## 二、手动配置python环境执行

#### 1.安装Python3.10及以上版本

#### 2.下载该项目的Zip文件并解压

#### 3.运行`pip install -r requirements.txt`安装依赖

#### 4.将`config.production.toml`文件，修改文件名为`config.toml`，并修改其中配置项

#### 5.运行`python bot.py`启动Bot

# Star History
<div align="center">

<a href="https://star-history.com/#MoYuanCN/Telegram-Jellyfin-bot&month">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Prejudice-Studio/Telegram-Jellyfin-bot&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Prejudice-Studio/Telegram-Jellyfin-bot" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Prejudice-Studio/Telegram-Jellyfin-bot" />
  </picture>
</a>

</div>

# Contributors
![Contributors](https://contrib.rocks/image?repo=MoYuanCN/telegram-Jellyfin-Bot)
