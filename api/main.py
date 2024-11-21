import asyncio
import logging
import os
import subprocess
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from api.routers.access_control_changed import router as access_control_changed_router
from api.routers.minio import router as minio_router
from api.routers.service_accounts import router as service_accounts_router

logger = logging.getLogger("micro-auth")


@asynccontextmanager
async def initialize_mc(app: FastAPI):
    api_endpoint = os.environ.get("S3_API_ENDPOINT")
    access_key = os.environ.get("S3_ACCESS_KEY")
    secret_key = os.environ.get("S3_SECRET_KEY")
    if api_endpoint and access_key and secret_key:
        try:
            result = subprocess.run(
                ["mc", "config", "host", "add", "cuahsi-admin", api_endpoint, access_key, secret_key],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"CLI command failed with error: {e.stderr}")
            raise e
    yield
    # cleanup


app = FastAPI(lifespan=initialize_mc)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(minio_router, tags=["HS S3 Authorization"], prefix="/minio")
app.include_router(service_accounts_router, tags=["Service Account Management"], prefix="/sa")
app.include_router(access_control_changed_router, tags=["Access Control Webhook"], prefix="/access")

openapi_schema = get_openapi(
    title="S3 Authorization API",
    version="1.0",
    description="Authorization and Service Account Management for HydroShare on S3",
    routes=app.routes,
)
app.openapi_schema = openapi_schema


class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame) -> None:
        return super().handle_exit(sig, frame)


async def main():
    """Run FastAPI"""

    server = Server(
        config=uvicorn.Config(app, workers=1, loop="asyncio", host="0.0.0.0", port=80, forwarded_allow_ips="*")
    )
    api = asyncio.create_task(server.serve())

    await asyncio.wait([api])


if __name__ == "__main__":
    asyncio.run(main())
