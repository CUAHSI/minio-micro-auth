import logging

from fastapi import FastAPI

from .database import (
    is_superuser_and_id,
    owner_username_from_bucket_name,
    resource_discoverablity,
    user_has_edit_access,
    user_has_view_access,
)
from .models import AuthRequest

logger = logging.getLogger("micro-auth")

app = FastAPI()


@app.post("/")
async def root(auth_request: AuthRequest):

    username = auth_request.input.conditions.user
    bucket = auth_request.input.bucket
    action = auth_request.input.action

    logger.debug(f"Checking {username} {bucket} {action}")

    if username == "cuahsi" or username == "minioadmin":
        # allow cuahsi admin account always
        return {"result": {"allow": True}}

    if auth_request.input.action in ["s3:GetBucketLocation"]:
        # This is needed by mc to list buckets and does not contain a prefix
        return {"result": {"allow": True}}

    is_superuser, user_id = is_superuser_and_id(username)
    if is_superuser:
        return {"result": {"allow": True}}

    # prefixes are paths to (folders/set of) objects in the bucket
    prefixes = auth_request.input.conditions.prefixes
    if not prefixes:
        # only owners of the bucket can do actions without prefixes
        bucket_owner = owner_username_from_bucket_name(bucket)
        if bucket_owner == username:
            logger.debug("Owner", username, bucket, action)
            return {"result": {"allow": True}}
        logger.debug(f"Not owner with no prefixes {username} {bucket} {action}")
        return {"result": {"allow": False}}

    # users access the objects in these buckets through presigned urls, admins are approved above
    if bucket in ["zips", "tmp", "bags"]:
        return {"result": {"allow": False}}

    resource_ids = [prefix.split("/")[0] for prefix in prefixes]
    # check the user and each resource against the action
    for resource_id in resource_ids:
        if not check_user_authorization(user_id, resource_id, action):
            logger.debug(f"Denied {username} {resource_id} {action}")
            return {"result": {"allow": False}}
        else:
            logger.debug(f"Approved {username} {resource_id} {action}")

    logger.debug(f"No resources found for {username} {prefixes}")
    return {"result": {"allow": False}}


def check_user_authorization(user_id, resource_id, action):
    # Break this down into just view and edit for now.
    # HydroShare does not conusme changes made through S3 API yet so edit check is not active
    # Later on we could share the metadata files only or allow resource deletion.
    # We will also need to figure out owners at some point

    # List of actions https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html

    # view actions
    if action in ["s3:GetObject", "s3:ListObjects", "s3:ListObjjectsV2", "s3:ListBucket"]:
        public, allow_private_sharing, discoverable = resource_discoverablity(resource_id)

        if action == "s3:GetObject":
            return public or allow_private_sharing or user_has_view_access(user_id, resource_id)
        # view and discoverable actions
        if action == "s3:ListObjects" or action == "s3:ListObjjectsV2" or action == "s3:ListBucket":
            return public or allow_private_sharing or discoverable or user_has_view_access(user_id, resource_id)

    # edit actions
    if action in ["s3:PutObject", "s3:DeleteObject", "s3:DeleteObjects", "s3:UploadPart"]:
        return user_has_edit_access(user_id, resource_id)

    return False
