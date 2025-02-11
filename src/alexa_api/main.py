import requests
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

alexa_domain = "alexa.amazon.com"
amazon = "amazon.com"
tts_locale = "en_US"

cookie_list = {}

devlist_list = {}


def run_cmd(
    command_type,
    command_message,
    device_type,
    device_serial_number,
    media_owner_customer_id,
    cookie,
):
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
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Handle `textcommand` requests
    if command_type == "textcommand":
        sequence_cmd = 'Alexa.TextCommand","skillId":"amzn1.ask.1p.tellalexa'
        text = "'" + command_message + "'"
        sequence_val = f',"text":"{text}"'
        alexa_cmd = build_alexa_command(
            sequence_cmd,
            sequence_val,
            device_type,
            device_serial_number,
            media_owner_customer_id,
            tts_locale,
        )

    # Handle `speak` requests
    elif command_type == "speak":
        tts = "'" + command_message + "'"
        sequence_cmd = "Alexa.Speak"
        sequence_val = f',"textToSpeak":"{tts}"'
        alexa_cmd = build_alexa_command(
            sequence_cmd,
            sequence_val,
            device_type,
            device_serial_number,
            media_owner_customer_id,
            tts_locale,
        )

    else:
        logger.error("Unsupported command type")

    # Send request
    response = session.post(
        f"https://{alexa_domain}/api/behaviors/preview", headers=headers, json=alexa_cmd
    )

    return response.status_code, response.text


def extract_csrf(session):
    """Attempts to fetch the CSRF token using multiple fallback methods."""
    urls = [
        f"https://{alexa_domain}/api/language",
        f"https://{alexa_domain}/templates/oobe/d-device-pick.handlebars",
        f"https://{alexa_domain}/api/devices-v2/device?cached=false",
    ]

    for url in urls:
        response = session.get(
            url,
            headers={
                "DNT": "1",
                "Connection": "keep-alive",
                "Referer": f"https://alexa.{amazon}/spa/index.html",
                "Origin": f"https://alexa.{amazon}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:1.0) bash-script/1.0",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

        if response.status_code == 200:
            csrf_token = session.cookies.get("csrf")
            if csrf_token:
                return csrf_token

    logger.error("No CSRF token received.")
    return None


def build_alexa_command(
    sequence_cmd,
    sequence_val,
    device_type,
    device_serial_number,
    media_owner_customer_id,
    tts_locale,
):
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


def get_devlist(refresh_token, refresh=False):
    if refresh_token in devlist_list and not refresh:
        logger.debug("Device list found locally.")
        return devlist_list[refresh_token]
    else:
        if refresh_token not in devlist_list:
            logger.debug("Device list not found locally.")
        return refresh_devlist(refresh_token)


def refresh_devlist(refresh_token):
    logger.debug("Refreshing device list...")
    cookie = fetch_cookie_with_refresh_token(refresh_token)
    devlist = fetch_new_devlist(cookie)
    devlist_list[refresh_token] = devlist
    return devlist


def fetch_new_devlist(cookie):
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
        logger.error(
            f"Failed to fetch device list. HTTP Status: {response.status_code}"
        )

    # Load the JSON data
    devlist = response.json()

    return devlist


def set_device(refresh_token, device=None):
    # Ensure 'devices' key is in the dictionary and it's a list
    devlist = get_devlist(refresh_token, refresh=(device is None))
    if (
        not isinstance(devlist, dict)
        or "devices" not in devlist
        or not isinstance(devlist["devices"], list)
    ):
        logger.error("Invalid device list format.")
        return None

    if not device:
        if (len(devlist["devices"])) == 0:
            logger.error("No available device")
            return {}
        device_info = devlist["devices"][0]
        logger.info("Using first device by default")
        return {
            "device": device_info.get("accountName", "Unknown Device"),
            "deviceSerialNumber": device_info["serialNumber"],
            "deviceFamily": device_info["deviceFamily"],
            "deviceType": device_info["deviceType"],
        }

    device_detail = find_device(devlist, device)
    if device_detail is None:
        logger.debug("Device not found locally.")
        devlist = get_devlist(refresh_token, True)
        device_detail = find_device(devlist, device)

    if device_detail is None:
        logger.error("Device not found")

    return device_detail


def find_device(devlist, device):
    for device_info in devlist["devices"]:
        if device != None:
            if device_info.get("accountName") == device:
                return {
                    "device": device_info.get("accountName", "Unknown Device"),
                    "deviceSerialNumber": device_info["serialNumber"],
                    "deviceFamily": device_info["deviceFamily"],
                    "deviceType": device_info["deviceType"],
                }
    return None


def get_customer_id(cookies):
    headers = {
        "DNT": "1",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:1.0) bash-script/1.0",
    }

    url = f"https://{alexa_domain}/api/bootstrap?version=0"
    response = requests.get(url, headers=headers, cookies=cookies, allow_redirects=True)

    if response.status_code == 200:
        try:
            data = response.json()
            authentication = data.get("authentication", {})
            if authentication.get("authenticated"):
                return authentication.get("customerId")
        except ValueError:
            logger.error("Invalid JSON response.")
    else:
        logger.error(f"Request failed with status code {response.status_code}")

    return None


def fetch_cookie_with_refresh_token(refresh_token):
    current_time = datetime.now(timezone.utc)

    if refresh_token in cookie_list:
        entry = cookie_list[refresh_token]
        expire_times = entry["expire_times"]
        # If any entries expired, fetch new cookies
        for name, expire_time_string in expire_times.items():
            expire_time = datetime.strptime(
                expire_time_string, "%d %b %Y %H:%M:%S GMT"
            ).replace(tzinfo=timezone.utc)
            if expire_time <= current_time:
                logger.debug(
                    f"Cookies expired at {expire_time}. fetching new cookies..."
                )
                new_cookies, new_expire_times = fetch_new_cookies(refresh_token)
                entry["cookies"] = new_cookies
                entry["expire_times"] = new_expire_times
                return new_cookies

        logger.debug("Cookies found locally.")
        return entry.get("cookies")

    logger.debug("No cookie found. fetching new cookies...")
    cookies, expire_times = fetch_new_cookies(refresh_token)
    cookie_list[refresh_token] = {"cookies": cookies, "expire_times": expire_times}
    return cookies


def fetch_new_cookies(refresh_token):
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
        logger.error(f"Failed to fetch cookies. HTTP Status: {response.status_code}")
        return None, None

    # Parse the JSON response
    response_data = response.json()
    if (
        "response" not in response_data
        or "tokens" not in response_data["response"]
        or "cookies" not in response_data["response"]["tokens"]
    ):
        logger.error("Invalid response format.")
        return None, None

    cookies = response_data["response"]["tokens"]["cookies"]

    flattened = {}
    expires = {}
    for domain, cookie in cookies.items():
        for c in cookie:
            flattened[c["Name"]] = c["Value"]
            expires[c["Name"]] = c["Expires"]
    return flattened, expires


def execute_command(command_type, command_message, refresh_token, device=None):
    # Step 1: Fetch the cookie
    logger.debug("Fetching cookies...")

    cookies = fetch_cookie_with_refresh_token(refresh_token)

    # Step 2: Find the target device
    logger.debug("Finding the target device...")
    device_info = set_device(refresh_token, device)

    if not device_info:
        return

    device_type = device_info["deviceType"]
    device_serial_number = device_info["deviceSerialNumber"]

    customerId = get_customer_id(cookies)

    # Step 3: Execute the command
    logger.debug("Executing the command...")
    status_code, response_text = run_cmd(
        command_type,
        command_message,
        device_type,
        device_serial_number,
        customerId,
        cookies,
    )
    logger.debug(f"Response: {status_code}")

    return status_code, response_text


def get_device_list(refresh_token):
    cookies = fetch_cookie_with_refresh_token(refresh_token)

    logger.debug("Fetching device list...")
    dev_list = get_devlist(refresh_token, True)
    account_names = [
        device["accountName"]
        for device in dev_list.get("devices", [])
        if "accountName" in device
    ]
    return account_names
