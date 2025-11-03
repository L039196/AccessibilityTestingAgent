"""
Custom exceptions for the Accessibility Testing Agent.
Provides fine-grained error categorization for better error handling.
"""

class AccessibilityAgentError(Exception):
    """Base exception for all agent errors."""
    pass


class AuthenticationError(AccessibilityAgentError):
    """Authentication-related errors (SSO, MFA, etc.)."""
    def __init__(self, message: str, provider: str = None, details: dict = None):
        self.provider = provider
        self.details = details or {}
        super().__init__(message)


class NavigationError(AccessibilityAgentError):
    """Page navigation errors (timeouts, DNS, network issues)."""
    def __init__(self, message: str, url: str = None, status_code: int = None):
        self.url = url
        self.status_code = status_code
        super().__init__(message)


class AnalysisError(AccessibilityAgentError):
    """Accessibility analysis errors (axe-core failures, etc.)."""
    def __init__(self, message: str, url: str = None, analyzer: str = "axe-core"):
        self.url = url
        self.analyzer = analyzer
        super().__init__(message)


class ScreenshotError(AccessibilityAgentError):
    """Screenshot capture errors."""
    def __init__(self, message: str, url: str = None, element: str = None):
        self.url = url
        self.element = element
        super().__init__(message)


class ConfigurationError(AccessibilityAgentError):
    """Configuration validation errors."""
    def __init__(self, message: str, field: str = None, value: any = None):
        self.field = field
        self.value = value
        super().__init__(message)


class BrowserError(AccessibilityAgentError):
    """Browser launch/management errors."""
    def __init__(self, message: str, browser_type: str = None):
        self.browser_type = browser_type
        super().__init__(message)


class ReportGenerationError(AccessibilityAgentError):
    """Report generation errors."""
    def __init__(self, message: str, report_type: str = None):
        self.report_type = report_type
        super().__init__(message)


class RetryableError(AccessibilityAgentError):
    """Base class for errors that should trigger a retry."""
    pass


class TransientNavigationError(NavigationError, RetryableError):
    """Temporary navigation error that may succeed on retry."""
    pass


class TransientAnalysisError(AnalysisError, RetryableError):
    """Temporary analysis error that may succeed on retry."""
    pass


class TransientBrowserError(BrowserError, RetryableError):
    """Temporary browser error that may succeed on retry."""
    pass
