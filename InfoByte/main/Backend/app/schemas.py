from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
Email = Annotated[str, StringConstraints(strip_whitespace=True, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9 ()-]{7,24}$")]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Credentials(Input):
    email: Email
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class Registration(Credentials):
    full_name: Name
    phone: Phone | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value):
        if value and not 7 <= sum(c.isdigit() for c in value) <= 15:
            raise ValueError("Телефон нөмірінде 7–15 цифр болуы керек.")
        return value


class Login(Credentials):
    remember: bool = False


class Profile(BaseModel):
    id: UUID
    email: str
    full_name: str
    phone: str | None


class Topic(Input):
    title: Name


class PlanItem(Topic):
    id: UUID
    done: bool = False


class Progress(Input):
    done: bool


class Problem(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
