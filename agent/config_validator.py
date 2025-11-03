"""
Configuration validator for the Accessibility Testing Agent.
Validates configuration before test execution.
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from .exceptions import ConfigurationError


class ConfigValidator:
    """Validates agent configuration."""
    
    VALID_BROWSERS = ['chromium', 'webkit', 'firefox']
    VALID_DEVICE_TYPES = ['desktop', 'mobile', 'tablet', 'mobile-ios', 'mobile-android', 'tablet-ios', 'tablet-android']
    VALID_REPORT_FORMATS = ['html', 'md', 'json', 'csv']
    VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    @staticmethod
    def validate_config(config: Any) -> List[str]:
        """
        Validate configuration object and return list of validation errors.
        
        Args:
            config: Configuration object to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate max_workers
        if hasattr(config, 'max_workers'):
            if not isinstance(config.max_workers, int):
                errors.append(f"max_workers must be an integer, got {type(config.max_workers).__name__}")
            elif config.max_workers < 1:
                errors.append(f"max_workers must be >= 1, got {config.max_workers}")
            elif config.max_workers > 20:
                errors.append(f"max_workers is too high ({config.max_workers}), recommended max is 20")
        
        # Validate max_pages
        if hasattr(config, 'max_pages'):
            if not isinstance(config.max_pages, int):
                errors.append(f"max_pages must be an integer, got {type(config.max_pages).__name__}")
            elif config.max_pages < 1:
                errors.append(f"max_pages must be >= 1, got {config.max_pages}")
        
        # Validate browser_types
        if hasattr(config, 'browser_types'):
            if not isinstance(config.browser_types, list):
                errors.append(f"browser_types must be a list, got {type(config.browser_types).__name__}")
            else:
                invalid_browsers = [b for b in config.browser_types if b not in ConfigValidator.VALID_BROWSERS]
                if invalid_browsers:
                    errors.append(f"Invalid browser types: {invalid_browsers}. Valid: {ConfigValidator.VALID_BROWSERS}")
        
        # Validate device_types
        if hasattr(config, 'device_types'):
            if not isinstance(config.device_types, list):
                errors.append(f"device_types must be a list, got {type(config.device_types).__name__}")
            elif not config.device_types:
                errors.append("device_types cannot be empty")
            else:
                invalid_devices = [d for d in config.device_types if d not in ConfigValidator.VALID_DEVICE_TYPES]
                if invalid_devices:
                    errors.append(f"Invalid device types: {invalid_devices}. Valid: {ConfigValidator.VALID_DEVICE_TYPES}")
        
        # Validate report_format
        if hasattr(config, 'report_format'):
            if config.report_format not in ConfigValidator.VALID_REPORT_FORMATS:
                errors.append(f"Invalid report_format: {config.report_format}. Valid: {ConfigValidator.VALID_REPORT_FORMATS}")
        
        # Validate results_folder
        if hasattr(config, 'results_folder'):
            try:
                results_path = Path(config.results_folder)
                if results_path.exists() and not results_path.is_dir():
                    errors.append(f"results_folder exists but is not a directory: {config.results_folder}")
            except Exception as e:
                errors.append(f"Invalid results_folder path: {config.results_folder} - {e}")
        
        # Validate base_url
        if hasattr(config, 'base_url'):
            if not config.base_url:
                errors.append("base_url cannot be empty")
            elif not config.base_url.startswith(('http://', 'https://')):
                errors.append(f"base_url must start with http:// or https://, got: {config.base_url}")
        
        # Validate SSO configuration
        if hasattr(config, 'use_sso') and config.use_sso:
            if hasattr(config, 'sso_provider') and not config.sso_provider:
                errors.append("sso_provider must be specified when use_sso is True")
        
        # Validate headless
        if hasattr(config, 'headless'):
            if not isinstance(config.headless, bool):
                errors.append(f"headless must be a boolean, got {type(config.headless).__name__}")
        
        # Validate parallel
        if hasattr(config, 'parallel'):
            if not isinstance(config.parallel, bool):
                errors.append(f"parallel must be a boolean, got {type(config.parallel).__name__}")
        
        # Validate concurrent tab limits
        if hasattr(config, 'max_concurrent_tabs'):
            if not isinstance(config.max_concurrent_tabs, int):
                errors.append(f"max_concurrent_tabs must be an integer, got {type(config.max_concurrent_tabs).__name__}")
            elif config.max_concurrent_tabs < 1:
                errors.append(f"max_concurrent_tabs must be >= 1, got {config.max_concurrent_tabs}")
        
        return errors
    
    @staticmethod
    def validate_and_raise(config: Any):
        """
        Validate configuration and raise ConfigurationError if invalid.
        
        Args:
            config: Configuration object to validate
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        errors = ConfigValidator.validate_config(config)
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ConfigurationError(error_message)
    
    @staticmethod
    def create_directories(config: Any):
        """
        Create necessary directories based on configuration.
        
        Args:
            config: Configuration object
        """
        if hasattr(config, 'results_folder'):
            Path(config.results_folder).mkdir(parents=True, exist_ok=True)
        
        # Create logs directory if logging is enabled
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def validate_csv_file(csv_path: str) -> List[str]:
        """
        Validate CSV file exists and has required columns.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not os.path.exists(csv_path):
            errors.append(f"CSV file not found: {csv_path}")
            return errors
        
        if not csv_path.endswith('.csv'):
            errors.append(f"File must be a CSV file: {csv_path}")
            return errors
        
        try:
            import csv
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                # Check for required columns
                required_columns = ['url']
                missing_columns = [col for col in required_columns if col not in headers]
                if missing_columns:
                    errors.append(f"CSV missing required columns: {missing_columns}")
                
                # Check for optional but recommended columns
                optional_columns = ['name', 'requiresAuth', 'mfaTemplate']
                missing_optional = [col for col in optional_columns if col not in headers]
                if missing_optional:
                    # This is a warning, not an error
                    pass
                
                # Validate that there's at least one row
                rows = list(reader)
                if not rows:
                    errors.append("CSV file is empty (no data rows)")
                
        except Exception as e:
            errors.append(f"Error reading CSV file: {e}")
        
        return errors
    
    @staticmethod
    def validate_device_profiles(device_profiles: Dict[str, Any]) -> List[str]:
        """
        Validate device profiles configuration.
        
        Args:
            device_profiles: Device profiles dictionary
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not isinstance(device_profiles, dict):
            errors.append(f"device_profiles must be a dictionary, got {type(device_profiles).__name__}")
            return errors
        
        required_keys = ['desktop', 'mobile', 'tablet']
        for key in required_keys:
            if key not in device_profiles:
                errors.append(f"device_profiles missing required key: {key}")
        
        # Validate each device profile has viewport
        for form_factor, profiles in device_profiles.items():
            if not isinstance(profiles, dict):
                continue
            
            for profile_name, profile_config in profiles.items():
                if isinstance(profile_config, dict):
                    for device_name, device_config in profile_config.items():
                        if 'viewport' not in device_config:
                            errors.append(f"Device profile {form_factor}.{profile_name}.{device_name} missing viewport")
        
        return errors
