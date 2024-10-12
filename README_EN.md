---

# Telegram-Jellyfin-Bot

An Easy Telegram Jellyfin Bot.

Uses Docker, Python, Jellyfin-ApiClient-Python, and Python-Telegram-Bot.

Other Language : [简体中文](README.md)

Developers:
- [MoYuanCN](https://github.com/MoYuanCN/)
- [Enlysure](https://github.com/Rovniced)

# Features

## /reg JellyfinUsername JellyfinPassword RegCode
- Register a new Jellyfin account and automatically bind it to the current Telegram account.

## /info
- View basic information about the current account.

## /bind JellyfinUsername JellyfinPassword
- Bind the current Telegram account to an existing Jellyfin account.

## /unbind JellyfinUsername JellyfinPassword
- Unbind the Telegram account from the currently bound Jellyfin account.

## /sign
- Check in and randomly receive 1-10 points (the score range can be modified according to the source code), points are temporarily useless, you can add other feathers for it yourself.

## /delete
- Delete the Jellyfin account bound to the current Telegram account.

# Administrator Commands

## /checkinfo [TelegramUserID/JellyfinUsername]
- Check the relevant information (including password) for the corresponding TelegramUserID/JellyfinUsername.

## /deleteAccountBy [TelegramUserID/JellyfinUsername]
- Delete the Jellyfin account corresponding to the TelegramUserID/JellyfinUsername.

## /regcodes
- View all current registration codes.

## /summon use_limit count
- Generate registration codes, including the number of uses and the number of registration codes.
- Optional parameter: validity_hours
- Expiration time, leave blank by default for permanent, unit is hours.

## /op TelegramUserID
- Add a Bot administrator.
- !!!! Only Bot Owner can use it.

# Usage

## 0. Telegram cannot be connected directly with Chinese mainland network environment. Ensure that your running environment can connect to Telegram.

## 1. Ensure Docker is installed.

## 2. Download the Zip file of this project.

## 3. Extract the Zip file to any empty folder.

## 4. Enter the folder , open bot.py and modify the following content:
```
server_url =http/https://YOUR_SERVER_IP:PORT Replace with your Jellyfin server IP
# account =Administrators Username Replace with your Jellyfin server administrator username
# password =Administrators Password Replace with the corresponding password for your Jellyfin server administrator username
access_token =Your_Jellyfin_App_Token Replace with your Jellyfin application key token (find the creation method yourself)
```
```
token("Your_Telegram_Bot_Api_Token") Replace with your Telegram Bot Api Token
```

## 5. Open the terminal, enter the project folder.

## 6. Successively execute the following commands and press Enter:
```
docker-compose build
docker-compose up -d
```

## 7. Run successfully.
The console displays "Bot Started", which means the Bot has been successfully started.

## 8. Close the Bot.
Open the terminal, enter the folder, and enter the following command and press Enter:
```
docker-compose down
```
