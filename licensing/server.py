from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List

from .models import (
    LicenseRequest, LicenseResponse, VerifyRequest, VerifyResponse,
    RevokeRequest, License
)
from .license_service import LicenseService

app = FastAPI(title="iOS Instagram Automation - License Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize license service
license_service = LicenseService(
    secret_key=os.environ.get("LICENSE_SECRET_KEY", "your-secret-key-change-this"),
    storage_path=os.environ.get("LICENSE_STORAGE_PATH", "/tmp/licenses.json")
)

# Simple admin authentication
security = HTTPBearer()
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "admin-token-change-this")

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials


@app.get("/")
async def root():
    return {
        "service": "iOS Instagram Automation License Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/auth/issue", response_model=LicenseResponse)
async def issue_license(
    request: LicenseRequest,
    _: HTTPAuthorizationCredentials = Depends(verify_admin_token)
):
    """Issue a new license (admin only)"""
    try:
        response = license_service.issue_license(
            customer_id=request.customer_id,
            plan=request.plan,
            features=request.features,
            device_id=request.device_id,
            duration_days=request.duration_days,
            grace_days=request.grace_days
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to issue license: {str(e)}"
        )


@app.get("/auth/verify", response_model=VerifyResponse)
async def verify_license(license_key: str, device_id: str = None):
    """Verify a license key (public endpoint)"""
    try:
        response = license_service.verify_license(license_key, device_id)
        return response
    except Exception as e:
        return VerifyResponse(
            valid=False,
            message=f"Verification failed: {str(e)}"
        )


@app.post("/auth/revoke")
async def revoke_license(
    request: RevokeRequest,
    _: HTTPAuthorizationCredentials = Depends(verify_admin_token)
):
    """Revoke a license (admin only)"""
    try:
        success = license_service.revoke_license(request.license_key, request.reason)
        if success:
            return {"success": True, "message": "License revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License not found or already revoked"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke license: {str(e)}"
        )


@app.get("/admin/licenses", response_model=List[License])
async def list_licenses(_: HTTPAuthorizationCredentials = Depends(verify_admin_token)):
    """List all licenses (admin only)"""
    try:
        licenses = license_service.list_licenses()
        return licenses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list licenses: {str(e)}"
        )


@app.post("/admin/extend")
async def extend_license(
    license_key: str,
    additional_days: int,
    _: HTTPAuthorizationCredentials = Depends(verify_admin_token)
):
    """Extend a license by additional days (admin only)"""
    try:
        success = license_service.extend_license(license_key, additional_days)
        if success:
            return {"success": True, "message": f"License extended by {additional_days} days"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License not found or inactive"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extend license: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)