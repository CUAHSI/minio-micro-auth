import os

os.environ["HS_DATABASE_URL"] = 'postgresql://postgres:postgres@host.docker.internal:54322/postgres'

from fastapi.testclient import TestClient
from api.routers.minio import router as minio_router
import pytest

client = TestClient(minio_router)

# user1 owns the reesource
# user2 does not have access to the resource
# user3 has view access to the resource
# user4 has edit access to the resource
# user5 is an owner
# user6 is is a member of view group
# user7 is a member of edit group

# private resource checks
def check_private_view_authorization(request_body):
    # user1 is the owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

def check_private_edit_authorization(request_body):
    # user1 is the owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}
    
    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

@pytest.mark.parametrize("action_json", [
    "user1_get_object_legal_hold.json",
    "user1_get_object_retention.json",
    "user1_list_bucket.json",
    "user1_list_objects.json",
    "user1_list_objects_v2.json"])
def test_private_view(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_view_authorization(request_body)

@pytest.mark.parametrize("action_json", [
    "user1_put_object.json",
    "user1_put_object_legal_hold.json",
    "user1_upload_part.json",
    "user1_delete_object.json",
    "user1_delete_objects.json"])
def test_private_edit(action_json):
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_edit_authorization(request_body)

# private link actions
def check_private_link_view_authorization(request_body):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", "d5c432ae01eb4f03a73d589e54d341b3")
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

def check_private_link_edit_authorization(request_body):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", "d5c432ae01eb4f03a73d589e54d341b3")
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}
    
    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

@pytest.mark.parametrize("action_json", [
    "user1_get_object_legal_hold.json",
    "user1_get_object_retention.json",
    "user1_list_bucket.json",
    "user1_list_objects_v2.json"])    
def test_private_link_view(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_link_view_authorization(request_body)

@pytest.mark.parametrize("action_json", [
    "user1_put_object.json",
    "user1_put_object_legal_hold.json",
    "user1_upload_part.json",
    "user1_delete_object.json",
    "user1_delete_objects.json"])
def test_private_link_edit(action_json):
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_link_edit_authorization(request_body)

# public actions
def check_public_view_authorization(request_body):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", "a2c0df5bf3eb4d8c8a34beaffe169f91")
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

def check_public_edit_authorization(request_body):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", "a2c0df5bf3eb4d8c8a34beaffe169f91")
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}
    
    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

@pytest.mark.parametrize("action_json", [
    "user1_get_object_legal_hold.json",
    "user1_get_object_retention.json",
    "user1_list_bucket.json",
    "user1_list_objects_v2.json"])    
def test_public_view(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_public_view_authorization(request_body)

@pytest.mark.parametrize("action_json", [
    "user1_put_object.json",
    "user1_put_object_legal_hold.json",
    "user1_upload_part.json",
    "user1_delete_object.json",
    "user1_delete_objects.json"])
def test_public_edit(action_json):
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_public_edit_authorization(request_body)

# discoverable actions
def check_discoverable_view_get_authorization(request_body):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", "5670903e39d54026a729abd4cc148f99")
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

# discoverable actions
def check_discoverable_view_authorization(request_body):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", "5670903e39d54026a729abd4cc148f99")
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

def check_discoverable_edit_authorization(request_body):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", "5670903e39d54026a729abd4cc148f99")
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
    
    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}
    
    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

@pytest.mark.parametrize("action_json", [
    "user1_get_object_legal_hold.json",
    "user1_get_object_retention.json",])    
def test_discoverable_view_get(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_discoverable_view_get_authorization(request_body)

@pytest.mark.parametrize("action_json", [
    "user1_list_bucket.json",
    "user1_list_objects_v2.json"])    
def test_discoverable_view(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_discoverable_view_authorization(request_body)

@pytest.mark.parametrize("action_json", [
    "user1_put_object.json",
    "user1_put_object_legal_hold.json",
    "user1_upload_part.json",
    "user1_delete_object.json",
    "user1_delete_objects.json"])
def test_discoverable_edit(action_json):
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_discoverable_edit_authorization(request_body)

# admin actions
def test_admin_request():
    with open("tests/json_payloads/minio_admin_request.json", "r") as file:
        request_body = file.read()
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # assert cuahsi has authorization
    request_body = request_body.replace("minioadmin", "cuahsi")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # assert user1 does not have authorization
    request_body = request_body.replace("cuahsi", "user1")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}
