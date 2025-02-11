from main import execute_command, get_device_list

from importlib.metadata import version
import time

import logging

logging.basicConfig(level=logging.DEBUG)


logger = logging.getLogger(__name__)

alert_message = "You forgot to close your refrigerator door."

refresh_token = "Atnr|EwICIEgz9TQFOsnKgFutlZXPMdIOJZmq-9cI8urAo1WBv64FFMx6a8-cQv-pWvO1nZFVHsqYqCTUv7h33QFawJC58ch5SNIhptcXPE1qMr9tU5u7iOCuS5c28eAmOsObiDsn3V4z_5dXLPHOfTeY-fbDM56YNRm4mkcPuurArELgYP3pez4oewUfXaJpDKMdzdCf0xSp4Wpxzdfe9s7odcayDaBgQB_xdgKsci6af95SSj-TpS6HXXuNRyRd-3CboGInrZAt4sRxrztrruU1J5MvOXKExqLlZNpehm32buP1WNWJJVhgXvsfpPAlaftXA1cjzUs"
# print(get_device_list(refresh_token))

execute_command("textcommand", "Alexa, open my demo", refresh_token, "Wenbo's Echo Dot")

time.sleep(2)

# execute_command("speak", "hehe", refresh_token)
