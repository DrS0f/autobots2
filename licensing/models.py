from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel


class License(BaseModel):
    id: str
    customer_id: str  # sub claim
    plan: str
    features: List[str]
    device_id: Optional[str] = None
    issued_at: datetime
    expires_at: datetime
    grace_days: int = 7
    is_active: bool = True
    revoked_at: Optional[datetime] = None
    
    
class LicenseRequest(BaseModel):
    customer_id: str
    plan: str = "basic"
    features: List[str] = ["basic_automation"]
    device_id: Optional[str] = None
    duration_days: int = 30
    grace_days: int = 7


class LicenseResponse(BaseModel):
    license_key: str
    customer_id: str
    plan: str
    features: List[str]
    expires_at: datetime
    grace_days: int


class VerifyRequest(BaseModel):
    license_key: str
    device_id: Optional[str] = None


class VerifyResponse(BaseModel):
    valid: bool
    customer_id: Optional[str] = None
    plan: Optional[str] = None
    features: List[str] = []
    expires_at: Optional[datetime] = None
    grace_days: int = 0
    time_to_expiry_hours: Optional[int] = None
    in_grace_period: bool = False
    message: str = ""


class RevokeRequest(BaseModel):
    license_key: str
    reason: str = "Revoked by admin"


class AdminCommand(BaseModel):
    action: str  # issue, revoke, extend, list
    license_key: Optional[str] = None
    customer_id: Optional[str] = None
    duration_days: Optional[int] = None
    plan: Optional[str] = None
    features: Optional[List[str]] = None
    device_id: Optional[str] = None
    grace_days: Optional[int] = 7