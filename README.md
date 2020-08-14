# AWS AppConfig Helper

A helper library for AWS AppConfig which makes rolling configuration updates out easier.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aws-appconfig-helper) ![PyPI version](https://badge.fury.io/py/aws-appconfig-helper.svg) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

* Configurable update interval: you can ask the library to update your configuration as often as needed, but it will only call the AWS AppConfig API at the configured interval.
* Uses best practices for updates: the API is called with the version of the last received configuration, which results in a lower charge for the API call if no new configuration has been deployed. Automatically generates a client ID if you do not specify one.
* Flexible: Can automatically fetch the current configuration on initialisation, every time the configuration is read by your code, or on demand. You can override the caching interval if needed.
* Handles YAML, JSON and plain text configurations, stored in any supported AppConfig store.
* Supports AWS Lambda, Amazon EC2 instances and on-premises use

## Installation

```bash
pip install aws-appconfig-helper
```

## Example

```python
from appconfig_helper import AppConfigHelper

appconfig = AppConfigHelper(
    "MyAppConfigApp",
    "MyAppConfigEnvironment",
    "MyAppConfigProfile",
    30
)

def lambda_handler(event, context):
    if appconfig.update_config():
        print("New configuration received")
    return {
        "statusCode": 200,
        "body": appconfig.config
    }
```

## Usage

Please see the [AWS AppConfig documentation](https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html) for details on configuring the service.

### Initialising

Start by creating an `AppConfigHelper` object. You must specify the application name, environment name, and profile (configuration) name. You must also specify the refresh interval, in seconds. AppConfigHelper will not attempt to fetch a new configuration version from the AWS AppConfig service more frequently than this interval. You should set it low enough that your code will receive new configuration promptly, but not so low that it takes too long.

The configuration is not automatically fetched unless you set `fetch_on_init`. To have the library fetch the configuration when it is accessed, if it has been more than `max_config_age` seconds since the last fetch, set `fetch_on_read`.

If you need to customise the AWS credentials or region, set `session` to configured `boto3.Session` object. Otherwise, the standard boto3 logic for credential/configuration discovery is used.

AWS AppConfig needs clients to specify a unique client ID to allow deployment strategies to work correctly. The library will automatically use the hostname, but you can override it with `client_id`.

### Reading the configuration

The configuration from AWS AppConfig is available as the `config` property. Before accessing it, you should call `update_config()`, unless you specified fetch_on_init or fetch_on_read during initialisation. If you want to force a config fetch, even if the number of seconds specified have not yet passed, call `update_config(True)`.

`update_config()` returns `True` if a new version of the configuration was received. If no attempt was made to fetch it, or the configuration received was the same as current one, it returns `False`. It will raise `ValueError` if the received configuration data could not be processed (e.g. invalid JSON, unknown type). If needed, the inner exception for JSON or YAML parsing is available as `__context__` on the raised exception.

To read the values in your configuration, access the `config` property. For JSON and YAML configurations, this will contain the structure of your data. For plain text configurations, this will be a simple string.

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

You can check which version of the configuration was last received by examining the `config_version` property. Note that this value is opaque and depends on the service being used to store the configuration data. For example, if Amazon S3 is being used, then the version will be the version identifier of the object, not an integer.

### Creating a Lambda layer

To create a Lambda layer containing the library, follow these steps:

1. In a temporary directory, `mkdir python`
1. Install the library in the python directory: `pip install -t python aws-appconfig-helper`
1. Create a zip file containing the installed library: `zip -r layer.zip python`
1. Upload the zip file as a Lambda layer (e.g. via the AWS Console)

You can now specify the layer in your function configuration to have it included.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## Licence

This library is licensed under Apache-2.0. See the LICENSE file.
