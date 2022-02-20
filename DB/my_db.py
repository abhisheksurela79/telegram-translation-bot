from Credentials.credentials import Admin
import pymongo


class DB:
    def __init__(self):
        client = pymongo.MongoClient(Admin().credentials()["mongoDB_string"])
        db = client["chats"]
        self.collection = db["chats"]

    def add_new_data(self, id_1, id_2):
        data = {"chat_1": id_1, "chat_2": id_2}
        self.collection.insert_one(data)

    def find_id(self, chat, look_for):
        if chat == 1:
            data = self.collection.find_one({"chat_1": look_for})
            return data["chat_2"]

        elif chat == 2:
            data = self.collection.find_one({"chat_2": look_for})
            return data["chat_1"]

    def delete_existing(self, value_to_delete):
        record = {"chat_1": value_to_delete}
        self.collection.delete_one(record)
