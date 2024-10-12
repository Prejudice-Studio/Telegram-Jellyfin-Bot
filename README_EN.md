---

# Telegram-Jellyfin-Bot

An Easy Telegram Jellyfin Bot.

Uses Docker, Python, Jellyfin-ApiClient-Python, and Python-Telegram-Bot.

其他语言 : [简体中文](README.md)

Developers:
- [MoYuanCN](https://github.com/MoYuanCN/)
- [Enlysure](https://github.com/Rovniced)

# Features
## User Commands

| Command                                     | Description                                                        |
|---------------------------------------------|--------------------------------------------------------------------|
| `/reg JellyfinUsername JellyfinPassword RegCode`  | Register a new Jellyfin account and automatically bind it to the current Telegram account |
| `/info`                                     | View basic information of the current account                      |
| `/bind JellyfinUsername JellyfinPassword`   | Bind the current Telegram account to an existing Jellyfin account  |
| `/unbind JellyfinUsername JellyfinPassword` | Unbind the current Telegram account from the bound Jellyfin account|
| `/sign`                                     | Sign in and randomly gain 1-10 points (the point range can be modified in the source code). Currently, points have no specific use, but custom functionality can be added |
| `/delete`                                   | Delete the Jellyfin account bound to the current Telegram account  |
| `/changepassword JellyfinOldPassword JellyfinNewPassword`                                        | Change the password of the Jellyfin account bound to the current Telegram account          |

## Admin Commands

| Command                                                   | Description                                                                      |
|-----------------------------------------------------------|----------------------------------------------------------------------------------|
| `/checkinfo [TelegramUserID/JellyfinUsername]`            | View detailed information (including passwords) for the specified TelegramUserID/JellyfinUsername |
| `/deleteAccountBy [TelegramUserID/JellyfinUsername]`      | Delete the Jellyfin account associated with the specified TelegramUserID/JellyfinUsername |
| `/regcodes`                                               | View all available registration codes                                             |
| `/summon use_limit count`                                 | Generate registration codes with a specified usage limit and quantity. Optional parameter: `validity_hours` for setting expiration time (in hours), default is permanent if left blank |
| `/op TelegramUserID`                                      | Add a Bot admin, !!!! Only the Bot Owner can use this command                     |



# Usage

## 0. Ensure Your Running Environment Can Connect To Telegram

## 1. Deploy with Docker (One-Click Setup)

#### 1. Ensure Docker is installed.

#### 2. Download the `config.production.toml` file, rename it to `config.toml`, and modify the configuration as needed.

#### 3. Run the following command in the same directory:
```
docker run -d --name Telegram-Jellyfin-Bot --restart always \
  -v $(pwd)/config.toml:/app/config.toml \
  enlysure/telegram-jellyfin-bot:latest
```


## 2. Manual Python Environment Setup

#### 1. Install Python 3.10 or higher.

#### 2. Download the ZIP file of the project and extract it.

#### 3. Run `pip install -r requirements.txt` to install dependencies.

#### 4. Rename the `config.production.toml` file to `config.toml` and adjust the settings as needed.

#### 5. Start the Bot by running `python bot.py`.

# Star History
![Star History](https://starchart.cc/MoYuanCN/telegram-Jellyfin-Bot.svg)

# Contributors
![Contributors](https://contrib.rocks/image?repo=MoYuanCN/telegram-Jellyfin-Bot)
