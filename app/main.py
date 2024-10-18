from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()

class Conditions(BaseModel):
    preferred_username: list[str] = []
    username: list[str] = []

    @property
    def user(self):
        if self.preferred_username:
            return self.preferred_username[0]
        else:
            return self.username[0]

class Input(BaseModel):
    conditions: Conditions

class AuthRequest(BaseModel):
    input: Input

@app.post("/")
async def root(auth_request: AuthRequest):
    if auth_request.input.conditions.user == "cuahsi":
        return {"result": {"allow": True}}
    return {"result": {"allow": False}}

