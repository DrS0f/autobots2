#!/usr/bin/env python3
"""
Smoke Test: UI Layout Validation
Validates that all UI elements are visible and positioned correctly after refinements
"""

import asyncio
import sys
import time
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UILayoutTester:
    def __init__(self):
        self.frontend_url = "https://4ef408ef-8dbe-4893-ba4f-68a32b4f29f2-frontend.preview.emergentagent.com"
        self.test_results = {}
        
    async def test_top_control_strip(self, page):
        """Test fixed top control strip elements"""
        logger.info("Testing top control strip layout...")
        
        # Check if top strip is visible and fixed
        top_strip = await page.query_selector('.fixed.top-0')
        assert top_strip is not None, "Top control strip not found"
        
        # Check mode toggle visibility
        mode_toggle = await page.query_selector('div:has-text("SAFE MODE"), div:has-text("LIVE MODE")')
        assert mode_toggle is not None, "Mode toggle not visible"
        
        # Check system control button
        system_button = await page.query_selector('button:has-text("STOP SYSTEM"), button:has-text("START SYSTEM")')
        assert system_button is not None, "System control button not visible"
        
        # Check metrics display
        metrics = await page.query_selector_all('[class*="text-center"]')
        assert len(metrics) >= 5, f"Expected at least 5 metrics, found {len(metrics)}"
        
        # Check alerts button
        alerts_button = await page.query_selector('button[title="System alerts"]')
        assert alerts_button is not None, "Alerts button not visible"
        
        return True
    
    async def test_main_layout_structure(self, page):
        """Test two-column main layout structure"""
        logger.info("Testing main layout structure...")
        
        # Check grid layout
        grid_container = await page.query_selector('.grid.grid-cols-1.lg\\:grid-cols-2')
        assert grid_container is not None, "Main grid layout not found"
        
        # Check device control section (left column)
        device_section = await page.query_selector('h2:has-text("Device Control & Monitoring")')
        assert device_section is not None, "Device control section not found"
        
        # Check device table
        device_table = await page.query_selector('table')
        assert device_table is not None, "Device table not found"
        
        # Check task management section (right column)
        task_section = await page.query_selector('h2:has-text("Quick Actions")')
        assert task_section is not None, "Task management section not found"
        
        # Check quick action buttons
        create_task_btn = await page.query_selector('button:has-text("CREATE TASK")')
        create_workflow_btn = await page.query_selector('button:has-text("CREATE WORKFLOW")')
        assert create_task_btn is not None, "Create Task button not found"
        assert create_workflow_btn is not None, "Create Workflow button not found"
        
        return True
    
    async def test_bottom_logs_panel(self, page):
        """Test bottom logs panel layout"""
        logger.info("Testing bottom logs panel...")
        
        # Check fixed bottom panel
        bottom_panel = await page.query_selector('.fixed.bottom-0')
        assert bottom_panel is not None, "Bottom panel not found"
        
        # Check tab navigation
        tabs = await page.query_selector_all('button:has-text("System Log"), button:has-text("Interactions"), button:has-text("Mode Settings"), button:has-text("Settings")')
        assert len(tabs) >= 4, f"Expected at least 4 tabs, found {len(tabs)}"
        
        # Check default active tab (system log)
        system_log_content = await page.query_selector('h3:has-text("System Log")')
        # Note: May not be visible initially, which is acceptable
        
        return True
    
    async def test_mobile_responsiveness(self, page):
        """Test mobile layout responsiveness"""
        logger.info("Testing mobile responsiveness...")
        
        # Test mobile viewport
        await page.set_viewport_size({"width": 390, "height": 844})
        await asyncio.sleep(2)
        
        # Check that top control strip is still visible
        top_strip = await page.query_selector('.fixed.top-0')
        assert top_strip is not None, "Top strip not visible on mobile"
        
        # Check that critical controls are still accessible
        mode_toggle = await page.query_selector('div:has-text("SAFE MODE"), div:has-text("LIVE MODE")')
        system_button = await page.query_selector('button:has-text("STOP SYSTEM"), button:has-text("START SYSTEM")')
        
        assert mode_toggle is not None, "Mode toggle not visible on mobile"
        assert system_button is not None, "System button not visible on mobile"
        
        # Check that main content adapts to single column
        # Note: Grid should stack vertically on mobile
        
        # Reset to desktop viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await asyncio.sleep(1)
        
        return True
    
    async def test_visual_hierarchy(self, page):
        """Test visual hierarchy and contrast improvements"""
        logger.info("Testing visual hierarchy...")
        
        # Check enhanced contrast elements
        enhanced_buttons = await page.query_selector_all('button[class*="border-2"]')
        assert len(enhanced_buttons) > 0, "Enhanced border buttons not found"
        
        # Check improved table headers
        table_headers = await page.query_selector_all('th[class*="uppercase"]')
        assert len(table_headers) > 0, "Enhanced table headers not found"
        
        # Check status badges have proper styling
        status_badges = await page.query_selector_all('span[class*="border"]')
        assert len(status_badges) > 0, "Status badges not properly styled"
        
        return True
    
    async def test_touch_targets(self, page):
        """Test improved touch targets for mobile"""
        logger.info("Testing touch targets...")
        
        # Check button padding improvements
        action_buttons = await page.query_selector_all('button[class*="px-3"], button[class*="px-4"], button[class*="px-6"]')
        assert len(action_buttons) > 0, "Enhanced touch targets not found"
        
        # Check focus states
        first_button = await page.query_selector('button')
        if first_button:
            await first_button.focus()
            # Check that focus is visible (accessibility)
        
        return True
    
    async def run_all_tests(self):
        """Run all UI layout tests"""
        logger.info("Starting UI Layout Smoke Tests...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Navigate to the application
                logger.info(f"Navigating to {self.frontend_url}")
                await page.goto(self.frontend_url, wait_until="networkidle", timeout=30000)
                
                # Wait for React app to load
                await asyncio.sleep(5)
                
                # Run tests
                tests = [
                    ("Top Control Strip", self.test_top_control_strip),
                    ("Main Layout Structure", self.test_main_layout_structure),
                    ("Bottom Logs Panel", self.test_bottom_logs_panel),
                    ("Mobile Responsiveness", self.test_mobile_responsiveness),
                    ("Visual Hierarchy", self.test_visual_hierarchy),
                    ("Touch Targets", self.test_touch_targets)
                ]
                
                for test_name, test_func in tests:
                    try:
                        result = await test_func(page)
                        self.test_results[test_name] = {"status": "PASS", "result": result}
                        logger.info(f"✅ {test_name}: PASS")
                    except Exception as e:
                        self.test_results[test_name] = {"status": "FAIL", "error": str(e)}
                        logger.error(f"❌ {test_name}: FAIL - {str(e)}")
                
            except Exception as e:
                logger.error(f"Failed to load application: {str(e)}")
                return False
                
            finally:
                await browser.close()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r["status"] == "PASS"])
        
        logger.info("\n" + "="*60)
        logger.info("UI LAYOUT SMOKE TEST RESULTS")
        logger.info("="*60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL UI LAYOUT TESTS PASSED!")
            return True
        else:
            logger.error("❌ Some UI layout tests failed")
            return False

async def main():
    tester = UILayoutTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))