import logging
from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("micro-auth")


class AccessLevel(Enum):
    VIEW = "VIEW"
    EDIT = "EDIT"
    NONE = "NONE"


class User(BaseModel):
    username: str
    access: AccessLevel
    is_superuser: bool


class Resource(BaseModel):
    id: str
    public: bool
    allow_private_sharing: bool
    discoverable: bool
    user_access: list[User]


class AccessControlChangeRequest(BaseModel):
    resources: list[Resource]


@router.post("/user/resource/")
async def save_access_key_argo(key_request: AccessControlChangeRequest):
    print(f"Changing access control for {key_request.resources}")
