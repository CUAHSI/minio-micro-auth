import os

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@host.docker.internal:54322/postgres")
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


def get_bucket_name(username: str) -> str:
    # returns the user's bucket name
    query = """SELECT theme_userprofile._bucket_name
    FROM theme_userprofile
    INNER JOIN auth_user
    ON (auth_user.id = theme_userprofile.user_id)
    WHERE auth_user.username = :username"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query), parameters=dict(username=username))
        return rs.fetchone()[0]


def owner_username_from_bucket_name(bucket_name: str) -> str:
    # returns the owner's username from the bucket name
    query = """SELECT auth_user.username
    FROM auth_user
    INNER JOIN theme_userprofile
    ON (auth_user.id = theme_userprofile.user_id)
    WHERE theme_userprofile._bucket_name = :bucket_name"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query), parameters=dict(bucket_name=bucket_name))
        row = rs.fetchone()
        if row:
            return row[0]


def quota_holder_id_from_bucket_name(bucket_name: str) -> str:
    # returns the owner's username from the bucket name
    query = """SELECT auth_user.id
    FROM auth_user
    INNER JOIN theme_userprofile
    ON (auth_user.id = theme_userprofile.user_id)
    WHERE theme_userprofile._bucket_name = :bucket_name"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query), parameters=dict(bucket_name=bucket_name))
        row = rs.fetchone()
        if row:
            return row[0]


def resource_discoverablity(resource_id: str, quota_holder_id: int):
    # return public, allow_private_sharing, discoverable as tuple
    query = """SELECT hs_access_control_resourceaccess.public, hs_access_control_resourceaccess.allow_private_sharing, hs_access_control_resourceaccess.discoverable
    FROM hs_access_control_resourceaccess
    INNER JOIN hs_core_genericresource
    ON (hs_core_genericresource.page_ptr_id = hs_access_control_resourceaccess.resource_id)
    WHERE hs_core_genericresource.short_id = :resource_id
    AND hs_core_genericresource.quota_holder_id = :quota_holder_id"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query), parameters=dict(resource_id=resource_id, quota_holder_id=quota_holder_id))
        row = rs.fetchone()
        if row:
            return row
    return (False, False, False)


def user_has_view_access(user_id: int, resource_id: str, quota_holder_id: int):
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
    AND hs_core_genericresource.short_id = :resource_id
    AND hs_core_genericresource.quota_holder_id = :quota_holder_id"""

    with engine.connect() as con:
        rs = con.execute(statement=text(query), parameters=dict(user_id=user_id, resource_id=resource_id, quota_holder_id=quota_holder_id))
        result = rs.fetchone()
        if result:
            return True
        return False


def user_has_edit_access(user_id: int, resource_id: str, quota_holder_id: int):
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
    AND hs_core_genericresource.short_id = :resource_id
    AND hs_core_genericresource.quota_holder_id = :quota_holder_id"""
    with engine.connect() as con:
        rs = con.execute(statement=text(query), parameters=dict(user_id=user_id, resource_id=resource_id, quota_holder_id=quota_holder_id))
        result = rs.fetchone()
        if result:
            return True
        return False
