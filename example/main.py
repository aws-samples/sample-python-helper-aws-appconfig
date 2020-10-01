import os

from fastapi import FastAPI

from appconfig_helper import AppConfigHelper

app = FastAPI()

# initialise the AppConfigHelper object
# this is done outside the lambda_handler so it is done when the Lambda container is started
# rather than on every request
appconfig = AppConfigHelper(
    os.environ.get("AppConfigApp", "DemoApp"),
    os.environ.get("AppConfigEnvironment", "prod"),
    os.environ.get("AppConfigProfile", "main"),
    15,
)


@app.get("/process-string/{input_string}")
def index(input_string):
    if appconfig.update_config():
        print("Received new configuration")
    output_string = input_string
    print(appconfig.config)
    if appconfig.config.get("transform_reverse", True):
        output_string = "".join(reversed(output_string))
    if appconfig.config.get("transform_allcaps", False):
        output_string = output_string.upper()

    return {
        "output": output_string,
    }
