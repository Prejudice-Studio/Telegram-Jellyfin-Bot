FROM python:3.10-slim

RUN apt-get update && apt-get install -y git

WORKDIR /app/

RUN git clone https://github.com/MoYuanCN/Telegram-Jellyfin-Bot.git /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'git pull' >> /app/start.sh && \
    echo 'python bot.py' >> /app/start.sh && \
    chmod +x /app/start.sh

CMD ["/app/start.sh"]