import yaml

from typing import Dict, List

from pydantic import BaseModel


class GMAIL(BaseModel):
    SCOPES: List[str]


class CHATGPT(BaseModel):
    API_KEY: str


class DEEPSEEK(BaseModel):
    API_KEY: str


class ModelSettings(BaseModel):
    base_url: str
    model: str


class AssignmentSettings(BaseModel):
    assignment_number: str
    assignment_save_path: str
    deadline: str
    my_email: str
    my_name: str


class Config(BaseModel):
    GMAIL: GMAIL
    CHATGPT: CHATGPT
    DEEPSEEK: DEEPSEEK
    ModelSettings: ModelSettings
    AssignmentSettings: AssignmentSettings


def load_config():
    """Generate config from config file

    Returns:
        config (class): return config in class type
    """
    config_file_path = "./config/configs.yaml"

    with open(config_file_path, "r") as config_file:
        config_data: Dict = yaml.safe_load(config_file)
        # print(type(yaml.safe_load(config_file)))

    config = Config(**config_data)
    # print(config.Keys.BinanceKeys.APIkey)
    return config


if __name__ == "__main__":
    load_config()
