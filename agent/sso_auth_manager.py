"""
SSO Authentication Manager for AccessibilityTestingAgent
Based on VisualTestingAgent's successful SSO implementation with session sharing
"""

import asyncio
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from playwright.async_api import Browser, BrowserContext, Page
from urllib.parse import urlparse

from .mfa_templates import MFATemplates
from .certificate_handler import CertificateDialogHandler


@dataclass
class AuthResult:
    """Result of authentication attempt"""
    success: bool
    template_name: str
    authenticated_context: Optional[BrowserContext] = None
    error_message: Optional[str] = None


class SSOAuthManager:
    """
    SSO Authentication Manager with single browser session sharing
    Based on VisualTestingAgent's successful implementation
    """
    
    def __init__(self):
        self.templates = MFATemplates.get_templates()
        self.browser: Optional[Browser] = None
        self.authenticated_contexts: Dict[str, BrowserContext] = {}
        self.authenticated_templates: set = set()
        self.shared_context: Optional[BrowserContext] = None
        self.certificate_handler = CertificateDialogHandler()
        
        # URL categorization patterns (same as VisualTestingAgent)
        self.private_domain_patterns = [
            r'.*\.dev\..*',           # Development environments
            r'.*\.internal\..*',      # Internal domains
            r'.*\.corp\..*',          # Corporate domains
            r'.*\.enterprise\..*',    # Enterprise domains
            r'feature\..*',           # Feature branches
            r'staging\..*',           # Staging environments
            r'test\..*',              # Test environments
            r'.*\.onmicrosoft\.com',  # Azure AD domains
            r'.*\.sharepoint\.com',   # SharePoint
            r'.*\.teams\.microsoft\.com',  # Teams
            r'.*\.lilly\.com',        # Lilly domains
            r'.*\.elililly\..*'       # Eli Lilly domains
        ]

    async def initialize(self, browser: Browser):
        """Initialize the auth manager with a browser instance"""
        self.browser = browser
        print("🔐 SSO Auth Manager initialized with browser")

    async def categorize_urls(self, urls: List[str]) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Categorize URLs into public and private groups
        Returns: (public_urls, {template_name: [private_urls]})
        """
        public_urls = []
        private_groups = {}
        
        for url in urls:
            template_name = self._identify_auth_template(url)
            
            if template_name:
                if template_name not in private_groups:
                    private_groups[template_name] = []
                private_groups[template_name].append(url)
                print(f"🔒 Private URL detected: {url} -> {template_name}")
            else:
                public_urls.append(url)
                print(f"🌐 Public URL: {url}")
        
        print(f"\n📊 URL Categorization Summary:")
        print(f"   Public URLs: {len(public_urls)}")
        for template, urls_list in private_groups.items():
            print(f"   {template}: {len(urls_list)} URLs")
        
        return public_urls, private_groups

    def _identify_auth_template(self, url: str) -> Optional[str]:
        """Identify which authentication template to use for a URL"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check if URL matches any private domain patterns
        for pattern in self.private_domain_patterns:
            if re.match(pattern, domain):
                # Find matching template based on domain
                for template_name, template in self.templates.items():
                    # Check if template has domain-specific patterns
                    if template_name == "lilly" and ("lilly" in domain or "elililly" in domain):
                        return template_name
                    elif template_name == "okta" and "okta" in domain:
                        return template_name
                    elif template_name == "azure-ad" and ("microsoftonline" in domain or "microsoft" in domain):
                        return template_name
                
                # Default to first available template for private domains
                if self.templates:
                    return "lilly"  # Default to Lilly for this implementation
        
        return None

    async def authenticate_with_template(self, template_name: str, context_options: Dict[str, Any] = None) -> AuthResult:
        """Authenticate using the specified template with session sharing and device-specific configuration"""
        if template_name in self.authenticated_templates:
            print(f"✅ Already authenticated with {template_name}")
            return AuthResult(
                success=True,
                template_name=template_name,
                authenticated_context=self.authenticated_contexts.get(template_name)
            )

        if not self.browser:
            return AuthResult(
                success=False,
                template_name=template_name,
                error_message="Browser not initialized"
            )

        template = self.templates.get(template_name)
        if not template:
            return AuthResult(
                success=False,
                template_name=template_name,
                error_message=f"Template '{template_name}' not found"
            )

        try:
            print(f"🔐 Starting authentication with {template['projectName']}...")
            
            # Create or reuse shared context with device-specific configuration
            if not self.shared_context:
                # Use provided context options or default to desktop
                if context_options:
                    self.shared_context = await self.browser.new_context(**context_options)
                    device_info = f"{context_options.get('viewport', {}).get('width', '?')}x{context_options.get('viewport', {}).get('height', '?')}"
                    mobile_status = "📱 Mobile" if context_options.get('is_mobile') else "🖥️ Desktop"
                    print(f"🆕 Created new shared browser context ({mobile_status} - {device_info})")
                else:
                    self.shared_context = await self.browser.new_context(
                        viewport={'width': 1280, 'height': 720},
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    )
                    print("🆕 Created new shared browser context (Desktop)")
            
            # Create a new page for authentication
            auth_page = await self.shared_context.new_page()
            
            # Navigate to login URL
            login_url = template['authFlow']['loginUrl']
            print(f"🌐 Navigating to: {login_url}")
            await auth_page.goto(login_url, wait_until="networkidle", timeout=60000)
            
            # Perform authentication
            auth_success = await self._perform_authentication(auth_page, template)
            
            if auth_success:
                self.authenticated_templates.add(template_name)
                self.authenticated_contexts[template_name] = self.shared_context
                
                print(f"✅ Authentication successful for {template_name}")
                return AuthResult(
                    success=True,
                    template_name=template_name,
                    authenticated_context=self.shared_context
                )
            else:
                await auth_page.close()
                return AuthResult(
                    success=False,
                    template_name=template_name,
                    error_message="Authentication failed"
                )

        except Exception as e:
            print(f"❌ Authentication error for {template_name}: {e}")
            return AuthResult(
                success=False,
                template_name=template_name,
                error_message=str(e)
            )

    async def _perform_authentication(self, page: Page, template: Dict[str, Any]) -> bool:
        """Perform the actual authentication steps"""
        try:
            credentials = template['credentials']
            selectors = template['selectors']
            mfa_config = template['mfaConfig']
            
            # Step 1: Enter username
            print("📝 Entering username...")
            username_field = page.locator(selectors['usernameField']).first
            await username_field.fill(credentials['username'])
            
            # Click Next/Submit button
            next_button = page.locator(selectors['nextButton']).first
            await next_button.click()
            await asyncio.sleep(1)  # Reduced from 2 to 1 second
            
            # Step 2: Enter password
            print("🔑 Entering password...")
            await page.wait_for_selector(selectors['passwordField'], timeout=30000)
            password_field = page.locator(selectors['passwordField']).first
            await password_field.fill(credentials['password'])
            
            # Click Submit button
            submit_button = page.locator(selectors['submitButton']).first
            await submit_button.click()
            
            # Step 3: Handle certificate dialog (crucial for Lilly SSO)
            print("🔒 Checking for certificate dialogs...")
            await asyncio.sleep(2)  # Reduced from 3 to 2 seconds
            await self.certificate_handler.handle_certificate_with_automation(page)
            
            # Step 4: Handle MFA (if required)
            if mfa_config.get('skipMFA', False) and mfa_config.get('automatedFlow', False):
                print("🤖 Using service account - MFA should be bypassed...")
                
                # Wait for authentication to complete
                success_patterns = template['authFlow']['successPatterns']
                auth_completed = False
                
                # Quick check: see if we're already on a success URL
                await asyncio.sleep(1)  # Brief wait for redirect to start
                current_url = page.url
                print(f"🔍 Current URL: {current_url}")
                
                # Check domain first (fastest check)
                if any(domain in current_url for domain in ['feature.dev.chat.lilly.com', 'cortex']):
                    print(f"✅ Authentication successful - on target domain: {current_url}")
                    auth_completed = True
                
                # Try pattern matching with reduced timeout if not already completed
                if not auth_completed:
                    for pattern in success_patterns:
                        try:
                            url_pattern = pattern.replace('**/', '').replace('**', '')
                            print(f"⏳ Waiting for redirect to: {url_pattern}")
                            
                            # Reduced timeout to 8 seconds for faster failure
                            await page.wait_for_url(f"*{url_pattern}*", timeout=8000)
                            print(f"✅ Successfully redirected to: {page.url}")
                            auth_completed = True
                            break
                            
                        except Exception as e:
                            # Check if we're already on the right page despite timeout
                            current_url = page.url
                            if url_pattern in current_url:
                                print(f"✅ Already on target URL: {current_url}")
                                auth_completed = True
                                break
                            continue
                
                # Final check: are we past login pages?
                if not auth_completed:
                    current_url = page.url
                    print(f"🔍 Final check - current URL: {current_url}")
                    
                    # Check if we're past login pages
                    if 'login.microsoftonline.com' not in current_url and 'microsoftonline.com' not in current_url:
                        # Just check DOM content loaded, no need for networkidle
                        try:
                            await page.wait_for_load_state('domcontentloaded', timeout=5000)
                        except:
                            pass  # Don't fail if timeout, we're already past login
                        
                        print("✅ Authentication successful - moved past login pages")
                        auth_completed = True
                    else:
                        print("❌ Still on login page - authentication may have failed")
                
                return auth_completed
            else:
                print("⚠️ MFA handling not implemented for non-service accounts")
                return False
                
        except Exception as e:
            print(f"❌ Authentication step failed: {e}")
            return False

    async def create_authenticated_page(self, template_name: str) -> Optional[Page]:
        """Create a new page in the authenticated context"""
        context = self.authenticated_contexts.get(template_name)
        if not context:
            print(f"❌ No authenticated context found for {template_name}")
            return None
        
        try:
            page = await context.new_page()
            print(f"✅ Created new authenticated page for {template_name}")
            return page
        except Exception as e:
            print(f"❌ Failed to create authenticated page: {e}")
            return None

    async def navigate_with_auth(self, url: str) -> Tuple[Optional[Page], bool]:
        """Navigate to URL, handling authentication if needed"""
        template_name = self._identify_auth_template(url)
        
        if template_name:
            # Private URL - needs authentication
            if template_name not in self.authenticated_templates:
                auth_result = await self.authenticate_with_template(template_name)
                if not auth_result.success:
                    print(f"❌ Authentication failed for {url}")
                    return None, True
            
            # Create authenticated page
            page = await self.create_authenticated_page(template_name)
            return page, True
        else:
            # Public URL - create regular page
            if not self.shared_context:
                self.shared_context = await self.browser.new_context()
            
            page = await self.shared_context.new_page()
            return page, False

    async def cleanup(self):
        """Clean up authentication manager resources"""
        try:
            # Close authenticated contexts
            for context in self.authenticated_contexts.values():
                if context:
                    await context.close()
            
            # Close shared context
            if self.shared_context:
                await self.shared_context.close()
            
            print("✅ SSO Auth Manager cleanup completed")
            
        except Exception as e:
            print(f"⚠️ Error during SSO auth manager cleanup: {e}")
