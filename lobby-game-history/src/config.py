import os
from dataclasses import dataclass

import yaml
from dataclass_wizard import YAMLWizard

@dataclass
class Account:
    nick: str
    password: str
    email: str

@dataclass
class LobbyConfig:
    host: str
    port: int

@dataclass
class LobbyAPIConfig:
    request_timeout: int

@dataclass
class Config(YAMLWizard):
    lobby: LobbyConfig
    lobby_api_client: LobbyAPIConfig
    accounts: list[Account]


def load_config():
    cfg_file = os.getenv("H3_CFG_FILE", "config.yml")
    return Config.from_yaml_file(cfg_file)


config: Config = load_config()
