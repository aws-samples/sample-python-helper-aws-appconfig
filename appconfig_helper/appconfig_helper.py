"""
AppConfig Helper class
"""


import json
import socket
import time
from typing import Any, Dict, Optional, Union

import boto3

try:
    import yaml

    yaml_available = True
except ImportError:
    yaml_available = False


class AppConfigHelper:
    """
    AWS AppConfig Helper class.

    Helps you fetch configuration from AWS AppConfig easily. Parses JSON and
    YAML configurations into native Python dicts, and keeps plain text as
    str.

    `appconfig_application`, `appconfig_environment` and `appconfig_profile`
    are the names or IDs of the AWS AppConfig application, environment and
    profile (configuration) respectively.

    `max_config_age` is the minimum interval in seconds between attempts to
    update the configuration. Set it low enough that your application
    receives new configuration in good time, but not so high that you are
    unnecessarily polling the AWS AppConfig service. A minimum of 15 seconds
    is enforced to help avoid throttling.

    If you need to override credentials or AWS Region, set `session` to a
    preconfigured `boto3.Session` object.

    If `fetch_on_init` is set, attempt to fetch configuration when the
    instance is created.

    If `fetch_on_read` is set, every time the `config` property is read, the
    configuration will be refreshed (if it has been at least `max_config_age`
    seconds since the last refresh).

    Use `client_id` to override the default (the hostname).
    """

    def __init__(
        self,
        appconfig_application: str,
        appconfig_environment: str,
        appconfig_profile: str,
        max_config_age: int,
        *,
        session: Optional[boto3.Session] = None,
        fetch_on_init: bool = False,
        fetch_on_read: bool = False,
        client_id: Optional[str] = None,
    ) -> None:

        if isinstance(session, boto3.Session):
            self._client = session.client("appconfig")
        else:
            self._client = boto3.client("appconfig")
        self._appconfig_profile = appconfig_profile
        self._appconfig_environment = appconfig_environment
        self._appconfig_application = appconfig_application
        if max_config_age < 15:
            raise ValueError("max_config_age must be at least 15 seconds")
        self._max_config_age = max_config_age
        if client_id is None:
            self._client_id = socket.gethostname()
        else:
            self._client_id = client_id
        self._configuration_version = "null"  # type: str
        self._last_update_time = 0.0
        self._config = None  # type: Union[None, Dict[Any, Any], str, bytes]
        self._fetch_on_read = fetch_on_read
        if fetch_on_init:
            self.update_config()

    @property
    def appconfig_profile(self) -> str:
        """The profile in use."""
        return self._appconfig_profile

    @property
    def appconfig_environment(self) -> str:
        """The environment in use."""
        return self._appconfig_environment

    @property
    def appconfig_application(self) -> str:
        """The application in use."""
        return self._appconfig_application

    @property
    def config_version(self) -> str:
        """The configuration version last received."""
        return self._configuration_version

    @property
    def config(self) -> Union[None, Dict[Any, Any], str, bytes]:
        """The application configuration content.

        If initialsed with `fetch_on_read` = True, will attempt to update the
        config before returning it to you."""
        if self._fetch_on_read:
            self.update_config()
        return self._config

    def update_config(self, force_update: bool = False) -> bool:
        """Request the lastest configration.

        `force_update`: set to True to request configuration event if it's not time yet

        Returns True if a new version of configuration was received. False
        indicates that no attempt was made, or that no new version was found.
        """
        if (
            time.time() - self._last_update_time < self._max_config_age
        ) and not force_update:
            return False

        response = self._client.get_configuration(
            Application=self._appconfig_application,
            Environment=self._appconfig_environment,
            Configuration=self._appconfig_profile,
            ClientId=self._client_id,
            ClientConfigurationVersion=self._configuration_version,
        )

        if response["ConfigurationVersion"] == self._configuration_version:
            self._last_update_time = time.time()
            return False

        if response["ContentType"] == "application/x-yaml":
            if not yaml_available:
                raise RuntimeError(
                    "Configuration in YAML format received and missing yaml library; pip install pyyaml?"
                )
            try:
                self._config = yaml.safe_load(response["Content"])
            except yaml.YAMLError as error:
                message = "Unable to parse YAML configuration data"
                if hasattr(error, "problem_mark"):
                    message = message + " at line {} column {}".format(
                        error.problem_mark.line + 1, error.problem_mark.column + 1
                    )
                raise ValueError(message) from error
        elif response["ContentType"] == "application/json":
            try:
                self._config = json.loads(response["Content"].read().decode("utf-8"))
            except json.JSONDecodeError as error:
                raise ValueError(error.msg) from error
        elif response["ContentType"] == "text/plain":
            self._config = response["Content"].read().decode("utf-8")
        else:
            self._config = response["Content"].read()

        self._last_update_time = time.time()
        self._configuration_version = response["ConfigurationVersion"]
        return True
