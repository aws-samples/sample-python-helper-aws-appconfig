"""
Example application for AppConfigHelper

Create the required AppConfig resources with the CloudFormation template.

Run this file with `uvicorn main:app`
"""

from fastapi import FastAPI

from appconfig_helper import AppConfigHelper

app = FastAPI()

appconfig = AppConfigHelper(
    "DemoApp",
    "prod",
    "main",
    15,
)


@app.get("/process-string/{input_string}")
def index(input_string):
    if appconfig.update_config():
        print("Received new configuration")
    output_string = input_string
    if appconfig.config.get("transform_reverse", True):
        output_string = "".join(reversed(output_string))
    if appconfig.config.get("transform_allcaps", False):
        output_string = output_string.upper()

    return {
        "output": output_string,
    }
