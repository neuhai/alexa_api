import requests
import re
import json
import os
from datetime import datetime, timedelta


alexa_domain = "alexa.amazon.com"
amazon = "amazon.com"
tts_locale = "en_US"

def run_cmd(command, device_type, device_serial_number, media_owner_customer_id, cookie):
    # Base headers
    session = requests.Session()
    session.cookies.update(cookie)
    headers = {
        "DNT": "1",
        "Connection": "keep-alive",
        "Content-Type": "application/json; charset=UTF-8",
        "Referer": f"https://alexa.{amazon}/spa/index.html",
        "Origin": f"https://alexa.{amazon}",
        "csrf": extract_csrf(session),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:1.0) bash-script/1.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    # print(cookie)

    print(session.cookies.get_dict())

    
    # Handle `textcommand` requests
    if command.startswith("textcommand:"):
        sequence_cmd = 'Alexa.TextCommand\",\"skillId\":\"amzn1.ask.1p.tellalexa'
        text = command.split("textcommand:", 1)[1].replace('"', "'")
        sequence_val = f',"text":"{text}"'
        alexa_cmd = build_alexa_command(sequence_cmd, sequence_val, device_type, device_serial_number, media_owner_customer_id, tts_locale)
    
    # Handle `speak` requests
    elif command.startswith("speak:"):
        tts = command.split("speak:", 1)[1].replace('"', "'")
        sequence_cmd = "Alexa.Speak"
        sequence_val = f',"textToSpeak":"{tts}"'
        alexa_cmd = build_alexa_command(sequence_cmd, sequence_val, device_type, device_serial_number, media_owner_customer_id, tts_locale)
    
    else:
        raise ValueError("Unsupported command type")
    
    # Send request
    response = session.post(
        f"https://{alexa_domain}/api/behaviors/preview",
        headers=headers,
        json=alexa_cmd
    )
    
    # Debugging
    print("Request Headers:", headers)
    print("Request Payload:", alexa_cmd)
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)
    
    return response.status_code, response.text


def extract_csrf(session):
    """Attempts to fetch the CSRF token using multiple fallback methods."""
    urls = [
        f"https://{alexa_domain}/api/language",
        f"https://{alexa_domain}/templates/oobe/d-device-pick.handlebars",
        f"https://{alexa_domain}/api/devices-v2/device?cached=false"
    ]
    
    for url in urls:
        response = session.get(url, headers={
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": f"https://alexa.{amazon}/spa/index.html",
            "Origin": f"https://alexa.{amazon}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:1.0) bash-script/1.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9"
        })
        
        if response.status_code == 200:
            csrf_token = session.cookies.get("csrf")
            if csrf_token:
                print("Extracted CSRF Token:", csrf_token)
                return csrf_token
    
    print("ERROR: No CSRF token received!")
    return None



def build_alexa_command(sequence_cmd, sequence_val, device_type, device_serial_number, media_owner_customer_id, tts_locale):
    """Build the Alexa command JSON."""
    nodes_to_execute = (
        f'{{"@type":"com.amazon.alexa.behaviors.model.OpaquePayloadOperationNode",'
        f'"type":"{sequence_cmd}",'
        f'"operationPayload":{{'
        f'"deviceType":"{device_type}",'
        f'"deviceSerialNumber":"{device_serial_number}",'
        f'"customerId":"{media_owner_customer_id}",'
        f'"locale":"{tts_locale}"{sequence_val}}}}}'
    )

    return {
        "behaviorId": "PREVIEW",
        "sequenceJson": f'{{"@type":"com.amazon.alexa.behaviors.model.Sequence","startNode":{{"@type":"com.amazon.alexa.behaviors.model.ParallelNode","nodesToExecute":[{nodes_to_execute}]}}}}',
        "status": "ENABLED",
    }


def get_devlist(cookie):

    # Set up headers
    headers = {
        "DNT": "1",
        "Connection": "keep-alive",
        "Content-Type": "application/json; charset=UTF-8",
        "Referer": f"https://alexa.{amazon}/spa/index.html",
        "Origin": f"https://alexa.{amazon}",
        # "csrf": extract_csrf(cookie),
    }

    # Fetch device list from Alexa API
    url = f"https://{alexa_domain}/api/devices-v2/device?cached=false"
    response = requests.get(url, headers=headers, cookies=cookie)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch device list. HTTP Status: {response.status_code}")
    


    # Load the JSON data
    devlist = response.json()

    return devlist



def set_device(devlist, device=None):
    # Ensure 'devices' key is in the dictionary and it's a list
    if not isinstance(devlist, dict) or "devices" not in devlist or not isinstance(devlist["devices"], list):
        print("Invalid device list format.")
        return {}

    # Iterate through devices in the list
    for device_info in devlist["devices"]:
        if device != None:
            if device_info.get("accountName") == device:
                return {
                    "device": device_info.get("accountName", "Unknown Device"),
                    "deviceserialnumber": device_info["serialNumber"],
                    "devicefamily": device_info["deviceFamily"],
                    "devicetype": device_info["deviceType"],
                }
        # if device not specified: find the first ECHO device.
        elif "ECHO" in device_info.get("deviceFamily", ""):

            # Ensure all required keys are present
            required_keys = {"deviceType", "serialNumber", "deviceFamily"}
            if not required_keys.issubset(device_info.keys()):
                print("Invalid device entry format in device list.")
                continue
            
            return {
                "device": device_info.get("accountName", "Unknown Device"),
                "deviceserialnumber": device_info["serialNumber"],
                "devicefamily": device_info["deviceFamily"],
                "devicetype": device_info["deviceType"],
            }

    print("No suitable device found")
    return {}


def check_status(cookies):
    headers = {
        "DNT": "1",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:1.0) bash-script/1.0"
    }
    
    url = f"https://{alexa_domain}/api/bootstrap?version=0"
    response = requests.get(url, headers=headers, cookies=cookies, allow_redirects=True)
    # print(response.text)
    
    if response.status_code == 200:
        try:
            data = response.json()
            authentication = data.get("authentication", {})
            if authentication.get("authenticated"):
                return authentication.get("customerId")
        except ValueError:
            print("Error: Invalid JSON response.")
    else:
        print(f"Error: Request failed with status code {response.status_code}")
    
    return None


def fetch_cookie_with_refresh_token(refresh_token):
    # API endpoint and headers
    url = f"https://api.{amazon}/ap/exchangetoken/cookies"
    headers = {
        "x-amzn-identity-auth-domain": f"api.{amazon}",
    }
    payload = {
        "app_name": "Amazon Alexa",
        "requested_token_type": "auth_cookies",
        "domain": f"www.{amazon}",
        "source_token_type": "refresh_token",
        "source_token": refresh_token,
    }

    # Send the POST request
    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        print(f"ERROR: Failed to fetch cookies. HTTP Status: {response.status_code}")
        return False

    # Parse the JSON response
    response_data = response.json()
    if "response" not in response_data or "tokens" not in response_data["response"] or "cookies" not in response_data["response"]["tokens"]:
        print("ERROR: Invalid response format.")
        return False

    cookies = response_data["response"]["tokens"]["cookies"]


    flattened = {}
    for domain, cookie in cookies.items():
        for c in cookie:
            flattened[c["Name"]] = c["Value"]  # Extract Name-Value pairs
    return flattened



def execute_command(command_type, command_message, refresh_token, device=None):

    # Step 1: Fetch the cookie
    print("Fetching cookies...")

    cookies = fetch_cookie_with_refresh_token(refresh_token)

    # Step 2: Fetch the device list
    print("Fetching device list...")
    dev_list = get_devlist(cookies)

    # Step 3: Find the target device
    print("Finding the target device...")
    device_info = set_device(dev_list)

    device_type = device_info["devicetype"]
    device_serial_number = device_info["deviceserialnumber"]

    print(device_info)

    customerId = check_status(cookies)

    # Step 4: Execute the command
    print("Executing the command...")
    command = f"{command_type}:\"{command_message}\""
    status_code, response_text = run_cmd(command, device_type, device_serial_number, customerId, cookies)
    print(status_code, response_text)

    return status_code, response_text