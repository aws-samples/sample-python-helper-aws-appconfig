# Sample AWS AppConfig Helper

A sample helper Python library for AWS AppConfig which makes rolling configuration updates out easier.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sample-helper-aws-appconfig) ![PyPI version](https://badge.fury.io/py/sample-helper-aws-appconfig.svg) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

* Configurable update interval: you can ask the library to update your configuration as often as needed, but it will only call the AWS AppConfig API at the configured interval (in seconds).
* Handles correct API usage: the library uses the new AppConfig Data API and handles tracking the next configuration token and poll interval for you.
* Flexible: Can automatically fetch the current configuration on initialisation, every time the configuration is read by your code, or on demand. You can override the caching interval if needed.
* Handles YAML, JSON and plain text configurations, stored in any supported AppConfig store. Any other content type is returned unprocessed as the Python `bytes` type.
* Supports AWS Lambda, Amazon EC2 instances and on-premises use.

## Installation

```bash
pip install sample-helper-aws-appconfig
```

## Example

```python
from appconfig_helper import AppConfigHelper
from fastapi import FastAPI

appconfig = AppConfigHelper(
    "MyAppConfigApp",
    "MyAppConfigEnvironment",
    "MyAppConfigProfile",
    45  # minimum interval between update checks
)

app = FastAPI()

@app.get("/some-url")
def index():
    if appconfig.update_config():
        print("New configuration received")
    # your configuration is available in the "config" attribute
    return {
        "config_info": appconfig.config
    }
```

## Usage

Please see the [AWS AppConfig documentation](https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html) for details on configuring the service.

### Initialising

Start by creating an `AppConfigHelper` object. You must specify the application name, environment name, and profile (configuration) name. You must also specify the refresh interval, in seconds. AppConfigHelper will not attempt to fetch a new configuration version from the AWS AppConfig service more frequently than this interval. You should set it low enough that your code will receive new configuration promptly, but not so low that it takes too long. The library enforces a minimum interval of 15 seconds.

The configuration is not automatically fetched unless you set `fetch_on_init`. To have the library fetch the configuration when it is accessed, if it has been more than `max_config_age` seconds since the last fetch, set `fetch_on_read`.

If you need to customise the AWS credentials or region, set `session` to a configured `boto3.Session` object. Otherwise, the [standard boto3 logic](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html) for credential/configuration discovery is used.

### Reading the configuration

The configuration from AWS AppConfig is available as the `config` property. Before accessing it, you should call `update_config()`, unless you specified fetch_on_init or fetch_on_read during initialisation. If you want to force a config fetch, even if the number of seconds specified have not yet passed, call `update_config(True)`.

`update_config()` returns `True` if a new version of the configuration was received. If no attempt was made to fetch it, or the configuration received was the same as current one, it returns `False`. It will raise `ValueError` if the received configuration data could not be processed (e.g. invalid JSON). If needed, the inner exception for JSON or YAML parsing is available as `__context__` on the raised exception.

To read the values in your configuration, access the `config` property. For JSON and YAML configurations, this will contain the structure of your data. For plain text configurations, this will be a simple string.

The original data received from AppConfig is available in the `raw_config` property. Accessing this property will not trigger an automatic update even if `fetch_on_read` is True. The content type field received from AppConfig is available in the `content_type` property.

For example, with the following JSON in your AppConfig configuration profile:

```json
{
    "hello": "world",
    "data": {
        "is_sample": true
    }
}
```

you would see the following when using the library:

```python
# appconfig is the instance of the library
>>> appconfig.config["hello"]
"world"
>>> appconfig.config["data"]
{'is_sample': True}
```

### Use in AWS Lambda

AWS AppConfig is best used in Lambda by taking advantage of [Lambda Extensions](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-integration-lambda-extensions.html)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## Licence

This library is licensed under Apache-2.0. See the LICENSE file.
