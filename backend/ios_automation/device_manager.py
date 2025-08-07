"""
iOS Device Management System
Handles device discovery, connection, and management for multiple iOS devices
"""

import asyncio
import subprocess
import logging
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import uuid
from appium import webdriver
from appium.options.ios import XCUITestOptions

logger = logging.getLogger(__name__)

class DeviceStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    BUSY = "busy"
    ERROR = "error"
    READY = "ready"

@dataclass
class IOSDevice:
    udid: str
    name: str
    ios_version: str
    status: DeviceStatus
    connection_port: int
    driver: Optional[webdriver.Remote] = None
    last_heartbeat: Optional[float] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None

class IOSDeviceManager:
    def __init__(self):
        self.devices: Dict[str, IOSDevice] = {}
        self.port_range_start = 8100
        self.max_devices = 50
        self.heartbeat_interval = 30  # seconds
        self.webdriver_agent_port_start = 8200

    async def discover_devices(self) -> List[IOSDevice]:
        """Discover connected iOS devices via USB"""
        try:
            # Use idevice_id to list connected iOS devices
            result = subprocess.run(['idevice_id', '-l'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logger.error(f"Failed to discover devices: {result.stderr}")
                return []

            device_udids = result.stdout.strip().split('\n')
            device_udids = [udid.strip() for udid in device_udids if udid.strip()]

            discovered_devices = []
            
            for i, udid in enumerate(device_udids):
                if udid and len(udid) > 20:  # Valid UDID length check
                    device_info = await self._get_device_info(udid)
                    if device_info:
                        port = self.port_range_start + i
                        device = IOSDevice(
                            udid=udid,
                            name=device_info.get('name', f'iPhone-{udid[:8]}'),
                            ios_version=device_info.get('ios_version', 'Unknown'),
                            status=DeviceStatus.CONNECTED,
                            connection_port=port,
                            last_heartbeat=time.time()
                        )
                        discovered_devices.append(device)
                        self.devices[udid] = device
                        logger.info(f"Discovered device: {device.name} ({device.udid})")

            return discovered_devices

        except subprocess.TimeoutExpired:
            logger.error("Device discovery timed out")
            return []
        except Exception as e:
            logger.error(f"Error discovering devices: {e}")
            return []

    async def _get_device_info(self, udid: str) -> Optional[Dict]:
        """Get device information using ideviceinfo"""
        try:
            result = subprocess.run(['ideviceinfo', '-u', udid, '-k', 'DeviceName'], 
                                  capture_output=True, text=True, timeout=5)
            device_name = result.stdout.strip() if result.returncode == 0 else 'Unknown'
            
            result = subprocess.run(['ideviceinfo', '-u', udid, '-k', 'ProductVersion'], 
                                  capture_output=True, text=True, timeout=5)
            ios_version = result.stdout.strip() if result.returncode == 0 else 'Unknown'
            
            return {
                'name': device_name,
                'ios_version': ios_version
            }
        except Exception as e:
            logger.error(f"Error getting device info for {udid}: {e}")
            return None

    async def initialize_device(self, udid: str) -> bool:
        """Initialize Appium connection for a device"""
        device = self.devices.get(udid)
        if not device:
            logger.error(f"Device {udid} not found")
            return False

        try:
            # WebDriverAgent port for this device
            wda_port = self.webdriver_agent_port_start + len(self.devices)
            
            options = XCUITestOptions()
            options.udid = device.udid
            options.platform_name = "iOS"
            options.platform_version = device.ios_version
            options.device_name = device.name
            options.automation_name = "XCUITest"
            options.bundle_id = "com.burbn.instagram"
            options.no_reset = True
            options.full_reset = False
            options.new_command_timeout = 300
            options.wda_local_port = wda_port
            options.use_new_wda = False
            options.should_use_singleton_test_manager = False
            
            # Additional capabilities for better stability
            options.set_capability("mjpegServerPort", device.connection_port + 100)
            options.set_capability("clearSystemFiles", False)
            options.set_capability("preventWDAAttachments", True)
            
            # Create driver with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    driver = webdriver.Remote(
                        f"http://localhost:4723/wd/hub",
                        options=options
                    )
                    
                    # Test connection
                    driver.get_window_size()
                    
                    device.driver = driver
                    device.status = DeviceStatus.READY
                    device.session_id = driver.session_id
                    device.last_heartbeat = time.time()
                    
                    logger.info(f"Successfully initialized device {device.name} ({udid})")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for device {udid}: {e}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Failed to initialize device {udid}: {e}")
            device.status = DeviceStatus.ERROR
            device.error_message = str(e)
            return False

    async def get_available_device(self) -> Optional[IOSDevice]:
        """Get the first available device for automation"""
        for device in self.devices.values():
            if device.status == DeviceStatus.READY and device.driver:
                device.status = DeviceStatus.BUSY
                return device
        return None

    async def release_device(self, udid: str):
        """Release device back to ready state"""
        device = self.devices.get(udid)
        if device and device.status == DeviceStatus.BUSY:
            device.status = DeviceStatus.READY
            device.last_heartbeat = time.time()
            logger.info(f"Released device {device.name}")

    async def cleanup_device(self, udid: str):
        """Cleanup device driver and reset status"""
        device = self.devices.get(udid)
        if device and device.driver:
            try:
                device.driver.quit()
            except Exception as e:
                logger.warning(f"Error cleaning up device {udid}: {e}")
            
            device.driver = None
            device.session_id = None
            device.status = DeviceStatus.CONNECTED

    async def heartbeat_check(self):
        """Check device heartbeat and reconnect if needed"""
        current_time = time.time()
        
        for udid, device in list(self.devices.items()):
            if device.last_heartbeat and (current_time - device.last_heartbeat) > self.heartbeat_interval * 2:
                logger.warning(f"Device {device.name} missed heartbeat, checking connection")
                
                try:
                    if device.driver:
                        device.driver.get_window_size()  # Simple connectivity test
                        device.last_heartbeat = current_time
                    else:
                        # Try to reinitialize
                        await self.initialize_device(udid)
                except Exception as e:
                    logger.error(f"Device {device.name} is unresponsive: {e}")
                    device.status = DeviceStatus.ERROR
                    device.error_message = str(e)

    def get_device_status(self) -> Dict:
        """Get status of all devices"""
        return {
            "total_devices": len(self.devices),
            "ready_devices": len([d for d in self.devices.values() if d.status == DeviceStatus.READY]),
            "busy_devices": len([d for d in self.devices.values() if d.status == DeviceStatus.BUSY]),
            "error_devices": len([d for d in self.devices.values() if d.status == DeviceStatus.ERROR]),
            "devices": [
                {
                    "udid": device.udid,
                    "name": device.name,
                    "ios_version": device.ios_version,
                    "status": device.status.value,
                    "connection_port": device.connection_port,
                    "session_id": device.session_id,
                    "error_message": device.error_message
                }
                for device in self.devices.values()
            ]
        }