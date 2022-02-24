from __future__ import annotations
from typing import TYPE_CHECKING

import boto3
from loguru import logger

from constants import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN

if TYPE_CHECKING:
    from mypy_boto3_output.mypy_boto3_sts_package.mypy_boto3_sts import STSClient
    from mypy_boto3_output.mypy_boto3_sts_package.mypy_boto3_sts.type_defs import (
        GetSessionTokenResponseTypeDef,
    )


class AWSClient:
    """AWS client for sts authentication"""

    client: STSClient
    response: GetSessionTokenResponseTypeDef

    ONE_HOUR = 3600
    # 15 mins
    MINIMUM_DURATION = 900
    MAXIMUM_DURAION = ONE_HOUR * 36

    def __init__(self, mfa_arn: str, token_code: str) -> None:
        self.client = boto3.client("sts")
        self.mfa_arn = mfa_arn
        self.token_code = token_code
        self.current_duration = self.MAXIMUM_DURAION

    def request_session_token(self):
        """request session config using aws sts client"""
        logger.info(
            f"set current duration about {self.current_duration/self.ONE_HOUR} hour."
        )

        try:
            self.response = self.client.get_session_token(
                DurationSeconds=self.MAXIMUM_DURAION,
                SerialNumber=self.mfa_arn,
                TokenCode=self.token_code,
            )
        except Exception as err:
            # TODO error is not specified
            logger.error("failed get response using sts client.")
            raise err
        else:
            logger.debug(f"get response {self.response}")
            return self.parse_response()

    def parse_response(self):
        """parsing config from response and return its values"""
        credentials = self.response["Credentials"]

        expiration = credentials["Expiration"]
        logger.debug(f"this session expired at {expiration}")

        return {
            AWS_ACCESS_KEY_ID: credentials["AccessKeyId"],
            AWS_SECRET_ACCESS_KEY: credentials["SecretAccessKey"],
            AWS_SESSION_TOKEN: credentials["SessionToken"],
        }
