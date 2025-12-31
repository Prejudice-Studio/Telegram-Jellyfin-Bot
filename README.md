# Telegram-Jellyfin-Bot
一个简单的Telegram Jellyfin/Emby Bot

**技术栈**: Docker · Python · Jellyfin-ApiClient-Python · Python-Telegram-Bot · EmbyAPI

**开发者**: 
- [MoYuanCN](https://github.com/MoYuanCN/)
- [Enlysure](https://github.com/Rovniced/)

---

## 🚀 快速开始

### 网络连接说明

如果您的运行环境无法直接连接Telegram，请选择以下任一方案：

- 在`config.toml`中配置代理
- 使用自定义Telegram API地址
- 将运行环境切换至可访问Telegram的网络

---

## 📦 部署方式

### 1. Docker Compose（推荐）

```bash
wget -O docker-compose.yml https://raw.githubusercontent.com/Prejudice-Studio/Telegram-Jellyfin-Bot/refs/heads/emby/docker-compose.yml
wget -O Dockerfile https://raw.githubusercontent.com/Prejudice-Studio/Telegram-Jellyfin-Bot/refs/heads/emby/Dockerfile
docker-compose build
docker-compose up -d
```

### 2. Docker 直接运行

```bash
docker run -d \
  --name Telegram-Jellyfin-Bot \
  --restart always \
  -v $(pwd)/config.toml:/app/config.toml \
  enlysure/telegram-jellyfin-bot:latest
```

**前置步骤**：

1. 下载[`config.production.toml`](https://raw.githubusercontent.com/Prejudice-Studio/Telegram-Jellyfin-Bot/refs/heads/emby/config.production.toml)
2. 重命名为`config.toml`并修改配置
3. 确保配置文件位于当前目录

### 3. 手动Python部署

```bash
# 1. 安装Python 3.10+
# 2. 克隆项目
git clone https://github.com/Prejudice-Studio/Telegram-Jellyfin-Bot.git
cd Telegram-Jellyfin-Bot

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置
cp config.production.toml config.toml
# 编辑config.toml文件

# 5. 运行
python bot.py
```

---

## 📊 项目数据

### Star History

<a href="https://www.star-history.com/#Prejudice-Studio/Telegram-Jellyfin-Bot&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Prejudice-Studio/Telegram-Jellyfin-Bot&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Prejudice-Studio/Telegram-Jellyfin-Bot&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Prejudice-Studio/Telegram-Jellyfin-Bot&type=date&legend=top-left" />
 </picture>
</a>

### 贡献者

感谢所有贡献者！✨

![Contributors](https://contrib.rocks/image?repo=MoYuanCN/telegram-Jellyfin-Bot)

---

## 📝 配置说明

详细配置选项请参考[`config.production.toml`](https://raw.githubusercontent.com/Prejudice-Studio/Telegram-Jellyfin-Bot/refs/heads/emby/config.production.toml)中的注释说明。