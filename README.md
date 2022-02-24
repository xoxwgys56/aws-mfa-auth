# AWS MFA auth

## setup

1. create environment using below command

```shell
pipenv shell
pipenv install

# for typing
pip3 install -e ./mypy_boto3_output/mypy_boto3_sts_package
```

2. create your own `.env` file using [`.env.template`](./.env.template)
3. check you have own credentials on `~/.aws/credentials` like below:

```s
[default]
aws_access_key_id = <your-aws-access-key-id>
aws_secret_access_key = <your-aws-secret-access-key>
```

## usage

```shell
python3 ./src/main.py

# or manually add property

python3 ./src/main.py --token-code <your-auth-token>
```
