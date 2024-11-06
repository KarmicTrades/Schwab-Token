import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

ca = certifi.where()

load_dotenv(dotenv_path="config.env")

MONGO_URI = os.getenv("MONGO_URI")


class MongoDB:

    def connect_mongo(self):

        try:

            if MONGO_URI:

                self.client = MongoClient(
                    MONGO_URI, authSource="admin", tlsCAFile=ca)

                self.db = self.client["Api_Trader"]

                self.users = self.db["users"]

            else:

                raise Exception("FAILED TO CONNECT TO MONGO!")

        except Exception as e:

            print(e)
