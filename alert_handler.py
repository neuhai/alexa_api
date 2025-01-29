import os
import subprocess
import time
from pymongo import MongoClient
import requests
import json
from datetime import datetime, timedelta
from alexa_remote_control import executeCommand

MONGO_URI = "mongodb+srv://wli273088:wgzHhvWWe8Nowh9D@cluster0.v3cn1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "alexa_alerts"
COLLECTION_NAME = "alerts"
CHECK_INTERVAL = 5



REFRESH_TOKEN_FILE = "refresh_tokens.json"
ALEXA_COOKIE_CLI = "./alexa-cookie-cli-macos-x64"
ALEXA_REMOTE_CONTROL = "./alexa_remote_control.sh"



client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def send_command(user_id, message):
    """
    Send a proactive alert to Alexa-enabled devices.
    """
    # Step 1: Load or create the JSON file
    if not os.path.exists(REFRESH_TOKEN_FILE):
        with open(REFRESH_TOKEN_FILE, 'w') as f:
            json.dump({}, f)

    with open(REFRESH_TOKEN_FILE, 'r') as f:
        refresh_tokens = json.load(f)

    # Step 2: Check if user_id exists in the file
    if user_id not in refresh_tokens:
        print(f"please run this command to get the refresh_token for user {user_id}: ./alexa-cookie-cli-macos-x64 -b amazon.com -p amazon.com -L en-US -a en-US")
        print("Then go to 127.0.0.1:8080 to log in with your Amazon username and password.")
        # Prompt the user to manually input the refresh token
        refresh_token = input("Once you've logged in, paste the refresh_token here: ").strip()
        
        # Store the refresh token in the dictionary
        refresh_tokens[user_id] = refresh_token

        # Save the updated dictionary to the JSON file
        with open(REFRESH_TOKEN_FILE, "w") as file:
            json.dump(refresh_tokens, file, indent=4)

        print(f"Refresh token for user {user_id} has been successfully saved.")
    else:
        print(f"Refresh token for user {user_id} already exists.")
        
    # Step 3: Set environment variables
    refresh_token = refresh_tokens[user_id]
    # os.environ["ALEXA"] = "alexa.amazon.com"
    # os.environ["AMAZON"] = "amazon.com"
    # os.environ["REFRESH_TOKEN"] = refresh_token

    # Step 4: List available devices
    try:
        # device_list_result = subprocess.run(
        #     [ALEXA_REMOTE_CONTROL, "-a"],
        #     capture_output=True, text=True
        # )

        # # Parse the device list
        # device_name = None
        # for line in device_list_result.stdout.splitlines():
        #     if "Echo Dot" in line:
        #         device_name = line.strip()
        #         break

        # if not device_name:
        #     print("No 'Echo Dot' device found in the account.")
        #     return


        # speak_command = [ALEXA_REMOTE_CONTROL, "-d", device_name, "-e", f"speak:\"{message}\""]
        # subprocess.run(speak_command)
        executeCommand(f"speak:\"{message}\"", refresh_token)

    except Exception as e:
        print(f"Error while sending message: {e}")





def check_new_alerts():
    """Continuously check for new alerts and send proactive events."""
    if collection.count_documents({"delivered": False}) == 0:
        print("No new alert detected")
    else:
        new_alerts = collection.find({"delivered": False})
                
        for alert in new_alerts:
            print("New Alert detected: ", alert['message'], " for user ", alert['userId'])
            send_proactive_event(alert["userId"], alert["message"])
            collection.update_one({"_id": alert["_id"]}, {"$set": {"delivered": True}})

def get_new_alerts(userId):
    message = ''
    if collection.count_documents({"delivered": False}) == 0:
        print("No new alert detected")
    else:
        new_alerts = collection.find({"delivered": False})
        for alert in new_alerts:
            print("New Alert detected: ", alert['message'], " for user ", alert['userId'])
            if userId == alert['userId']:
                message += alert['message'] + ' '
            collection.update_one({"_id": alert["_id"]}, {"$set": {"delivered": True}})
    return message
        

if __name__ == "__main__":
    print("Starting checking alerts")
    while True:
        check_new_alerts()
        time.sleep(CHECK_INTERVAL)
