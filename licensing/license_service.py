import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import os
from pathlib import Path

from jose import jwt, JWTError
from .models import License, LicenseResponse, VerifyResponse


class LicenseService:
    def __init__(self, secret_key: str = None, storage_path: str = "licenses.json"):
        self.secret_key = secret_key or os.environ.get("LICENSE_SECRET_KEY", "your-secret-key-change-this")
        self.storage_path = storage_path
        self.algorithm = "HS256"
        self._ensure_storage()
    
    def _ensure_storage(self):
        """Create storage file if it doesn't exist"""
        if not os.path.exists(self.storage_path):
            self._save_licenses({})
    
    def _load_licenses(self) -> Dict[str, License]:
        """Load licenses from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return {
                    license_id: License(**license_data)
                    for license_id, license_data in data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_licenses(self, licenses: Dict[str, License]):
        """Save licenses to storage"""
        serializable_data = {}
        for license_id, license_obj in licenses.items():
            license_dict = license_obj.dict()
            # Convert datetime objects to ISO format strings
            for key, value in license_dict.items():
                if isinstance(value, datetime):
                    license_dict[key] = value.isoformat()
            serializable_data[license_id] = license_dict
        
        with open(self.storage_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)
    
    def issue_license(
        self,
        customer_id: str,
        plan: str = "basic",
        features: List[str] = None,
        device_id: Optional[str] = None,
        duration_days: int = 30,
        grace_days: int = 7
    ) -> LicenseResponse:
        """Issue a new license"""
        if features is None:
            features = ["basic_automation"]
        
        license_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=duration_days)
        
        # Create license object
        license_obj = License(
            id=license_id,
            customer_id=customer_id,
            plan=plan,
            features=features,
            device_id=device_id,
            issued_at=now,
            expires_at=expires_at,
            grace_days=grace_days,
            is_active=True
        )
        
        # Save to storage
        licenses = self._load_licenses()
        licenses[license_id] = license_obj
        self._save_licenses(licenses)
        
        # Generate JWT token
        payload = {
            "sub": customer_id,
            "license_id": license_id,
            "plan": plan,
            "features": features,
            "device_id": device_id,
            "exp": expires_at.timestamp(),
            "iat": now.timestamp(),
            "grace_days": grace_days
        }
        
        license_key = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return LicenseResponse(
            license_key=license_key,
            customer_id=customer_id,
            plan=plan,
            features=features,
            expires_at=expires_at,
            grace_days=grace_days
        )
    
    def verify_license(self, license_key: str, device_id: Optional[str] = None) -> VerifyResponse:
        """Verify a license key"""
        try:
            # Decode JWT
            payload = jwt.decode(license_key, self.secret_key, algorithms=[self.algorithm])
            
            license_id = payload.get("license_id")
            customer_id = payload.get("sub")
            plan = payload.get("plan", "basic")
            features = payload.get("features", [])
            exp_timestamp = payload.get("exp")
            grace_days = payload.get("grace_days", 7)
            token_device_id = payload.get("device_id")
            
            if not all([license_id, customer_id, exp_timestamp]):
                return VerifyResponse(
                    valid=False,
                    message="Invalid license format"
                )
            
            # Load license from storage
            licenses = self._load_licenses()
            license_obj = licenses.get(license_id)
            
            if not license_obj:
                return VerifyResponse(
                    valid=False,
                    message="License not found"
                )
            
            # Check if license is revoked
            if not license_obj.is_active or license_obj.revoked_at:
                return VerifyResponse(
                    valid=False,
                    message="License has been revoked"
                )
            
            # Check device binding if specified
            if token_device_id and device_id and token_device_id != device_id:
                return VerifyResponse(
                    valid=False,
                    message="License not valid for this device"
                )
            
            # Check expiration
            now = datetime.now(timezone.utc)
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            grace_end = expires_at + timedelta(days=grace_days)
            
            time_to_expiry_hours = int((expires_at - now).total_seconds() / 3600)
            in_grace_period = now > expires_at and now <= grace_end
            
            if now > grace_end:
                return VerifyResponse(
                    valid=False,
                    message="License has expired (grace period ended)"
                )
            
            # License is valid
            return VerifyResponse(
                valid=True,
                customer_id=customer_id,
                plan=plan,
                features=features,
                expires_at=expires_at,
                grace_days=grace_days,
                time_to_expiry_hours=max(0, time_to_expiry_hours),
                in_grace_period=in_grace_period,
                message="License is valid" + (" (in grace period)" if in_grace_period else "")
            )
            
        except JWTError as e:
            return VerifyResponse(
                valid=False,
                message=f"Invalid license token: {str(e)}"
            )
        except Exception as e:
            return VerifyResponse(
                valid=False,
                message=f"License verification failed: {str(e)}"
            )
    
    def revoke_license(self, license_key: str, reason: str = "Revoked by admin") -> bool:
        """Revoke a license"""
        try:
            payload = jwt.decode(license_key, self.secret_key, algorithms=[self.algorithm])
            license_id = payload.get("license_id")
            
            if not license_id:
                return False
            
            licenses = self._load_licenses()
            license_obj = licenses.get(license_id)
            
            if license_obj:
                license_obj.is_active = False
                license_obj.revoked_at = datetime.now(timezone.utc)
                self._save_licenses(licenses)
                return True
            
            return False
            
        except JWTError:
            return False
    
    def list_licenses(self) -> List[License]:
        """List all licenses"""
        licenses = self._load_licenses()
        return list(licenses.values())
    
    def extend_license(self, license_key: str, additional_days: int) -> bool:
        """Extend a license by additional days"""
        try:
            payload = jwt.decode(license_key, self.secret_key, algorithms=[self.algorithm])
            license_id = payload.get("license_id")
            
            if not license_id:
                return False
            
            licenses = self._load_licenses()
            license_obj = licenses.get(license_id)
            
            if license_obj and license_obj.is_active:
                license_obj.expires_at += timedelta(days=additional_days)
                self._save_licenses(licenses)
                return True
            
            return False
            
        except JWTError:
            return False