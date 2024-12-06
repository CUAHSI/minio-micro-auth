import logging
from typing import AnyStr, List, Optional

from database import is_superuser_and_id, resource_discoverablity, user_has_edit_access, user_has_view_access
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
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
    action: AnyStr
    bucket: AnyStr


class AuthRequest(BaseModel):
    input: Input


@router.post("/authorization/")
async def hs_s3_authorization_check(auth_request: AuthRequest):

    username = auth_request.input.conditions.user
    bucket = auth_request.input.bucket
    action = auth_request.input.action

    print(f"Checking {username} {bucket} {action}")

    if username == "cuahsi" or username == "minioadmin":
        # allow cuahsi admin account always
        return {"result": {"allow": True}}

    if auth_request.input.action in ["s3:GetBucketLocation"]:
        # This is needed by mc to list buckets and does not contain a prefix
        return {"result": {"allow": True}}

    user_is_superuser, user_id = is_superuser_and_id(username)
    if user_is_superuser:
        return {"result": {"allow": True}}

    # users access the objects in these buckets through presigned urls, admins are approved above
    if bucket in ["zips", "tmp", "bags"]:
        return {"result": {"allow": False}}

    # prefixes are paths to (folders/set of) objects in the bucket
    prefixes = auth_request.input.conditions.prefixes
    if not prefixes:
        return {"result": {"allow": False}}

    resource_ids = [prefix.split("/")[0] for prefix in prefixes]
    # check the user and each resource against the action
    for resource_id in resource_ids:
        if not _check_user_authorization(user_id, resource_id, action):
            print(f"Denied {username} {resource_id} {action}")
            return {"result": {"allow": False}}
        else:
            print(f"Approved {username} {resource_id} {action}")
    if resource_ids:
        return {"result": {"allow": True}}

    print(f"No resources found for {username} {prefixes}")
    return {"result": {"allow": False}}


def _check_user_authorization(user_id, resource_id, action, quota_holder_id):
    # Break this down into just view and edit for now.
    # HydroShare does not conusme changes made through S3 API yet so edit check is not active
    # Later on we could share the metadata files only or allow resource deletion.
    # We will also need to figure out owners at some point

    # List of actions https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html

    # view actions
    if action in ["s3:GetObject", "s3:ListObjects", "s3:ListObjjectsV2", "s3:ListBucket"]:
        public, allow_private_sharing, discoverable = resource_discoverablity(resource_id, quota_holder_id)

        if action == "s3:GetObject":
            return public or allow_private_sharing or user_has_view_access(user_id, resource_id, quota_holder_id)
        # view and discoverable actions
        if action == "s3:ListObjects" or action == "s3:ListObjjectsV2" or action == "s3:ListBucket":
            return (
                public
                or allow_private_sharing
                or discoverable
                or user_has_view_access(user_id, resource_id, quota_holder_id)
            )

    # edit actions
    if action in ["s3:PutObject", "s3:DeleteObject", "s3:DeleteObjects", "s3:UploadPart"]:
        return user_has_edit_access(user_id, resource_id, quota_holder_id)

    return False
