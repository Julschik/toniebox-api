"""Pydantic models for Tonie Cloud API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """Current user information."""

    uuid: str
    email: str


class Config(BaseModel):
    """Backend configuration."""

    model_config = ConfigDict(populate_by_name=True)

    locales: list[str]
    unicode_locales: list[str] = Field(alias="unicodeLocales")
    max_chapters: int = Field(alias="maxChapters")
    max_seconds: int = Field(alias="maxSeconds")
    max_bytes: int = Field(alias="maxBytes")
    accepts: list[str]
    stage_warning: bool = Field(alias="stageWarning")
    paypal_client_id: str = Field(alias="paypalClientId")
    sso_enabled: bool = Field(alias="ssoEnabled")


class Household(BaseModel):
    """Household information."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    owner_name: str = Field(alias="ownerName")
    access: str
    can_leave: bool = Field(alias="canLeave")


class Chapter(BaseModel):
    """Chapter on a Creative Tonie."""

    id: str
    title: str
    file: str
    seconds: float
    transcoding: bool


class CreativeTonie(BaseModel):
    """Creative Tonie with chapters."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    household_id: str = Field(alias="householdId")
    name: str
    image_url: str = Field(alias="imageUrl")
    seconds_remaining: float = Field(alias="secondsRemaining")
    seconds_present: float = Field(alias="secondsPresent")
    chapters_remaining: int = Field(alias="chaptersRemaining")
    chapters_present: int = Field(alias="chaptersPresent")
    transcoding: bool
    last_update: Optional[datetime] = Field(alias="lastUpdate", default=None)
    chapters: list[Chapter]


class UploadRequestDetails(BaseModel):
    """S3 presigned upload details."""

    url: str
    fields: dict[str, str]


class FileUploadRequest(BaseModel):
    """Response from file upload request."""

    model_config = ConfigDict(populate_by_name=True)

    request: UploadRequestDetails
    file_id: str = Field(alias="fileId")
