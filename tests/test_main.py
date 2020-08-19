# type: ignore

import io
import json
import socket

import boto3
import botocore
import botocore.exceptions
import botocore.session
import pytest
import yaml
from appconfig_helper import AppConfigHelper
from botocore.response import StreamingBody
from botocore.stub import Stubber
from freezegun import freeze_time


@pytest.fixture(autouse=True)
def appconfig_stub():
    session = botocore.session.get_session()
    client = session.create_client("appconfig", region_name="us-east-1")
    with Stubber(client) as stubber:
        yield (client, stubber, session)
        stubber.assert_no_pending_responses()


@pytest.fixture(autouse=True)
def appconfig_stub_ignore_pendng():
    session = botocore.session.get_session()
    client = session.create_client("appconfig", region_name="us-east-1")
    with Stubber(client) as stubber:
        yield (client, stubber, session)


def _build_request(
    app="AppConfig-App",
    env="AppConfig-Env",
    profile="AppConfig-Profile",
    client_id=None,
    version="null",
):
    if client_id is None:
        client_id = socket.gethostname()
    return {
        "Application": app,
        "ClientConfigurationVersion": str(version),
        "ClientId": client_id,
        "Configuration": profile,
        "Environment": env,
    }


def _build_response(content, version, content_type):
    if content_type == "application/json":
        content_text = json.dumps(content).encode("utf-8")
    elif content_type == "application/x-yaml":
        content_text = str(yaml.dump(content)).encode("utf-8")
    else:
        content_text = content.encode("utf-8")
    return {
        "Content": StreamingBody(io.BytesIO(bytes(content_text)), len(content_text)),
        "ConfigurationVersion": version,
        "ContentType": content_type,
    }


def test_appconfig_init(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)

    assert isinstance(a, AppConfigHelper)
    assert a.appconfig_application == "AppConfig-App"
    assert a.appconfig_environment == "AppConfig-Env"
    assert a.appconfig_profile == "AppConfig-Profile"
    assert a.config is None
    assert a.config_version == "null"
    assert a._last_update_time == 0.0


def test_appconfig_update(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response("hello", "1", "text/plain"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"
    assert a.config_version == "1"


def test_appconfig_update_interval(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response("hello", "1", "text/plain"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"
    assert a.config_version == "1"

    result = a.update_config()
    assert not result
    assert a.config == "hello"
    assert a.config_version == "1"


def test_appconfig_force_update_same(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response("hello", "1", "text/plain"),
        _build_request(),
    )
    stub.add_response(
        "get_configuration",
        _build_response("", "1", "text/plain"),
        _build_request(version="1"),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"
    assert a.config_version == "1"

    result = a.update_config(force_update=True)
    assert not result
    assert a.config == "hello"
    assert a.config_version == "1"


def test_appconfig_force_update_new(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response("hello", "1", "text/plain"),
        _build_request(),
    )
    stub.add_response(
        "get_configuration",
        _build_response("world", "2", "text/plain"),
        _build_request(version="1"),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"
    assert a.config_version == "1"

    result = a.update_config(force_update=True)
    assert result
    assert a.config == "world"
    assert a.config_version == "2"


def test_appconfig_fetch_on_init(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response("hello", "1", "text/plain"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper(
        "AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15, fetch_on_init=True
    )
    assert a.config == "hello"
    assert a.config_version == "1"


@freeze_time("2020-08-01 12:00:00", auto_tick_seconds=20)
def test_appconfig_fetch_on_read(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response("hello", "1", "text/plain"),
        _build_request(),
    )
    stub.add_response(
        "get_configuration",
        _build_response("world", "2", "text/plain"),
        _build_request(version="1"),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper(
        "AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15, fetch_on_read=True
    )
    assert a.config == "hello"
    assert a.config_version == "1"
    assert a.config == "world"
    assert a.config_version == "2"


@freeze_time("2020-08-01 12:00:00", auto_tick_seconds=10)
def test_appconfig_fetch_interval(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response("hello", "1", "text/plain"),
        _build_request(),
    )
    stub.add_response(
        "get_configuration",
        _build_response("world", "2", "text/plain"),
        _build_request(version="1"),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"
    assert a.config_version == "1"

    result = a.update_config()
    assert not result
    assert a.config == "hello"
    assert a.config_version == "1"

    result = a.update_config()
    assert result
    assert a.config == "world"
    assert a.config_version == "2"


def test_appconfig_yaml(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response({"hello": "world"}, "1", "application/x-yaml"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    a.update_config()
    assert a.config == {"hello": "world"}
    assert a.config_version == "1"


def test_appconfig_json(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response({"hello": "world"}, "1", "application/json"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    a.update_config()
    assert a.config == {"hello": "world"}
    assert a.config_version == "1"


def test_appconfig_client(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response({"hello": "world"}, "1", "application/json"),
        _build_request(client_id="hello"),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper(
        "AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15, client_id="hello",
    )
    a.update_config()


def test_appconfig_session(appconfig_stub, mocker):
    client, stub, session = appconfig_stub
    stub.add_response(
        "get_configuration",
        _build_response({"hello": "world"}, "1", "application/json"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    mocker.patch.object(boto3.Session, "client", return_value=client)
    a = AppConfigHelper(
        "AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15, session=session
    )
    a.update_config()


def test_bad_json(appconfig_stub, mocker):
    client, stub, session = appconfig_stub
    content_text = """{"broken": "json",}""".encode("utf-8")
    stub.add_response(
        "get_configuration",
        {
            "Content": StreamingBody(
                io.BytesIO(bytes(content_text)), len(content_text)
            ),
            "ConfigurationVersion": "1",
            "ContentType": "application/json",
        },
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    with pytest.raises(ValueError):
        a.update_config()


def test_bad_yaml(appconfig_stub, mocker):
    client, stub, session = appconfig_stub
    content_text = """
    broken:
        - yaml
    - content
    """.encode(
        "utf-8"
    )
    stub.add_response(
        "get_configuration",
        {
            "Content": StreamingBody(
                io.BytesIO(bytes(content_text)), len(content_text)
            ),
            "ConfigurationVersion": "1",
            "ContentType": "application/x-yaml",
        },
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    with pytest.raises(ValueError):
        a.update_config()


def test_bad_content_type(appconfig_stub, mocker):
    client, stub, session = appconfig_stub
    content_text = """hello world""".encode("utf-8")
    stub.add_response(
        "get_configuration",
        {
            "Content": StreamingBody(
                io.BytesIO(bytes(content_text)), len(content_text)
            ),
            "ConfigurationVersion": "1",
            "ContentType": "image/jpeg",
        },
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    with pytest.raises(ValueError):
        a.update_config()


def test_bad_request(appconfig_stub_ignore_pendng, mocker):
    client, stub, session = appconfig_stub_ignore_pendng
    content_text = """hello world""".encode("utf-8")
    stub.add_response(
        "get_configuration",
        {
            "Content": StreamingBody(
                io.BytesIO(bytes(content_text)), len(content_text)
            ),
            "ConfigurationVersion": "1",
            "ContentType": "image/jpeg",
        },
        _build_request("", "", ""),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    with pytest.raises(botocore.exceptions.ParamValidationError):
        a = AppConfigHelper("", "", "", 15)
        a.update_config()


def test_bad_interval(appconfig_stub, mocker):
    client, stub, session = appconfig_stub
    mocker.patch.object(boto3, "client", return_value=client)
    with pytest.raises(ValueError):
        _ = AppConfigHelper("Any", "Any", "Any", 10)
