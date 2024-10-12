from jellyfin_apiclient_python import JellyfinClient

from src.config import JellyfinConfig
from src.model import RegCodesModel, UsersModel

UsersData = UsersModel("Users.json")
RegCodeData = RegCodesModel("RegCode.json")

# 连接服务器
client = JellyfinClient()


def check_server_connectivity() -> bool:
    """
    检查服务器连接性
    :return: bool
    """
    try:
        client.jellyfin.get_system_info()
        return True
    except Exception:
        return False


def init_client():
    client.config.data["auth.ssl"] = False
    client.config.data["app.name"] = 'telegram'
    client.config.data["app.version"] = '0.0.1'
    client.auth.connect_to_address(JellyfinConfig.BASE_URL)
    auth_config = {"Servers": [{"AccessToken": JellyfinConfig.API_KEY, "address": JellyfinConfig.BASE_URL}]}
    client.authenticate(auth_config, discover=False)
    try:
        client.start()
    except Exception as e:
        print(e)


init_client()
