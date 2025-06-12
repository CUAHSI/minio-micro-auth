import logging

import cache
from fastapi import APIRouter, Request

router = APIRouter()
logger = logging.getLogger("micro-auth")


@router.post("/hook/")
async def set_auth(request: Request):
    try:
        body = await request.json()

        for resource in body["resources"]:
            resource_id = resource["id"]
            for user_access in resource["user_access"]:
                user_id = user_access["id"]
                access = user_access["access"]
                cache.set_cache_xx(f"{user_id}:{resource_id}", access)

            if resource["public"]:
                resource_access = "PUBLIC"
            elif resource["discoverable"]:
                resource_access = "DISCOVERABLE"
            else:
                resource_access = "PRIVATE"
            cache.hset_cache_xx(
                resource_id,
                {
                    "access": resource_access,
                    "private_sharing": "ENABLED" if resource["allow_private_sharing"] else "DISABLED",
                    "bucket_name": resource["bucket_name"],
                },
            )

        return None, 204

    except Exception as e:
        logger.exception("Error processing request")
        raise
