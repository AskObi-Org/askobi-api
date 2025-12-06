from typing import Any
from pydantic import  BaseModel, EmailStr

from src.schemas.base import Schema



# This ensures that your JSON data follows a strict structure in your API.
class NotificationPreferences(BaseModel):
    reminders: bool = True
    prescription_updates: bool = True
    health_tips: bool = True
    marketing_emails: bool = False


class UserPreferences(Schema):
    theme: str = "system"  # Options: 'light', 'dark', 'system'
    language: str = "en"
    notifications: NotificationPreferences = NotificationPreferences()