import logging
import os
import secrets
import subprocess
from datetime import datetime, timedelta

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("micro-auth")


class KeyRequest(BaseModel):
    username: str
    expiry_days: int = 30


class ServiceAccountResponse(BaseModel):
    access_key: str
    secret_key: str


class AccessKeyAndExpiry(BaseModel):
    access_key: str
    expiry: str


class ServiceAccountListResponse(BaseModel):
    service_accounts: list[AccessKeyAndExpiry]


@router.post("/auth/minio/sa/")
async def create_service_account(key_request: KeyRequest, response: Response) -> ServiceAccountResponse:
    try:
        # mc admin user add myminio newuser newusersecret
        print(f"Creating user for {key_request.username}")
        result = subprocess.run(
            ["mc", "admin", "user", "add", "hydroshare", key_request.username, secrets.token_urlsafe(16)],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Creating Service Account for {key_request.username}")
        expiry_date = (datetime.now() + timedelta(days=key_request.expiry_days)).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["mc", "admin", "user", "svcacct", "add", "hydroshare", key_request.username, "--expiry", expiry_date],
            check=True,
            capture_output=True,
            text=True,
        )
        output = result.stdout
    except Exception as e:
        logger.error(f"CLI command failed with error: {e.stderr}")
        raise e
    access_key = output.split("Access Key: ")[1].split("\n")[0]
    secret_key = output.split("Secret Key: ")[1].split("\n")[0]
    response.status_code = status.HTTP_201_CREATED
    return ServiceAccountResponse(access_key=access_key, secret_key=secret_key)


@router.get("/auth/minio/sa/{username}")
async def get_service_accounts(username: str) -> ServiceAccountListResponse:
    try:
        result = subprocess.run(
            ["mc", "admin", "user", "svcacct", "list", "hydroshare", username],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        logger.error(f"CLI command failed with error: {e.stderr}")
        raise e
    lines = result.stdout.splitlines()[1:]  # Skip the header line
    service_accounts = []
    for line in lines:
        parts = line.split("|")
        service_account = {"access_key": parts[0].strip(), "expiry": parts[1].strip()}
        service_accounts.append(service_account)
    return {"service_accounts": service_accounts}


@router.delete("/auth/minio/sa/{service_account_key}")
async def delete_service_account(service_account_key: str, response: Response):
    try:
        print(f"Deleting Service Account {service_account_key}")
        subprocess.run(
            ["mc", "admin", "user", "svcacct", "remove", "hydroshare", service_account_key],
            check=True,
            capture_output=True,
            text=True,
        )
        print("Service Account deleted successfully")
        response.status_code = status.HTTP_204_NO_CONTENT
    except Exception as e:
        logger.error(f"CLI command failed with error: {e.stderr}")
        raise e


# TODO: This is not ready for prime time yet, needs more testing
@router.post("/auth/minio/sa/argo/")
async def save_access_key_argo(key_request: KeyRequest):
    service_account = await create_service_account(key_request)
    secret_name = f"{key_request.username}-credentials"
    try:
        result = subprocess.run(
            [
                "kubectl",
                "create",
                "secret",
                "generic",
                secret_name,
                "--namespace",
                "workflows",
                f"--from-literal=access_key={service_account.access_key}",
                f"--from-literal=secret_key={service_account.secret_key}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"CLI command failed with error: {e.stderr}")
        raise e
