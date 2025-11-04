"""
Certificate Dialog Handler for AccessibilityTestingAgent SSO
Handles both web-based and native OS certificate acceptance dialogs
Based on VisualTestingAgent's successful implementation
"""

import asyncio
import subprocess
import os
from typing import Optional
from playwright.async_api import Page

class CertificateDialogHandler:
    """Handle certificate dialogs during SSO authentication"""
    
    def __init__(self):
        self.script_path = os.path.join(
            os.path.dirname(__file__), 
            'scripts', 
            'handleCertificateDialog.scpt'
        )

    async def handle_certificate_with_automation(self, page: Page) -> bool:
        """
        Enhanced certificate handling with both native OS and web dialog support
        """
        print("🔒 Checking for certificate dialogs (native OS + web)...")
        
        # First, try to handle native OS certificate dialog with AppleScript (if on macOS)
        native_handled = False
        if os.name == 'posix':  # Unix-like systems (macOS, Linux)
            native_handled = await self._handle_native_os_certificate_dialog()
        
        # Then handle any web-based certificate dialogs
        web_handled = await self._handle_web_certificate_dialog(page)
        
        return native_handled or web_handled

    async def _handle_native_os_certificate_dialog(self) -> bool:
        """Handle native OS certificate dialog using AppleScript (macOS only)"""
        try:
            print("🤖 Attempting to handle native OS certificate dialog with AppleScript...")
            
            # Check if AppleScript file exists
            if not os.path.exists(self.script_path):
                print(f"⚠️ AppleScript file not found: {self.script_path}")
                return False
            
            # Run the AppleScript
            process = await asyncio.create_subprocess_exec(
                'osascript', self.script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if stderr:
                stderr_str = stderr.decode()
                if 'osascript is not allowed to send keystrokes' in stderr_str:
                    print("⚠️ AppleScript accessibility permissions not granted")
                    print("💡 To enable: System Preferences > Security & Privacy > Privacy > Accessibility > Terminal")
                    return False
                else:
                    print(f"⚠️ AppleScript warning: {stderr_str}")
            
            print("✅ Native certificate dialog handling completed automatically")
            if stdout:
                print(f"📝 AppleScript output: {stdout.decode().strip()}")
            
            # Give time for certificate processing to complete
            await asyncio.sleep(3)
            
            return True
            
        except Exception as e:
            error_message = str(e)
            if 'osascript is not allowed to send keystrokes' in error_message:
                print("⚠️ AppleScript accessibility permissions not granted")
                print("💡 To enable: System Preferences > Security & Privacy > Privacy > Accessibility > Terminal")
            else:
                print(f"⚠️ AppleScript certificate handling failed: {error_message}")
            
            print("🔄 Will try web-based certificate dialog handling...")
            return False

    async def _handle_web_certificate_dialog(self, page: Page) -> bool:
        """Handle certificate acceptance dialog with comprehensive detection"""
        print("🔒 Checking for certificate acceptance dialog...")
        
        # Check if page is still accessible
        try:
            await page.evaluate('document.readyState')
        except Exception:
            print("⚠️ Page is not accessible - may have been closed or navigated")
            return False

        # Extended certificate dialog selectors
        certificate_selectors = [
            # Microsoft Azure/Office 365 certificate dialogs
            "button:has-text('Continue')",
            "button:has-text('Accept')",
            "button:has-text('Yes')",
            "button:has-text('Allow')",
            "input[type='button'][value='Continue']",
            "input[type='button'][value='Accept']",
            "input[type='button'][value='Yes']",
            "input[type='submit'][value='Continue']",
            "input[type='submit'][value='Accept']",
            
            # Generic certificate acceptance buttons
            "[id*='accept'], [id*='continue'], [id*='allow']",
            "[class*='accept'], [class*='continue'], [class*='allow']",
            "button[data-testid*='accept']",
            "button[data-testid*='continue']",
            
            # Certificate-specific selectors
            "button:has-text('Install certificate')",
            "button:has-text('Trust certificate')",
            "input[value*='certificate']",
            
            # Common dialog patterns
            ".modal button:has-text('OK')",
            ".dialog button:has-text('OK')",
            ".popup button:has-text('Continue')"
        ]

        try:
            # Wait for potential certificate dialog with shorter timeout
            await asyncio.sleep(2)
            
            # Check for certificate dialog elements
            for selector in certificate_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=1000):
                        print(f"✅ Found certificate dialog button: {selector}")
                        await element.click()
                        print("✅ Certificate dialog accepted")
                        
                        # Wait for dialog to close
                        await asyncio.sleep(2)
                        return True
                        
                except Exception:
                    continue  # Try next selector
            
            # Check for text-based certificate dialogs
            certificate_text_patterns = [
                "certificate",
                "security warning", 
                "untrusted",
                "continue anyway",
                "proceed",
                "accept risk"
            ]
            
            page_content = await page.content()
            for pattern in certificate_text_patterns:
                if pattern.lower() in page_content.lower():
                    print(f"🔍 Detected certificate-related content: {pattern}")
                    
                    # Try to find and click continue/accept buttons
                    continue_buttons = [
                        "button:has-text('Continue')",
                        "button:has-text('Proceed')", 
                        "button:has-text('Accept')",
                        "input[value='Continue']",
                        "input[value='Proceed']"
                    ]
                    
                    for button_selector in continue_buttons:
                        try:
                            button = page.locator(button_selector).first
                            if await button.is_visible(timeout=1000):
                                await button.click()
                                print(f"✅ Clicked certificate continue button: {button_selector}")
                                await asyncio.sleep(2)
                                return True
                        except Exception:
                            continue
            
            print("ℹ️ No certificate dialog detected")
            return False
            
        except Exception as e:
            print(f"⚠️ Error handling certificate dialog: {e}")
            return False

    async def wait_for_navigation_after_certificate(self, page: Page, timeout: int = 30000) -> bool:
        """Wait for page navigation after certificate handling"""
        try:
            print("⏳ Waiting for navigation after certificate handling...")
            
            # Wait for either navigation or specific success indicators
            await asyncio.wait_for(
                page.wait_for_load_state('networkidle'),
                timeout=timeout/1000
            )
            
            print("✅ Navigation completed after certificate handling")
            return True
            
        except asyncio.TimeoutError:
            print("⚠️ Timeout waiting for navigation after certificate")
            return False
        except Exception as e:
            print(f"⚠️ Error waiting for navigation: {e}")
            return False
