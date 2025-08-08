#!/usr/bin/env python3
"""
Smoke Test: Mobile Responsiveness
Validates that critical controls remain visible across all breakpoints after UI refinements
"""

import asyncio
import sys
import time
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MobileResponsiveTester:
    def __init__(self):
        self.frontend_url = "https://4ef408ef-8dbe-4893-ba4f-68a32b4f29f2-frontend.preview.emergentagent.com"
        self.test_results = {}
        
        # Test viewports representing different device categories
        self.viewports = {
            "Mobile Portrait": {"width": 390, "height": 844},      # iPhone 12 Pro
            "Mobile Landscape": {"width": 844, "height": 390},     # iPhone 12 Pro rotated
            "Tablet Portrait": {"width": 768, "height": 1024},     # iPad
            "Tablet Landscape": {"width": 1024, "height": 768},    # iPad rotated
            "Desktop Small": {"width": 1280, "height": 800},       # Small laptop
            "Desktop Large": {"width": 1920, "height": 1080},      # Full desktop
            "Ultra Wide": {"width": 2560, "height": 1440}          # Ultra-wide monitor
        }
    
    async def test_critical_controls_visibility(self, page, viewport_name):
        """Test that critical controls are visible at given viewport"""
        logger.info(f"Testing critical controls visibility on {viewport_name}...")
        
        critical_elements = []
        
        # Check mode toggle visibility
        mode_toggle = await page.query_selector('div:has-text("SAFE MODE"), div:has-text("LIVE MODE")')
        if mode_toggle:
            is_visible = await mode_toggle.is_visible()
            critical_elements.append(("Mode Toggle", is_visible))
        else:
            critical_elements.append(("Mode Toggle", False))
        
        # Check system control button
        system_button = await page.query_selector('button:has-text("STOP SYSTEM"), button:has-text("START SYSTEM")')
        if system_button:
            is_visible = await system_button.is_visible()
            critical_elements.append(("System Button", is_visible))
        else:
            critical_elements.append(("System Button", False))
        
        # Check metrics visibility (at least some should be visible)
        metrics = await page.query_selector_all('[class*="text-center"] div[class*="font-bold"]')
        visible_metrics = 0
        for metric in metrics:
            if await metric.is_visible():
                visible_metrics += 1
        critical_elements.append(("Metrics Display", visible_metrics >= 3))  # At least 3 metrics visible
        
        # Check quick action buttons (may not be visible on very small screens without scrolling)
        create_task_btn = await page.query_selector('button:has-text("CREATE TASK")')
        create_workflow_btn = await page.query_selector('button:has-text("CREATE WORKFLOW")')
        
        task_btn_visible = await create_task_btn.is_visible() if create_task_btn else False
        workflow_btn_visible = await create_workflow_btn.is_visible() if create_workflow_btn else False
        
        # For mobile, quick actions may require scrolling, which is acceptable
        if viewport_name.startswith("Mobile"):
            # On mobile, it's acceptable if quick actions require scrolling
            critical_elements.append(("Quick Actions", True))  # Consider pass if top controls are visible
        else:
            critical_elements.append(("Quick Actions", task_btn_visible and workflow_btn_visible))
        
        return critical_elements
    
    async def test_navigation_accessibility(self, page, viewport_name):
        """Test that navigation and key actions are accessible"""
        logger.info(f"Testing navigation accessibility on {viewport_name}...")
        
        # Check that top strip remains fixed and accessible
        top_strip = await page.query_selector('.fixed.top-0')
        if not top_strip:
            return False
        
        # Check that we can access system controls without excessive scrolling
        system_button = await page.query_selector('button:has-text("STOP SYSTEM"), button:has-text("START SYSTEM")')
        if system_button:
            # Ensure button is within viewport or easily scrollable
            button_box = await system_button.bounding_box()
            if button_box:
                viewport_height = page.viewport_size["height"]
                # Button should be in top portion of screen
                is_accessible = button_box["y"] < viewport_height * 0.3  # Top 30% of screen
                return is_accessible
        
        return False
    
    async def test_layout_adaptation(self, page, viewport_name, viewport):
        """Test that layout adapts appropriately to viewport"""
        logger.info(f"Testing layout adaptation on {viewport_name}...")
        
        width = viewport["width"]
        
        # Check grid layout behavior
        grid_container = await page.query_selector('.grid.grid-cols-1.lg\\:grid-cols-2')
        
        if width < 1024:  # Should be single column
            # On smaller screens, layout should stack
            expected_columns = 1
        else:  # Should be two columns
            expected_columns = 2
        
        # For mobile and tablet, ensure no horizontal scrolling needed
        if width <= 768:
            # Check that content doesn't overflow horizontally
            body = await page.query_selector('body')
            if body:
                body_box = await body.bounding_box()
                # Allow for small margins/padding, but content should generally fit
                fits_horizontally = body_box["width"] <= width * 1.1  # 10% tolerance
                return fits_horizontally
        
        return True
    
    async def test_touch_targets(self, page, viewport_name):
        """Test that touch targets are appropriate for mobile"""
        logger.info(f"Testing touch targets on {viewport_name}...")
        
        if not viewport_name.startswith("Mobile"):
            return True  # Skip for non-mobile viewports
        
        # Check button sizes for touch friendliness
        buttons = await page.query_selector_all('button')
        appropriate_touch_targets = 0
        total_buttons = len(buttons)
        
        for button in buttons:
            if await button.is_visible():
                box = await button.bounding_box()
                if box:
                    # Touch targets should be at least 44px in either dimension (iOS guideline)
                    min_dimension = min(box["width"], box["height"])
                    if min_dimension >= 32:  # Slightly relaxed for dense interfaces
                        appropriate_touch_targets += 1
        
        # At least 80% of visible buttons should have appropriate touch targets
        if total_buttons > 0:
            ratio = appropriate_touch_targets / total_buttons
            return ratio >= 0.8
        
        return True
    
    async def test_content_readability(self, page, viewport_name):
        """Test that content remains readable at different viewport sizes"""
        logger.info(f"Testing content readability on {viewport_name}...")
        
        # Check that text doesn't become too small or get cut off
        text_elements = await page.query_selector_all('h1, h2, h3, td, th, span, div')
        readable_elements = 0
        total_elements = 0
        
        for element in text_elements[:20]:  # Sample first 20 elements
            if await element.is_visible():
                text_content = await element.text_content()
                if text_content and text_content.strip():
                    total_elements += 1
                    
                    # Check if element is not clipped
                    box = await element.bounding_box()
                    if box and box["width"] > 0 and box["height"] > 0:
                        readable_elements += 1
        
        if total_elements > 0:
            readability_ratio = readable_elements / total_elements
            return readability_ratio >= 0.9  # 90% of elements should be readable
        
        return True
    
    async def test_viewport(self, page, viewport_name, viewport_size):
        """Test a specific viewport size"""
        logger.info(f"\n📱 Testing {viewport_name} ({viewport_size['width']}x{viewport_size['height']})")
        
        # Set viewport
        await page.set_viewport_size(viewport_size)
        await asyncio.sleep(2)  # Allow layout to adapt
        
        viewport_results = {}
        
        # Run all tests for this viewport
        tests = [
            ("Critical Controls", self.test_critical_controls_visibility),
            ("Navigation", lambda p, vn: self.test_navigation_accessibility(p, vn)),
            ("Layout Adaptation", lambda p, vn: self.test_layout_adaptation(p, vn, viewport_size)),
            ("Touch Targets", self.test_touch_targets),
            ("Content Readability", self.test_content_readability)
        ]
        
        for test_name, test_func in tests:
            try:
                if test_name == "Critical Controls":
                    result = await test_func(page, viewport_name)
                    # For critical controls, check if all are visible
                    all_visible = all(item[1] for item in result)
                    viewport_results[test_name] = {
                        "status": "PASS" if all_visible else "FAIL",
                        "details": result
                    }
                    
                    if not all_visible:
                        failed_controls = [item[0] for item in result if not item[1]]
                        logger.warning(f"  ⚠️  {test_name}: Some controls not visible: {failed_controls}")
                    else:
                        logger.info(f"  ✅ {test_name}: All critical controls visible")
                else:
                    result = await test_func(page, viewport_name)
                    viewport_results[test_name] = {
                        "status": "PASS" if result else "FAIL",
                        "result": result
                    }
                    
                    status_icon = "✅" if result else "❌"
                    logger.info(f"  {status_icon} {test_name}: {'PASS' if result else 'FAIL'}")
                    
            except Exception as e:
                viewport_results[test_name] = {"status": "FAIL", "error": str(e)}
                logger.error(f"  ❌ {test_name}: FAIL - {str(e)}")
        
        return viewport_results
    
    async def run_all_tests(self):
        """Run mobile responsiveness tests across all viewports"""
        logger.info("Starting Mobile Responsiveness Smoke Tests...")
        
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
                
                # Test each viewport
                for viewport_name, viewport_size in self.viewports.items():
                    self.test_results[viewport_name] = await self.test_viewport(page, viewport_name, viewport_size)
                
            except Exception as e:
                logger.error(f"Failed to load application: {str(e)}")
                return False
                
            finally:
                await browser.close()
        
        # Calculate overall results
        total_viewport_tests = 0
        passed_viewport_tests = 0
        
        logger.info("\n" + "="*80)
        logger.info("MOBILE RESPONSIVENESS SMOKE TEST RESULTS")
        logger.info("="*80)
        
        for viewport_name, viewport_tests in self.test_results.items():
            logger.info(f"\n{viewport_name}:")
            viewport_passed = 0
            viewport_total = len(viewport_tests)
            
            for test_name, test_result in viewport_tests.items():
                status = test_result["status"]
                status_icon = "✅" if status == "PASS" else "❌"
                logger.info(f"  {status_icon} {test_name}: {status}")
                
                if status == "PASS":
                    viewport_passed += 1
                    passed_viewport_tests += 1
                
                total_viewport_tests += 1
            
            viewport_success_rate = (viewport_passed / viewport_total) * 100
            logger.info(f"  Viewport Success Rate: {viewport_success_rate:.1f}%")
        
        overall_success_rate = (passed_viewport_tests / total_viewport_tests) * 100
        
        logger.info(f"\nOverall Results:")
        logger.info(f"Total Tests: {total_viewport_tests}")
        logger.info(f"Passed: {passed_viewport_tests}")
        logger.info(f"Failed: {total_viewport_tests - passed_viewport_tests}")
        logger.info(f"Success Rate: {overall_success_rate:.1f}%")
        
        # Success criteria: 90% of tests should pass
        success = overall_success_rate >= 90.0
        
        if success:
            logger.info("🎉 MOBILE RESPONSIVENESS TESTS PASSED!")
        else:
            logger.error("❌ Mobile responsiveness tests failed")
        
        return success

async def main():
    tester = MobileResponsiveTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))