from lib2to3.pgen2 import token
import click
from dotenv import dotenv_values
from loguru import logger


from aws_client import AWSClient
from config_editor import ConfigEditor

config = {"aws_mfa_arn": "", "aws_token_code": "", "config_name": ""}


def read_local_env():
    global config

    config["aws_mfa_arn"] = dotenv_values(".env")["AWS_MFA_ARN"]
    logger.debug(f'read local mfa arn : {config["aws_mfa_arn"]}')
    config["config_name"] = dotenv_values(".env")["CONFIG_NAME"]


def get_session_configuration():
    """get response using default config profile"""
    aws_client = AWSClient(
        mfa_arn=config["aws_mfa_arn"], token_code=config["aws_token_code"]
    )
    return aws_client.request_session_token()


def edit_config_file(config_response):
    """editing config using parsed session response"""
    config_editor = ConfigEditor(config["config_name"], config_response)
    config_editor.edit()


@click.command()
@click.option(
    "--token-code",
    prompt="MFA token code",
    help="check token code from your own authenticator",
)
def main(token_code: str) -> None:
    global config

    if not isinstance(token_code, str):
        token_code = str(token_code)
    config["aws_token_code"] = token_code

    config_response = get_session_configuration()
    edit_config_file(config_response)


if __name__ == "__main__":
    read_local_env()
    main()
