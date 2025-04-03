import logging
import subprocess
import secrets

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("micro-auth")


class KeyRequest(BaseModel):
    username: str


class ServiceAccountResponse(BaseModel):
    access_key: str
    secret_key: str


@router.post("/auth/minio/sa/")
async def create_service_account(key_request: KeyRequest) -> ServiceAccountResponse:
    try:
        # mc admin user add myminio newuser newusersecret
        print(f"Creating user for {key_request.username}")
        result = subprocess.run(
            ["mc", "admin", "user", "add", "cuahsi-admin", key_request.username, secrets.token_urlsafe(16)],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Creating Service Account for {key_request.username}")
        result = subprocess.run(
            ["mc", "admin", "user", "svcacct", "add", "cuahsi-admin", key_request.username],
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
    return ServiceAccountResponse(access_key=access_key, secret_key=secret_key)


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
