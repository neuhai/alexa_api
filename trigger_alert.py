from pymongo import MongoClient
from datetime import datetime
from alert_handler import send_command

MONGO_URI = "mongodb+srv://wli273088:wgzHhvWWe8Nowh9D@cluster0.v3cn1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "alexa_alerts"
COLLECTION_NAME = "alerts"

def add_alert(user_id, message):
    """Add a new alert to MongoDB."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    alert = {
        "userId": user_id,
        "message": message,
        "delivered": True,
        "timestamp": datetime.utcnow()
    }

    collection.insert_one(alert)
    print(f"Added alert for user {user_id}")


# userId = "amzn1.ask.account.AMAU6X2C3AOMLZDKT4C3HEDWM65JR5TGUKYFPYAANUZXXUJ3IRX7KKJN6DVFHE42UM3XI3SNXOGRIMA3ZAVLKZR3OY4WJQQQFRK2L4EACN75375O452TQIJ3XR5WX63HJ5LH4RKRVHHOAJR4D5XMKRNLEFJROLAXWYNAVOQCLQEEOAS2ZUHIGIOQJLF23EPSA6TQJASAU54HUKBFM3XPSNO7YWPKIZ5SFBVPBVW6SA"
userId = "amzn1.ask.account.AMAZMRESRVCDNZM3C3YGSHF6WORAMWNP5M6DMIUSU3O5GQRE6FQPTGLA47ERWHC63GVLW262MLPSR3UAGX2ACY2IXJO5YPTGUHON2AH3CS5M7W5MOCH24KCRRALF3QSGS53KQNG2CVEBIO4JN7P6XNUZQA2HOVISM2VTPGUFIAMMMDLMN7HI3FGTRFP5UQYUMU6XAURVPGOIUJAOATU3DQDDAWBFWAP5OZR7Z6QOPA"
alert_message = "You forgot to close your refrigerator door."

add_alert(userId, alert_message)
send_command(userId, alert_message)