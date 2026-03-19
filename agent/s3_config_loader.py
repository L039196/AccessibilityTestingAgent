"""
S3 Configuration Loader
Loads S3 configuration from config/s3_config.json and environment variables.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class S3ConfigLoader:
    """Loads and manages S3 configuration."""
    
    DEFAULT_CONFIG_PATH = "config/s3_config.json"
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load S3 configuration from file and environment variables.
        Environment variables take precedence over file configuration.
        
        Args:
            config_path: Path to s3_config.json (optional)
            
        Returns:
            Dictionary with S3 configuration
        """
        # Load from file
        config_file = config_path or S3ConfigLoader.DEFAULT_CONFIG_PATH
        file_config = S3ConfigLoader._load_from_file(config_file)
        
        # Override with environment variables
        env_config = S3ConfigLoader._load_from_env()
        
        # Merge configurations (env takes precedence)
        merged_config = {**file_config, **env_config}
        
        return merged_config
    
    @staticmethod
    def _load_from_file(config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                return S3ConfigLoader._get_default_config()
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Extract s3_config section
            s3_config = config.get('s3_config', {})
            aws_creds = config.get('aws_credentials', {})
            
            return {
                'enabled': s3_config.get('enabled', False),
                'bucket_name': s3_config.get('bucket_name', ''),
                'region': s3_config.get('region', 'us-east-1'),
                'auto_cleanup_local': s3_config.get('auto_cleanup_local', True),
                'presigned_url_expiry': s3_config.get('presigned_url_expiry_seconds', 604800),
                'use_env_credentials': aws_creds.get('use_environment_variables', True),
                'access_key_id': aws_creds.get('access_key_id', ''),
                'secret_access_key': aws_creds.get('secret_access_key', '')
            }
        
        except Exception as e:
            print(f"⚠️ Failed to load S3 config from {config_path}: {e}")
            return S3ConfigLoader._get_default_config()
    
    @staticmethod
    def _load_from_env() -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        
        # Check if S3 is enabled via environment
        if 'ENABLE_S3_STORAGE' in os.environ:
            config['enabled'] = os.getenv('ENABLE_S3_STORAGE', 'false').lower() == 'true'
        
        # Load AWS credentials from environment
        if 'AWS_ACCESS_KEY_ID' in os.environ:
            config['access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID')
        
        if 'AWS_SECRET_ACCESS_KEY' in os.environ:
            config['secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # Load S3 bucket configuration
        if 'S3_BUCKET_NAME' in os.environ:
            config['bucket_name'] = os.getenv('S3_BUCKET_NAME')
        
        if 'S3_REGION' in os.environ:
            config['region'] = os.getenv('S3_REGION')
        
        if 'S3_AUTO_CLEANUP_LOCAL' in os.environ:
            config['auto_cleanup_local'] = os.getenv('S3_AUTO_CLEANUP_LOCAL', 'true').lower() == 'true'
        
        if 'S3_PRESIGNED_URL_EXPIRY' in os.environ:
            try:
                config['presigned_url_expiry'] = int(os.getenv('S3_PRESIGNED_URL_EXPIRY'))
            except ValueError:
                pass
        
        return config
    
    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default S3 configuration."""
        return {
            'enabled': False,
            'bucket_name': '',
            'region': 'us-east-1',
            'auto_cleanup_local': True,
            'presigned_url_expiry': 604800,
            'use_env_credentials': True,
            'access_key_id': '',
            'secret_access_key': ''
        }
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate S3 configuration.
        
        Args:
            config: S3 configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not config.get('enabled'):
            return True, "S3 storage is disabled"
        
        # Check required fields
        if not config.get('bucket_name'):
            return False, "S3 bucket name is required when S3 storage is enabled"
        
        if not config.get('region'):
            return False, "S3 region is required"
        
        # Check credentials (if not using environment)
        if not config.get('use_env_credentials'):
            if not config.get('access_key_id'):
                return False, "AWS_ACCESS_KEY_ID is required"
            if not config.get('secret_access_key'):
                return False, "AWS_SECRET_ACCESS_KEY is required"
        
        return True, "Configuration is valid"
    
    @staticmethod
    def merge_with_agent_config(agent_config: Any, s3_config: Dict[str, Any]) -> Any:
        """
        Merge S3 configuration into agent Config object.
        
        Args:
            agent_config: Agent Config instance
            s3_config: S3 configuration dictionary
            
        Returns:
            Updated agent config
        """
        agent_config.enable_s3_storage = s3_config.get('enabled', False)
        agent_config.s3_bucket_name = s3_config.get('bucket_name', '')
        agent_config.s3_region = s3_config.get('region', 'us-east-1')
        agent_config.s3_auto_cleanup_local = s3_config.get('auto_cleanup_local', True)
        agent_config.s3_presigned_url_expiry = s3_config.get('presigned_url_expiry', 604800)
        
        return agent_config
