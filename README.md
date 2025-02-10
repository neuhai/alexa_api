# alexa_api

[![PyPI - Version](https://img.shields.io/pypi/v/alexa-api.svg)](https://pypi.org/project/alexa-api/1.0.1/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/alexa-api.svg)](https://pypi.org/project/alexa-api/1.0.1/)
[![License](https://img.shields.io/pypi/l/alexa-api.svg)](https://spdx.org/licenses/MIT.html)

-----

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [API Reference](#api_reference)
- [License](#license)


## Installation

```console
pip install alexa-api
```

## Usage
To use the library, first download from https://github.com/adn77/alexa-cookie-cli/releases/tag/v5.0.1

Run the program and go to http://127.0.0.1:8080 to log in your Amazon account and obtain a refresh token.

Here is a sample usage:

```Python
import alexa_api

# Define your Alexa refresh token
refresh_token = "your_refresh_token_here"

# Retrieve the list of Alexa devices
devices = alexa_api.get_device_list(refresh_token)
print(devices)

# Make Alexa speak a custom message
alexa_api.execute_command("speak", "Hello, how can I help you?", refresh_token, "Your Echo Dot")

# Send a text command to Alexa (e.g., open a skill)
alexa_api.execute_command("textcommand", "Alexa, open my demo", refresh_token, "Your Echo Dot")
```


## Features
- Get a list of Alexa devices: Retrieve all devices associated with an account using the refresh token.
- Make Alexa Speak: Send a message to Alexa and have it spoken aloud.
- Execute Commands: Simulate real user usage programmatically by sending text-based commands like open a skill.

## API Reference

```Python
get_device_list(refresh_token)
```
Parameters:
- `refresh_token`: the refresh token of your account.

```Python
execute_command(command_type, command_message, refresh_token, device)
```

Parameters:
- `command_type`: the type of the command.
    - Use `speak` to let Alexa speak out the text.
    - Use `textcommand` to send a text-based command to Alexa.
- `command_message`: the message content of the command.
    - If using `speak` command: `command_message` is the text that will be read out by Alexa.
    - If using `textcommand` command: `command_message` is the command context that will be sent to Alexa.
- `refresh_token`: the refresh token of your account.
- `device`: (Optional) the device name of the device that you want the command to execute on. If not specified, the first device in the device list will be used by default.



## License

`alexa-api` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
