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

## usage

```shell
python3 ./src/main.py

# or manually add property

python3 ./src/main.py --token-code <your-auth-token>
```
