import logging
from typing import AnyStr, List, Optional

from database import is_superuser_and_id, resource_discoverablity, user_has_edit_access, user_has_view_access
from cache import (
    is_superuser_and_id_cache,
    resource_discoverability_cache,
    user_has_edit_access_cache,
    user_has_view_access_cache,
    backfill_superuser_and_id,
    backfill_resource_discoverability,
    backfill_view_access,
    backfill_edit_access,
)
from fastapi import APIRouter
from pydantic import BaseModel, Extra

router = APIRouter()
logger = logging.getLogger("micro-auth")


class AllowBaseModel(BaseModel, extra=Extra.allow):
    pass

class Conditions(AllowBaseModel):
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


class Input(AllowBaseModel):
    conditions: Conditions
    # https://min.io/docs/minio/linux/administration/identity-access-management/policy-based-access-control.html
    action: AnyStr
    bucket: AnyStr
    object: AnyStr


class AuthRequest(AllowBaseModel):
    input: Input


@router.post("/authorization/")
async def hs_s3_authorization_check(auth_request: AuthRequest):
    print(f"Received request: {auth_request.model_dump_json(indent=2)}")

    username = auth_request.input.conditions.user
    bucket = auth_request.input.bucket
    action = auth_request.input.action

    print(f"Checking {username} {bucket} {action}")

    if username == "cuahsi" or username == "minioadmin":
        # allow cuahsi admin account always
        print(f"Approved cuahsi and minioadmin {username} {bucket} {action}")
        return {"result": {"allow": True}}

    if auth_request.input.action in ["s3:GetBucketLocation", "s3:GetBucketObjectLockConfiguration"]:
        # This is needed by mc to list buckets and does not contain a prefix
        return {"result": {"allow": True}}

    try:
        print(f"Checking cache for {username}")
        user_is_superuser, user_id = is_superuser_and_id_cache(username)
    except:
        print(f"Checking db for {username}")
        user_is_superuser, user_id = is_superuser_and_id(username)
        logger.warning(f"Backfilling cache: {username}:(is_superuser:{user_is_superuser},user_id:{user_id})")
        backfill_superuser_and_id(username, user_is_superuser, user_id)
    if user_is_superuser:
        print(f"Approved superuser {username} {bucket} {action}")
        return {"result": {"allow": True}}

    # users access the objects in these buckets through presigned urls, admins are approved above
    if bucket in ["zips", "tmp", "bags"]:
        return {"result": {"allow": False}}

    # prefixes are paths to (folders/set of) objects in the bucket
    prefixes = auth_request.input.conditions.prefixes
    if not prefixes:
        if auth_request.input.object:
            # if there is an object but no prefix, it is a file in the root of the bucket
            print(f"No prefixes but object {username} {bucket} {action} {auth_request.input.object}")
            prefixes = [auth_request.input.object]
        else:
            print(f"Denied No prefixes {username} {bucket} {action}")
            return {"result": {"allow": False}}

    resource_ids = [prefix.split("/")[0] for prefix in prefixes]
    # check the user and each resource against the action
    for resource_id in resource_ids:
        print(f"Checking {username} {bucket} {resource_id} {action}")
        if not _check_user_authorization(user_id, resource_id, action):
            print(f"Denied {username} {resource_id} {action}")
            return {"result": {"allow": False}}
        else:
            print(f"Approved {username} {resource_id} {action}")
    if resource_ids:
        print(f"Approved {username} {bucket} {resource_ids} {action}")
        return {"result": {"allow": True}}

    print(f"No resources found for {username} {prefixes}")
    return {"result": {"allow": False}}


def _check_user_authorization(user_id, resource_id, action):
    # Break this down into just view and edit for now.
    # HydroShare does not conusme changes made through S3 API yet so edit check is not active
    # Later on we could share the metadata files only or allow resource deletion.
    # We will also need to figure out owners at some point

    # List of actions https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html

    # view actions
    if action in ["s3:GetObject", "s3:ListObjects", "s3:ListObjjectsV2", "s3:ListBucket", "s3:GetObjectRetention",
                  "s3:GetObjectLegalHold"]:
        try:
            public, allow_private_sharing, discoverable = resource_discoverability_cache(resource_id)
        except:
            public, allow_private_sharing, discoverable = resource_discoverablity(resource_id)
            logger.warning(f"Backfilling cache: {resource_id}:(public:{public},allow_private_sharing:{allow_private_sharing},discoverable:{discoverable})")
            backfill_resource_discoverability(resource_id, public, allow_private_sharing, discoverable)

        try:
            view_access = user_has_view_access_cache(user_id, resource_id)
        except:
            view_access = user_has_view_access(user_id, resource_id)
            logger.warning(f"Backfilling cache: {user_id}:{resource_id}:{view_access}")
            backfill_view_access(user_id, resource_id, view_access)

        if action in ["s3:GetObject", "s3:GetObjectRetention", "s3:GetObjectLegalHold"]:
            return public or allow_private_sharing or view_access
        # view and discoverable actions
        if action in ["s3:ListObjects", "s3:ListObjjectsV2", "s3:ListBucket"]:
            return (
                public
                or allow_private_sharing
                or discoverable
                or view_access
            )

    # edit actions
    if action in ["s3:PutObject", "s3:DeleteObject", "s3:DeleteObjects", "s3:UploadPart", "s3:PutObjectLegalHold"]:
        try:
            edit_access = user_has_edit_access_cache(user_id, resource_id)
        except:
            edit_access = user_has_edit_access(user_id, resource_id)
            logger.warning(f"Backfilling cache: {user_id}:{resource_id}:{edit_access}")
            backfill_edit_access(user_id, resource_id, edit_access)
        print(f"Edit access {user_id} {resource_id} {edit_access}")
        return edit_access

    return False
