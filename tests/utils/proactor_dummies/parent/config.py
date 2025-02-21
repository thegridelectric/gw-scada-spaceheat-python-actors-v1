from typing import Any, Optional

from pydantic import validator

from proactor import ProactorSettings
from proactor.config import MQTTClient
from proactor.config import Paths
from proactor.config import LoggingSettings
from tests.utils.proactor_dummies.names import DUMMY_PARENT_ENV_PREFIX


class DummyParentSettings(ProactorSettings):
    child_mqtt: MQTTClient = MQTTClient()

    class Config(ProactorSettings.Config):
        env_prefix = DUMMY_PARENT_ENV_PREFIX

    @validator("logging", always=True)
    def get_logging(cls, v: Optional[LoggingSettings], values: dict[str, Any]) -> LoggingSettings:
        if v is None:
            v = LoggingSettings()
        if not isinstance(values["paths"], Paths):
            raise ValueError(f"ERROR. 'paths' value has type {type(values['paths'])}, not Paths")
        paths: Paths = values["paths"]
        v.base_log_name = str(paths.name)
        v.file_handler.filename = "atn.log"
        return v
