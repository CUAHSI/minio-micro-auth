import os

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("HS_DATABASE_URL")
engine = create_engine(DATABASE_URL)


def is_superuser_and_id(username: str):
    # return is_superuser and user_id as tuple
    query = """SELECT auth_user.is_superuser, auth_user.id
    FROM auth_user
    WHERE auth_user.username = :username"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query), parameters=dict(username=username))
        row = rs.fetchone()
        if row:
            return row
    return {False, None}


def resource_discoverablity(resource_id: str):
    # return public, allow_private_sharing, discoverable as tuple
    query = """SELECT hs_access_control_resourceaccess.public, hs_access_control_resourceaccess.allow_private_sharing, hs_access_control_resourceaccess.discoverable
    FROM hs_access_control_resourceaccess
    INNER JOIN hs_core_genericresource
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_resourceaccess.resource_id)
    WHERE hs_core_genericresource.short_id = :resource_id"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query), parameters=dict(resource_id=resource_id))
        row = rs.fetchone()
        if row:
            return row
    return (False, False, False)


def user_has_view_access(user_id: int, resource_id: str):
    query = """SELECT DISTINCT hs_core_genericresource.short_id
    FROM hs_core_genericresource
    LEFT OUTER JOIN hs_access_control_userresourceprivilege
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_userresourceprivilege.resource_id)
    LEFT OUTER JOIN hs_access_control_groupresourceprivilege
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_groupresourceprivilege.resource_id)
    LEFT OUTER JOIN auth_group
    ON (hs_access_control_groupresourceprivilege.group_id = auth_group.id)
    LEFT OUTER JOIN hs_access_control_usergroupprivilege
    ON (auth_group.id = hs_access_control_usergroupprivilege.group_id)
    LEFT OUTER JOIN hs_access_control_groupaccess
    ON (auth_group.id = hs_access_control_groupaccess.group_id)
    INNER JOIN pages_page
    ON (hs_core_genericresource.page_ptr_id = pages_page.id)
    WHERE (hs_access_control_userresourceprivilege.user_id = :user_id
    OR (hs_access_control_usergroupprivilege.user_id = :user_id
    AND hs_access_control_groupaccess.active))
    AND hs_core_genericresource.short_id = :resource_id"""

    with engine.connect() as con:
        rs = con.execute(
            statement=text(query),
            parameters=dict(user_id=user_id, resource_id=resource_id),
        )
        result = rs.fetchone()
        if result:
            return True
        return False


def user_has_edit_access(user_id: int, resource_id: str):
    query = """SELECT DISTINCT hs_core_genericresource.short_id
    FROM hs_core_genericresource
    LEFT OUTER JOIN hs_access_control_userresourceprivilege
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_userresourceprivilege.resource_id)
    LEFT OUTER JOIN hs_access_control_resourceaccess
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_resourceaccess.resource_id)
    LEFT OUTER JOIN hs_access_control_groupresourceprivilege
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_groupresourceprivilege.resource_id)
    LEFT OUTER JOIN auth_group
    ON (hs_access_control_groupresourceprivilege.group_id = auth_group.id)
    LEFT OUTER JOIN hs_access_control_usergroupprivilege
    ON (auth_group.id = hs_access_control_usergroupprivilege.group_id)
    LEFT OUTER JOIN hs_access_control_groupaccess
    ON (auth_group.id = hs_access_control_groupaccess.group_id)
    INNER JOIN pages_page
    ON (hs_core_genericresource.page_ptr_id = pages_page.id)
    WHERE ((hs_access_control_userresourceprivilege.privilege = 1
    AND hs_access_control_userresourceprivilege.user_id = :user_id)
    OR (hs_access_control_userresourceprivilege.privilege <= 2
    AND hs_access_control_userresourceprivilege.user_id = :user_id
    AND NOT hs_access_control_resourceaccess.immutable)
    OR (hs_access_control_usergroupprivilege.user_id = :user_id
    AND hs_access_control_groupaccess.active
    AND hs_access_control_groupresourceprivilege.privilege = 2
    AND NOT hs_access_control_resourceaccess.immutable))
    AND hs_core_genericresource.short_id = :resource_id"""
    with engine.connect() as con:
        rs = con.execute(
            statement=text(query),
            parameters=dict(user_id=user_id, resource_id=resource_id),
        )
        result = rs.fetchone()
        if result:
            return True
        return False

def user_quota_usage(user_id: int):
    query = """SELECT SUM(""hs_core_resourcefile"."_size")
    FROM "hs_core_resourcefile"
    WHERE "hs_core_resourcefile"."object_id"
    IN (SELECT U0."page_ptr_id" FROM "hs_core_genericresource" U0 WHERE U0."quota_holder_id" = :user_id)"""

    with engine.connect() as con:
        rs = con.execute(
            statement=text(query),
            parameters=dict(user_id=user_id),
        )
        result = rs.fetchone()
        if result:
            return result[0]
        return 0

def user_has_quota(user_id: int, filezize : int):
    quota_usage = user_quota_usage(user_id)
    query = """SELECT "theme_userquota"."allocated_value"
    FROM "theme_userquota"
    WHERE "theme_userquota"."user_id" = :user_id"""

    with engine.connect() as con:
        rs = con.execute(
            statement=text(query),
            parameters=dict(user_id=user_id),
        )
        result = rs.fetchone()
        if result:
            return quota_usage + filezize <= result[0]
        return False
