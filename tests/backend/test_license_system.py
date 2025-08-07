"""
Test cases for Phase 5 SaaS Licensing & Kill-Switch system
"""
import asyncio
import pytest
import sys
import os
from datetime import datetime, timezone, timedelta

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../licensing'))

from license_client import LicenseClient, LicenseStatus
from licensing.license_service import LicenseService
from licensing.models import LicenseResponse, VerifyResponse


class TestLicenseService:
    """Test cases for the LicenseService backend"""
    
    def setup_method(self):
        """Set up test environment"""
        self.license_service = LicenseService(
            secret_key="test-secret-key",
            storage_path="/tmp/test_licenses.json"
        )
    
    def test_issue_license(self):
        """Test license issuance"""
        response = self.license_service.issue_license(
            customer_id="test-customer",
            plan="premium",
            features=["advanced_automation", "analytics"],
            duration_days=30
        )
        
        assert isinstance(response, LicenseResponse)
        assert response.customer_id == "test-customer"
        assert response.plan == "premium"
        assert "advanced_automation" in response.features
        assert response.license_key is not None
        assert len(response.license_key) > 50  # JWT should be reasonably long
    
    def test_verify_valid_license(self):
        """Test verification of a valid license"""
        # Issue a license first
        issued = self.license_service.issue_license(
            customer_id="test-verify",
            duration_days=30
        )
        
        # Verify it
        response = self.license_service.verify_license(issued.license_key)
        
        assert isinstance(response, VerifyResponse)
        assert response.valid is True
        assert response.customer_id == "test-verify"
        assert response.time_to_expiry_hours > 24 * 29  # Should be close to 30 days
    
    def test_verify_invalid_license(self):
        """Test verification of invalid license"""
        response = self.license_service.verify_license("invalid-license-key")
        
        assert isinstance(response, VerifyResponse)
        assert response.valid is False
        assert "Invalid license token" in response.message
    
    def test_revoke_license(self):
        """Test license revocation"""
        # Issue a license first
        issued = self.license_service.issue_license(
            customer_id="test-revoke",
            duration_days=30
        )
        
        # Verify it's valid
        verify_response = self.license_service.verify_license(issued.license_key)
        assert verify_response.valid is True
        
        # Revoke it
        revoke_success = self.license_service.revoke_license(issued.license_key)
        assert revoke_success is True
        
        # Verify it's now invalid
        verify_response = self.license_service.verify_license(issued.license_key)
        assert verify_response.valid is False
        assert "revoked" in verify_response.message.lower()
    
    def test_expired_license(self):
        """Test verification of expired license (simulate by short duration)"""
        import time
        
        # Issue a license with very short duration
        issued = self.license_service.issue_license(
            customer_id="test-expire",
            duration_days=0,  # Expires immediately
            grace_days=0
        )
        
        # Wait a bit to ensure expiry
        time.sleep(1)
        
        # Verify it's expired
        response = self.license_service.verify_license(issued.license_key)
        assert response.valid is False
        assert "expired" in response.message.lower()
    
    def test_grace_period(self):
        """Test license grace period functionality"""
        import time
        
        # Issue a license with very short duration but grace period
        issued = self.license_service.issue_license(
            customer_id="test-grace",
            duration_days=0,  # Expires immediately
            grace_days=1  # 1 day grace
        )
        
        # Wait a bit to ensure expiry but within grace
        time.sleep(1)
        
        # Should still be valid due to grace period
        response = self.license_service.verify_license(issued.license_key)
        assert response.valid is True
        assert response.in_grace_period is True
        assert "grace period" in response.message.lower()


class TestLicenseClient:
    """Test cases for the LicenseClient integration"""
    
    def setup_method(self):
        """Set up test environment"""
        # Mock environment variables
        os.environ["LICENSE_KEY"] = ""  # Start with no license
        os.environ["LICENSE_API_URL"] = "http://localhost:8002"
        os.environ["LICENSE_VERIFY_INTERVAL"] = "60"  # 1 minute for testing
        
        self.license_client = LicenseClient()
    
    @pytest.mark.asyncio
    async def test_no_license_startup(self):
        """Test client behavior when no license is configured"""
        await self.license_client.start()
        
        assert self.license_client.is_licensed() is True  # Should allow operation without license
        
        status = self.license_client.get_status()
        assert status["status"] == "no_license_required"
        assert status["licensed"] is True
        
        await self.license_client.stop()
    
    @pytest.mark.asyncio
    async def test_invalid_license_startup(self):
        """Test client behavior with invalid license key"""
        os.environ["LICENSE_KEY"] = "invalid-license-key"
        client = LicenseClient()
        
        await client.start()
        
        # Should be locked due to invalid license
        assert client.is_licensed() is False
        
        status = client.get_status()
        assert status["status"] == LicenseStatus.LOCKED
        assert status["licensed"] is False
        
        await client.stop()
        
        # Clean up
        os.environ["LICENSE_KEY"] = ""
    
    def test_device_id_generation(self):
        """Test device ID generation and persistence"""
        client1 = LicenseClient()
        client2 = LicenseClient()
        
        # Both clients should get the same device ID (persisted)
        assert client1.device_id == client2.device_id
        assert len(client1.device_id) == 36  # UUID format


def run_license_tests():
    """Run all license system tests"""
    print("🧪 Running Phase 5 License System Tests...")
    
    # Test LicenseService
    print("\n📋 Testing LicenseService...")
    service_test = TestLicenseService()
    
    try:
        service_test.setup_method()
        service_test.test_issue_license()
        print("✅ License issuance: PASS")
    except Exception as e:
        print(f"❌ License issuance: FAIL - {e}")
    
    try:
        service_test.setup_method()
        service_test.test_verify_valid_license()
        print("✅ Valid license verification: PASS")
    except Exception as e:
        print(f"❌ Valid license verification: FAIL - {e}")
    
    try:
        service_test.setup_method()
        service_test.test_verify_invalid_license()
        print("✅ Invalid license verification: PASS")
    except Exception as e:
        print(f"❌ Invalid license verification: FAIL - {e}")
    
    try:
        service_test.setup_method()
        service_test.test_revoke_license()
        print("✅ License revocation: PASS")
    except Exception as e:
        print(f"❌ License revocation: FAIL - {e}")
    
    try:
        service_test.setup_method()
        service_test.test_grace_period()
        print("✅ Grace period functionality: PASS")
    except Exception as e:
        print(f"❌ Grace period functionality: FAIL - {e}")
    
    # Test LicenseClient
    print("\n🔗 Testing LicenseClient...")
    client_test = TestLicenseClient()
    
    try:
        client_test.setup_method()
        asyncio.run(client_test.test_no_license_startup())
        print("✅ No license startup: PASS")
    except Exception as e:
        print(f"❌ No license startup: FAIL - {e}")
    
    try:
        client_test.setup_method()
        asyncio.run(client_test.test_invalid_license_startup())
        print("✅ Invalid license handling: PASS")
    except Exception as e:
        print(f"❌ Invalid license handling: FAIL - {e}")
    
    try:
        client_test.setup_method()
        client_test.test_device_id_generation()
        print("✅ Device ID generation: PASS")
    except Exception as e:
        print(f"❌ Device ID generation: FAIL - {e}")
    
    print("\n🎉 License system tests completed!")


if __name__ == "__main__":
    run_license_tests()