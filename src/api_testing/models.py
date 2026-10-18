"""Strict response contracts and DTOs for valid requests."""

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class ResponseModel(BaseModel):
    model_config = ConfigDict(
        strict=True, validate_by_alias=True, validate_by_name=False, extra="ignore"
    )


class RequestModel(BaseModel):
    model_config = ConfigDict(
        strict=True, validate_by_alias=True, validate_by_name=True, extra="ignore"
    )


class Geo(ResponseModel):
    lat: str
    lng: str


class Address(ResponseModel):
    street: str
    suite: str
    city: str
    zipcode: str
    geo: Geo


class Company(ResponseModel):
    name: str
    catch_phrase: str = Field(alias="catchPhrase")
    bs: str


class User(ResponseModel):
    id: PositiveInt
    name: str
    username: str
    email: str
    address: Address
    phone: str
    website: str
    company: Company


class PostPayload(RequestModel):
    user_id: PositiveInt = Field(alias="userId")
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)


class Post(ResponseModel):
    id: PositiveInt
    user_id: PositiveInt = Field(alias="userId")
    title: str
    body: str


class PostPatch(RequestModel):
    title: str = Field(min_length=1)


class Comment(ResponseModel):
    post_id: PositiveInt = Field(alias="postId")
    id: PositiveInt
    name: str
    email: str
    body: str
