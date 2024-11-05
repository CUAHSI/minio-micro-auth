import os

from sqlalchemy import create_engine, text

# SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user" INNER JOIN "theme_userprofile" ON ("auth_user"."id" = "theme_userprofile"."user_id") WHERE "theme_userprofile"."_bucket_name" = admin-21e67f86f4df4b008a5894622fa81c00

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:54322/postgres")
engine = create_engine(DATABASE_URL)


def is_superuser_and_id(username: str):
    # return is_superuser and user_id as tuple
    with engine.connect() as con:
        rs = con.execute(
            text(f"SELECT auth_user.is_superuser, auth_user.id FROM auth_user WHERE auth_user.username = '{username}'")
        )
        return rs.fetchone()


def get_bucket_name(username: str) -> str:
    # returns the user's bucket name
    with engine.connect() as con:
        rs = con.execute(
            text(
                f"SELECT theme_userprofile._bucket_name FROM theme_userprofile INNER JOIN auth_user ON (auth_user.id = theme_userprofile.user_id) WHERE auth_user.username = '{username}'"
            )
        )
        return rs.fetchone()[0]


def owner_username_from_bucket_name(bucket_name: str) -> str:
    # returns the owner's username from the bucket name
    with engine.connect() as con:
        rs = con.execute(
            text(
                f"SELECT auth_user.username FROM auth_user INNER JOIN theme_userprofile ON (auth_user.id = theme_userprofile.user_id) WHERE theme_userprofile._bucket_name = '{bucket_name}'"
            )
        )
        return rs.fetchone()[0]


def resource_discoverablity(resource_id: str):
    # return public, allow_private_sharing, discoverable as tuple
    with engine.connect() as con:
        rs = con.execute(
            text(
                f"SELECT hs_access_control_resourceaccess.public, hs_access_control_resourceaccess.allow_private_sharing, hs_access_control_resourceaccess.discoverable FROM hs_access_control_resourceaccess INNER JOIN hs_core_genericresource ON (hs_core_genericresource.page_ptr_id = hs_access_control_resourceaccess.resource_id) WHERE hs_core_genericresource.short_id = '{resource_id}'"
            )
        )
        return rs.fetchone()


def user_has_view_access(user_id: int, resource_id: str):
    query = f"""SELECT DISTINCT hs_core_genericresource.short_id 
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
WHERE (hs_access_control_userresourceprivilege.user_id = {user_id}
OR (hs_access_control_usergroupprivilege.user_id = {user_id} 
AND hs_access_control_groupaccess.active))
and hs_core_genericresource.short_id = '{resource_id}'"""
    with engine.connect() as con:
        rs = con.execute(text(query))
        result = rs.fetchone()
        if result:
            return True
        return False


def user_has_edit_access(user_id: int, resource_id: str):
    query = f"""SELECT DISTINCT hs_core_genericresource.short_id 
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
AND hs_access_control_userresourceprivilege.user_id = {user_id}) 
OR (hs_access_control_userresourceprivilege.privilege <= 2 
AND hs_access_control_userresourceprivilege.user_id = {user_id} 
AND NOT hs_access_control_resourceaccess.immutable) 
OR (hs_access_control_usergroupprivilege.user_id = {user_id} 
AND hs_access_control_groupaccess.active 
AND hs_access_control_groupresourceprivilege.privilege = 2 
AND NOT hs_access_control_resourceaccess.immutable))
and hs_core_genericresource.short_id = '{resource_id}'"""
    with engine.connect() as con:
        rs = con.execute(text(query))
        result = rs.fetchone()
        if result:
            return True
        return False


print(is_superuser_and_id('admin'))
print(get_bucket_name('admin'))
print(owner_username_from_bucket_name('admin-21e67f86f4df4b008a5894622fa81c00'))
print(resource_discoverablity('c5b44869a666462a921ead0c6f3c9975'))
print(user_has_view_access(4, 'c5b44869a666462a921ead0c6f3c9975'))
print(user_has_edit_access(4, 'c5b44869a666462a921ead0c6f3c9975'))
