"""
MFA Templates Configuration for AccessibilityTestingAgent
Based on VisualTestingAgent's successful SSO implementation
"""

import os
from typing import Dict, Any

class MFATemplates:
    """
    MFA template configurations for different authentication providers
    """
    
    @staticmethod
    def get_templates() -> Dict[str, Dict[str, Any]]:
        """
        Get all available MFA templates
        """
        return {
            "lilly": {
                "projectName": "Eli Lilly and Company",
                "mfaProvider": "microsoft-authenticator",
                "authFlow": {
                    "loginUrl": "https://feature.dev.chat.lilly.com/",
                    "redirectPatterns": [
                        "**/login.microsoftonline.com/**", 
                        "**/18a59a81-eea8-4c30-948a-d8824cdc2580/**"
                    ],
                    "successPatterns": [
                        "**/feature.dev.chat.lilly.com/**", 
                        "**/cortex/chat/**",
                        "**/cortex/dashboard/**",
                        "**/cortex/**"
                    ]
                },
                "credentials": {
                    "username": os.getenv("AUTOMATION_EMAIL", "SPE_AUTOMATION_ACC@elililly.onmicrosoft.com"),
                    "password": os.getenv("SSO_PASSWORD", "-Br985sGo6P,;E#V"),
                    "domain": "elililly.onmicrosoft.com",
                    "accountType": "service",
                    "automationEnabled": True
                },
                "mfaConfig": {
                    "type": "service-account",
                    "method": "automated-credentials",
                    "waitTime": 30000,
                    "pollInterval": 1000,
                    "description": "Service account auto-login with predefined credentials",
                    "skipMFA": True,
                    "automatedFlow": True
                },
                "selectors": {
                    "usernameField": "input[name='loginfmt'], input[id='i0116'], input[type='email']",
                    "passwordField": "input[name='passwd'], input[id='i0118'], input[type='password']",
                    "mfaField": "input[name='otc'], input[id='idTxtBx_SAOTCC_OTC']",
                    "submitButton": "input[type='submit'], input[id='idSIButton9']",
                    "nextButton": "input[id='idSIButton9']",
                    "mfaChoice": "div[data-value='PhoneAppNotification'], a[data-value='PhoneAppNotification']"
                }
            },
            
            "okta": {
                "projectName": "Okta Enterprise SSO",
                "mfaProvider": "okta-verify",
                "authFlow": {
                    "loginUrl": "https://{org}.okta.com/oauth2/v1/authorize",
                    "redirectPatterns": ["**/okta.com/**"],
                    "successPatterns": ["**/app.okta.com/**"]
                },
                "credentials": {
                    "username": os.getenv("OKTA_USERNAME", "user@company.com"),
                    "password": os.getenv("OKTA_PASSWORD", "your-password")
                },
                "mfaConfig": {
                    "type": "totp",
                    "secret": os.getenv("OKTA_MFA_SECRET", "OKTA_MFA_SECRET_BASE32_KEY"),
                    "digits": 6,
                    "period": 30
                },
                "selectors": {
                    "usernameField": "#okta-signin-username",
                    "passwordField": "#okta-signin-password",
                    "mfaField": "input[name='answer']",
                    "submitButton": "#okta-signin-submit",
                    "mfaChoice": "a[data-se='factor-question']"
                }
            },
            
            "azure-ad": {
                "projectName": "Microsoft Azure AD",
                "mfaProvider": "microsoft-authenticator",
                "authFlow": {
                    "loginUrl": "https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize",
                    "redirectPatterns": ["**/login.microsoftonline.com/**"],
                    "successPatterns": ["**/portal.azure.com/**", "**/office.com/**"]
                },
                "credentials": {
                    "username": os.getenv("AZURE_USERNAME", "user@company.com"),
                    "password": os.getenv("AZURE_PASSWORD", "your-password")
                },
                "mfaConfig": {
                    "type": "totp",
                    "secret": os.getenv("AZURE_MFA_SECRET", "AZURE_AD_MFA_SECRET_BASE32_KEY"),
                    "digits": 6,
                    "period": 30
                },
                "selectors": {
                    "usernameField": "input[name='loginfmt']",
                    "passwordField": "input[name='passwd']", 
                    "mfaField": "input[name='otc']",
                    "submitButton": "input[type='submit']",
                    "nextButton": "input[type='submit'][value='Next']"
                }
            }
        }
    
    @staticmethod
    def get_template(name: str) -> Dict[str, Any]:
        """
        Get a specific MFA template by name
        """
        templates = MFATemplates.get_templates()
        if name not in templates:
            raise ValueError(f"MFA template '{name}' not found. Available: {list(templates.keys())}")
        return templates[name]
    
    @staticmethod
    def get_available_templates() -> list:
        """
        Get list of available template names
        """
        return list(MFATemplates.get_templates().keys())
