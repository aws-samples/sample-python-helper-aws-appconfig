# type: ignore

import io
import json

import boto3
import botocore
import botocore.exceptions
import botocore.session
import pytest
import yaml
from botocore.response import StreamingBody
from botocore.stub import Stubber
from freezegun import freeze_time

from appconfig_helper import AppConfigHelper


@pytest.fixture(autouse=True)
def appconfig_stub():
    session = botocore.session.get_session()
    client = session.create_client("appconfigdata", region_name="us-east-1")
    with Stubber(client) as stubber:
        yield (client, stubber, session)
        stubber.assert_no_pending_responses()


@pytest.fixture(autouse=True)
def appconfig_stub_ignore_pending():
    session = botocore.session.get_session()
    client = session.create_client("appconfigdata", region_name="us-east-1")
    with Stubber(client) as stubber:
        yield (client, stubber, session)


def _build_request(next_token="token1234"):
    return {"ConfigurationToken": next_token}


def _build_response(content, content_type, next_token="token5678", poll=30):
    if content_type == "application/json":
        content_text = json.dumps(content).encode("utf-8")
    elif content_type == "application/x-yaml":
        content_text = str(yaml.dump(content)).encode("utf-8")
    else:
        content_text = content.encode("utf-8")
    return {
        "Configuration": StreamingBody(
            io.BytesIO(bytes(content_text)), len(content_text)
        ),
        "ContentType": content_type,
        "NextPollConfigurationToken": next_token,
        "NextPollIntervalInSeconds": poll,
    }


def _add_start_stub(
    stub,
    app_id="AppConfig-App",
    config_id="AppConfig-Profile",
    env_id="AppConfig-Env",
    poll=15,
    next_token="token1234",
):
    stub.add_response(
        "start_configuration_session",
        {"InitialConfigurationToken": next_token},
        {
            "ApplicationIdentifier": app_id,
            "ConfigurationProfileIdentifier": config_id,
            "EnvironmentIdentifier": env_id,
            "RequiredMinimumPollIntervalInSeconds": poll,
        },
    )


def test_appconfig_init(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)

    assert isinstance(a, AppConfigHelper)
    assert a.appconfig_application == "AppConfig-App"
    assert a.appconfig_environment == "AppConfig-Env"
    assert a.appconfig_profile == "AppConfig-Profile"
    assert a.config is None
    assert a._last_update_time == 0.0
    assert a.raw_config is None
    assert a.content_type is None
    assert a._poll_interval == 15
    assert a._next_config_token is None


def test_appconfig_update(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response("hello", "text/plain"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"
    assert a.raw_config == b"hello"
    assert a.content_type == "text/plain"
    assert a._next_config_token == "token5678"
    assert a._poll_interval == 30


def test_appconfig_update_interval(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response("hello", "text/plain"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"
    assert a._next_config_token == "token5678"
    assert a._poll_interval == 30

    result = a.update_config()
    assert not result
    assert a.config == "hello"
    assert a._next_config_token == "token5678"


def test_appconfig_force_update_same(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response("hello", "text/plain"),
        _build_request(),
    )
    stub.add_response(
        "get_latest_configuration",
        _build_response("", "text/plain"),
        _build_request(next_token="token5678"),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"
    assert a.raw_config == b"hello"
    assert a.content_type == "text/plain"
    assert a._next_config_token == "token5678"
    assert a._poll_interval == 30

    result = a.update_config(force_update=True)
    assert not result
    assert a.config == "hello"
    assert a.raw_config == b"hello"
    assert a.content_type == "text/plain"
    assert a._next_config_token == "token5678"
    assert a._poll_interval == 30


def test_appconfig_force_update_new(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response("hello", "text/plain"),
        _build_request(),
    )
    stub.add_response(
        "get_latest_configuration",
        _build_response("world", "text/plain", next_token="token9012"),
        _build_request(next_token="token5678"),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"
    assert a.raw_config == b"hello"
    assert a.content_type == "text/plain"
    assert a._next_config_token == "token5678"
    assert a._poll_interval == 30

    result = a.update_config(force_update=True)
    assert result
    assert a.config == "world"
    assert a.raw_config == b"world"
    assert a.content_type == "text/plain"
    assert a._next_config_token == "token9012"
    assert a._poll_interval == 30


def test_appconfig_fetch_on_init(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response("hello", "text/plain"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper(
        "AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15, fetch_on_init=True
    )
    assert a.config == "hello"


@freeze_time("2020-08-01 12:00:00", auto_tick_seconds=20)
def test_appconfig_fetch_on_read(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response("hello", "text/plain", poll=15),
        _build_request(),
    )
    stub.add_response(
        "get_latest_configuration",
        _build_response("world", "text/plain", next_token="token9012"),
        _build_request(next_token="token5678"),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper(
        "AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15, fetch_on_read=True
    )
    assert a.config == "hello"
    assert a._next_config_token == "token5678"
    assert a.config == "world"
    assert a._next_config_token == "token9012"


@freeze_time("2020-08-01 12:00:00", auto_tick_seconds=10)
def test_appconfig_fetch_interval(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response("hello", "text/plain", poll=15),
        _build_request(),
    )
    stub.add_response(
        "get_latest_configuration",
        _build_response("world", "text/plain", poll=15, next_token="token1234"),
        _build_request(next_token="token5678"),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    result = a.update_config()
    assert result
    assert a.config == "hello"

    result = a.update_config()
    assert not result
    assert a.config == "hello"

    result = a.update_config()
    assert result
    assert a.config == "world"
    assert a._next_config_token == "token1234"


def test_appconfig_yaml(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response({"hello": "world"}, "application/x-yaml"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    a.update_config()
    assert a.config == {"hello": "world"}
    assert a.content_type == "application/x-yaml"


def test_appconfig_json(appconfig_stub, mocker):
    client, stub, _ = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response({"hello": "world"}, "application/json"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    a.update_config()
    assert a.config == {"hello": "world"}
    assert a.content_type == "application/json"


def test_appconfig_session(appconfig_stub, mocker):
    client, stub, session = appconfig_stub
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response({"hello": "world"}, "application/json"),
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
    _add_start_stub(stub)
    broken_response = _build_response({}, "application/json")
    broken_response["Configuration"] = StreamingBody(
        io.BytesIO(bytes(content_text)), len(content_text)
    )
    stub.add_response(
        "get_latest_configuration",
        broken_response,
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
    _add_start_stub(stub)
    broken_response = _build_response({}, "application/x-yaml")
    broken_response["Configuration"] = StreamingBody(
        io.BytesIO(bytes(content_text)), len(content_text)
    )
    stub.add_response(
        "get_latest_configuration",
        broken_response,
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    with pytest.raises(ValueError):
        a.update_config()


def test_unknown_content_type(appconfig_stub, mocker):
    client, stub, session = appconfig_stub
    content_text = "hello world"
    _add_start_stub(stub)
    stub.add_response(
        "get_latest_configuration",
        _build_response(content_text, "image/jpeg"),
        _build_request(),
    )
    mocker.patch.object(boto3, "client", return_value=client)
    a = AppConfigHelper("AppConfig-App", "AppConfig-Env", "AppConfig-Profile", 15)
    a.update_config()
    assert a.config == b"hello world"
    assert a.content_type == "image/jpeg"
    assert a.raw_config == content_text.encode("utf-8")


def test_bad_request(appconfig_stub_ignore_pending, mocker):
    client, stub, session = appconfig_stub_ignore_pending
    content_text = "hello world"
    _add_start_stub(stub, "", "", "")
    stub.add_response(
        "get_latest_configuration",
        _build_response(content_text, "image/jpeg"),
        _build_request(),
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
