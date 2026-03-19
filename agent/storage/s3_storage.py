"""
AWS S3 Storage Integration for Accessibility Reports
Handles uploading reports, screenshots, and generating presigned URLs.
"""

import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class S3ReportStorage:
    """Handles uploading accessibility reports to AWS S3."""
    
    def __init__(
        self, 
        bucket_name: str,
        region: str = 'us-east-1',
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        session_token: Optional[str] = None
    ):
        """
        Initialize S3 storage.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key: AWS access key (optional, uses env if not provided)
            secret_key: AWS secret key (optional, uses env if not provided)
            session_token: AWS session token for temporary credentials (optional)
        """
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize S3 client
        try:
            if access_key and secret_key:
                # Build client parameters
                client_params = {
                    'region_name': region,
                    'aws_access_key_id': access_key,
                    'aws_secret_access_key': secret_key
                }
                
                # Add session token if provided (for temporary credentials)
                if session_token:
                    client_params['aws_session_token'] = session_token
                    logger.info("Using temporary AWS credentials with session token")
                
                self.s3_client = boto3.client('s3', **client_params)
            else:
                # Use credentials from environment or AWS config
                self.s3_client = boto3.client('s3', region_name=region)
            
            logger.info(f"✅ S3 client initialized for bucket: {bucket_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 client: {e}")
            raise
    
    def upload_report_folder(
        self,
        local_folder_path: str,
        user_id: str,
        session_id: str,
        device_type: str
    ) -> Dict[str, str]:
        """
        Upload entire report folder (HTML + screenshots) to S3.
        
        Args:
            local_folder_path: Path to local results folder
            user_id: User identifier
            session_id: Test session identifier
            device_type: Device type (desktop, mobile-ios, etc.)
            
        Returns:
            Dict with report URLs and metadata
        """
        timestamp = datetime.now().strftime('%Y-%m-%d')
        s3_prefix = f"sessions/{user_id}/{timestamp}-{session_id}/{device_type}/"
        
        uploaded_files = []
        screenshot_map = {}  # Map local paths to S3 URLs
        
        try:
            local_path = Path(local_folder_path)
            
            # STEP 1: Upload all files EXCEPT HTML (screenshots first)
            for file_path in local_path.rglob('*'):
                if file_path.is_file() and not file_path.suffix == '.html':
                    # Calculate relative path for S3 key
                    relative_path = file_path.relative_to(local_path)
                    s3_key = f"{s3_prefix}{relative_path}"
                    
                    # Determine content type
                    content_type = self._get_content_type(file_path.suffix)
                    
                    # Upload file
                    self.s3_client.upload_file(
                        str(file_path),
                        self.bucket_name,
                        s3_key,
                        ExtraArgs={'ContentType': content_type}
                    )
                    
                    uploaded_files.append({
                        'local_path': str(file_path),
                        's3_key': s3_key,
                        'size': file_path.stat().st_size
                    })
                    
                    # If it's a screenshot, generate presigned URL and store mapping
                    if file_path.suffix in ['.png', '.jpg', '.jpeg']:
                        presigned_url = self._generate_presigned_url(s3_key, expires_in=604800)
                        # Store both relative path formats
                        screenshot_map[str(relative_path)] = presigned_url
                        screenshot_map[str(relative_path).replace('\\', '/')] = presigned_url
                    
                    logger.debug(f"✅ Uploaded: {s3_key}")
            
            # STEP 2: Process HTML files - replace screenshot paths with S3 URLs
            html_files = []
            for file_path in local_path.rglob('*.html'):
                if file_path.is_file():
                    # Read HTML content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Replace screenshot paths with S3 presigned URLs
                    modified_html = self._replace_screenshot_paths(html_content, screenshot_map)
                    
                    # Calculate S3 key
                    relative_path = file_path.relative_to(local_path)
                    s3_key = f"{s3_prefix}{relative_path}"
                    
                    # Upload modified HTML to S3
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Body=modified_html.encode('utf-8'),
                        ContentType='text/html'
                    )
                    
                    uploaded_files.append({
                        'local_path': str(file_path),
                        's3_key': s3_key,
                        'size': len(modified_html.encode('utf-8'))
                    })
                    
                    html_files.append(s3_key)
                    logger.debug(f"✅ Uploaded (with fixed screenshot URLs): {s3_key}")
            
            # Find main HTML report
            if html_files:
                # Use the first HTML file found (main report)
                html_key = html_files[0]
            else:
                # Fallback to default name
                html_key = f"{s3_prefix}accessibility_report.html"
            
            # Generate presigned URL for main HTML report
            report_url = self._generate_presigned_url(html_key, expires_in=604800)  # 7 days
            
            logger.info(f"✅ Report uploaded to S3: {len(uploaded_files)} files, {len(screenshot_map)} screenshots linked")
            
            return {
                'report_url': report_url,
                's3_prefix': s3_prefix,
                'uploaded_files': uploaded_files,
                'total_files': len(uploaded_files),
                'total_size_mb': sum(f['size'] for f in uploaded_files) / (1024 * 1024)
            }
            
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {e}")
            raise
    
    def _replace_screenshot_paths(self, html_content: str, screenshot_map: Dict[str, str]) -> str:
        """
        Replace local screenshot paths in HTML with S3 presigned URLs.
        
        Args:
            html_content: Original HTML content
            screenshot_map: Dictionary mapping local paths to S3 URLs
            
        Returns:
            Modified HTML with S3 URLs
        """
        import re
        
        modified_html = html_content
        
        # Pattern to match img src attributes
        # Matches: src="screenshots/file.png" or src='screenshots/file.png'
        img_pattern = r'(src=["\'`])([^"\'`]+\.(png|jpg|jpeg))(["\'\`])'
        
        def replace_match(match):
            prefix = match.group(1)  # src=" or src='
            path = match.group(2)     # the path
            suffix = match.group(4)   # closing quote
            
            # Try to find this path in our screenshot map
            # Check various formats (with/without ./, forward/back slashes)
            path_variants = [
                path,
                path.replace('\\', '/'),
                path.lstrip('./'),
                path.replace('\\', '/').lstrip('./')
            ]
            
            for variant in path_variants:
                if variant in screenshot_map:
                    logger.debug(f"Replacing '{path}' with S3 URL")
                    return f'{prefix}{screenshot_map[variant]}{suffix}'
            
            # If not found, return original
            logger.warning(f"Screenshot path not found in map: {path}")
            return match.group(0)
        
        modified_html = re.sub(img_pattern, replace_match, modified_html)
        
        return modified_html
    
    def _get_content_type(self, file_extension: str) -> str:
        """Map file extension to content type."""
        content_types = {
            '.html': 'text/html',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.txt': 'text/plain',
            '.md': 'text/markdown'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')
    
    def _generate_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Generate presigned URL for secure temporary access.
        
        Args:
            s3_key: S3 object key
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            raise
    
    def list_user_reports(self, user_id: str) -> List[Dict]:
        """
        List all reports for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of report metadata
        """
        try:
            prefix = f"sessions/{user_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            reports = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.html'):
                        reports.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'url': self._generate_presigned_url(obj['Key'])
                        })
            
            return reports
            
        except ClientError as e:
            logger.error(f"❌ Failed to list reports: {e}")
            return []
    
    def delete_report(self, s3_prefix: str) -> bool:
        """
        Delete all files in a report folder.
        
        Args:
            s3_prefix: S3 prefix (folder path)
            
        Returns:
            True if successful
        """
        try:
            # List all objects with prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=s3_prefix
            )
            
            if 'Contents' not in response:
                logger.warning(f"⚠️ No objects found with prefix: {s3_prefix}")
                return False
            
            # Delete all objects
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects_to_delete}
            )
            
            logger.info(f"✅ Deleted {len(objects_to_delete)} objects from {s3_prefix}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Failed to delete report: {e}")
            return False
    
    def get_bucket_size(self) -> Dict:
        """Get total bucket size and object count."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                return {'total_objects': 0, 'total_size_mb': 0}
            
            total_size = sum(obj['Size'] for obj in response['Contents'])
            total_objects = len(response['Contents'])
            
            return {
                'total_objects': total_objects,
                'total_size_mb': total_size / (1024 * 1024),
                'bucket_name': self.bucket_name
            }
            
        except ClientError as e:
            logger.error(f"❌ Failed to get bucket size: {e}")
            return {}
