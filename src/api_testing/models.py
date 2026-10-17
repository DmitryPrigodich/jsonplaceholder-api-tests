"""Strict response contracts and DTOs for valid requests."""

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class ApiModel(BaseModel):
    # Additive API fields are allowed; required fields and their types remain strict.
    model_config = ConfigDict(strict=True, populate_by_name=True, extra="ignore")


class Geo(ApiModel):
    lat: str
    lng: str


class Address(ApiModel):
    street: str
    suite: str
    city: str
    zipcode: str
    geo: Geo


class Company(ApiModel):
    name: str
    catch_phrase: str = Field(alias="catchPhrase")
    bs: str


class User(ApiModel):
    id: PositiveInt
    name: str
    username: str
    email: str
    address: Address
    phone: str
    website: str
    company: Company


class PostPayload(ApiModel):
    user_id: PositiveInt = Field(alias="userId")
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)


class Post(ApiModel):
    id: PositiveInt
    user_id: PositiveInt = Field(alias="userId")
    title: str
    body: str


class PostPatch(ApiModel):
    title: str = Field(min_length=1)


class Comment(ApiModel):
    post_id: PositiveInt = Field(alias="postId")
    id: PositiveInt
    name: str
    email: str
    body: str
