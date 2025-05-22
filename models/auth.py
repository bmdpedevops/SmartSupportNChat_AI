from pydantic import BaseModel


class User(BaseModel):
    username: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class Register(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
