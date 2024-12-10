from src.model import UsersModel

bb = UsersModel()
# print(bb.userList)
ttt = next((u for u in bb.userList if "洛天依" in u.TelegramFullName), None)
print(ttt)