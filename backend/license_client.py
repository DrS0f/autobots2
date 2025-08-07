import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import aiohttp
from threading import Lock
import uuid

logger = logging.getLogger(__name__)


class LicenseStatus:
    """License status enumeration"""
    OK = "OK"
    LOCKED = "LOCKED"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"
    ERROR = "ERROR"


class LicenseClient:
    """Client for license verification with caching and state management"""
    
    def __init__(self):
        self.license_key = os.environ.get("LICENSE_KEY", "")
        self.license_api_url = os.environ.get("LICENSE_API_URL", "http://localhost:8002")
        self.verify_interval = int(os.environ.get("LICENSE_VERIFY_INTERVAL", "900"))  # 15 minutes
        
        # State management
        self.status = LicenseStatus.LOCKED if self.license_key else LicenseStatus.OK  # Start OK if no key required
        self.last_verification = 0
        self.license_data: Dict[str, Any] = {}
        self.device_id = self._generate_device_id()
        self._lock = Lock()
        
        # Background task
        self._verification_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
        logger.info(f"LicenseClient initialized. Key present: {bool(self.license_key)}, "
                   f"API URL: {self.license_api_url}, Verify interval: {self.verify_interval}s")
    
    def _generate_device_id(self) -> str:
        """Generate a device identifier"""
        # In production, this might use hardware info, MAC address, etc.
        device_file = "/tmp/device_id"
        try:
            if os.path.exists(device_file):
                with open(device_file, "r") as f:
                    return f.read().strip()
            else:
                device_id = str(uuid.uuid4())
                with open(device_file, "w") as f:
                    f.write(device_id)
                return device_id
        except Exception:
            return str(uuid.uuid4())
    
    async def start(self):
        """Start the background verification task"""
        if not self.license_key:
            logger.info("No license key configured, running without license restrictions")
            self.status = LicenseStatus.OK
            return
        
        logger.info("Starting license verification service")
        await self._verify_now()
        
        # Start background verification task
        self._verification_task = asyncio.create_task(self._verification_loop())
    
    async def stop(self):
        """Stop the background verification task"""
        self._shutdown = True
        if self._verification_task:
            self._verification_task.cancel()
            try:
                await self._verification_task
            except asyncio.CancelledError:
                pass
    
    async def _verification_loop(self):
        """Background task to periodically verify license"""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.verify_interval)
                if not self._shutdown:
                    await self._verify_now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in verification loop: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def _verify_now(self):
        """Perform license verification"""
        if not self.license_key:
            return
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                params = {
                    "license_key": self.license_key,
                    "device_id": self.device_id
                }
                
                async with session.get(f"{self.license_api_url}/auth/verify", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._process_verification_response(data)
                    else:
                        logger.error(f"License verification failed with status {response.status}")
                        await self._handle_verification_error("HTTP error")
                        
        except asyncio.TimeoutError:
            logger.error("License verification timeout")
            await self._handle_verification_error("Timeout")
        except Exception as e:
            logger.error(f"License verification error: {e}")
            await self._handle_verification_error(str(e))
    
    async def _process_verification_response(self, data: Dict[str, Any]):
        """Process the verification response"""
        with self._lock:
            self.last_verification = time.time()
            
            if data.get("valid"):
                self.status = LicenseStatus.OK
                self.license_data = data
                
                # Log grace period warning
                if data.get("in_grace_period"):
                    logger.warning("License is in GRACE PERIOD - expires soon!")
                
                # Log expiry warning
                time_to_expiry = data.get("time_to_expiry_hours", 0)
                if time_to_expiry <= 24:
                    logger.warning(f"License expires in {time_to_expiry} hours!")
                
                logger.info(f"License verification successful. Status: {self.status}")
            else:
                # License is invalid
                self.status = LicenseStatus.LOCKED
                self.license_data = {}
                logger.error(f"License verification failed: {data.get('message', 'Unknown error')}")
    
    async def _handle_verification_error(self, error: str):
        """Handle verification errors with grace period logic"""
        with self._lock:
            # If we haven't verified successfully in the grace period, lock the system
            grace_period = 2 * 3600  # 2 hours grace for network issues
            if self.last_verification == 0 or (time.time() - self.last_verification) > grace_period:
                if self.status != LicenseStatus.LOCKED:
                    logger.critical(f"License verification failed for too long ({error}), locking system")
                    self.status = LicenseStatus.LOCKED
                    self.license_data = {}
    
    def is_licensed(self) -> bool:
        """Check if the system is properly licensed"""
        if not self.license_key:
            return True  # No license required
        
        with self._lock:
            return self.status == LicenseStatus.OK
    
    def get_status(self) -> Dict[str, Any]:
        """Get current license status"""
        with self._lock:
            if not self.license_key:
                return {
                    "status": "no_license_required",
                    "message": "Running without license restrictions",
                    "licensed": True
                }
            
            status_data = {
                "status": self.status,
                "licensed": self.status == LicenseStatus.OK,
                "last_verification": datetime.fromtimestamp(self.last_verification, tz=timezone.utc).isoformat() if self.last_verification > 0 else None,
                "device_id": self.device_id,
                "verify_interval": self.verify_interval
            }
            
            if self.license_data:
                status_data.update({
                    "customer_id": self.license_data.get("customer_id"),
                    "plan": self.license_data.get("plan"),
                    "features": self.license_data.get("features", []),
                    "expires_at": self.license_data.get("expires_at"),
                    "time_to_expiry_hours": self.license_data.get("time_to_expiry_hours"),
                    "in_grace_period": self.license_data.get("in_grace_period", False),
                    "message": self.license_data.get("message", "")
                })
            
            return status_data
    
    async def verify_immediately(self) -> Dict[str, Any]:
        """Force immediate license verification"""
        await self._verify_now()
        return self.get_status()


# Global license client instance
license_client = LicenseClient()