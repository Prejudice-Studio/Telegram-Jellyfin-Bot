from flask import Flask, jsonify, request

from src.config import FlaskConfig
from src.database.user import UsersOperate

app = Flask(__name__)


# 路由设置，处理 Jellyfin Webhook
@app.route('/webhook', methods=['POST'])
async def webhook():
    if request:
        print("Flask", request.data)
    return jsonify({'status': 'success'}), 200


def run_flask():
    app.run(host=FlaskConfig.HOST, port=FlaskConfig.PORT)
