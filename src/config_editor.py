from cmath import log
import configparser
from pathlib import Path

from loguru import logger

from constants import AWS_SESSION_TOKEN, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY


class ConfigEditor:
    config_name: str
    config_response: any

    def __init__(self, config_name: str, config_response) -> None:
        """This class highly depend on aws_client"""
        self.config_name = config_name
        self.config_response = config_response

    def edit(self) -> None:
        """
        edit ~/.aws/credentials config file using session config response
        which get using aws_client
        """
        config = configparser.ConfigParser()
        config_path = f"{Path.home()}/.aws/credentials"
        config.read(config_path)

        if self.config_name in config.sections():
            logger.info(
                f"next job will overwrite exist config data. section [{self.config_name}]"
            )

        config[self.config_name][AWS_ACCESS_KEY_ID] = self.config_response[
            AWS_ACCESS_KEY_ID
        ]
        config[self.config_name][AWS_SECRET_ACCESS_KEY] = self.config_response[
            AWS_SECRET_ACCESS_KEY
        ]
        config[self.config_name][AWS_SESSION_TOKEN] = self.config_response[
            AWS_SESSION_TOKEN
        ]

        try:
            config_file = open(config_path, "w")
            config.write(config_file)
        except Exception as err:
            logger.error(f"failed write config to {config_path}")
            raise err
        else:
            logger.info(f"succeed write config file to {config_path}")
