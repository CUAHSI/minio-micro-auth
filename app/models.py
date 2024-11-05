import logging
from typing import AnyStr, List, Optional

from pydantic import BaseModel

logger = logging.getLogger("micro-auth")


class Conditions(BaseModel):
    preferred_username: Optional[List[AnyStr]] = []
    username: Optional[List[AnyStr]] = []
    Prefix: Optional[List[AnyStr]] = []
    prefix: Optional[List[AnyStr]] = []

    @property
    def users(self):
        if self.preferred_username:
            return self.preferred_username
        else:
            return self.username

    @property
    def user(self):
        users = self.users
        if len(users) != 1:
            logger.warning(f"Exactly one user must be specified {users}")
            raise ValueError("Exactly one user must be specified")
        return self.users[0]

    @property
    def prefixes(self):
        if self.Prefix:
            return [prefix for prefix in self.Prefix if prefix]
        elif self.prefix:
            return [prefix for prefix in self.prefix if prefix]
        else:
            return []


class Input(BaseModel):
    conditions: Conditions
    # https://min.io/docs/minio/linux/administration/identity-access-management/policy-based-access-control.html
    action: Optional[AnyStr] = None
    bucket: AnyStr


class AuthRequest(BaseModel):
    input: Input
