FROM python:3.10-slim

WORKDIR /app/

# 复制 requirements.txt 以确保可以安装依赖
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制所有源码到容器中
COPY . .

CMD ["python", "bot.py"]