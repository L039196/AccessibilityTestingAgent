#!/usr/bin/env python3
"""
Verify S3 Upload - List all files in the S3 bucket
"""
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def verify_s3_upload():
    """List all files in the S3 bucket to verify upload."""
    
    # Get credentials from environment
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    session_token = os.getenv('AWS_SESSION_TOKEN')
    bucket_name = os.getenv('S3_BUCKET_NAME')
    region = os.getenv('S3_REGION', 'us-east-1')
    
    print("=" * 80)
    print("🔍 S3 BUCKET VERIFICATION")
    print("=" * 80)
    print(f"📦 Bucket: {bucket_name}")
    print(f"📍 Region: {region}")
    print()
    
    try:
        # Create S3 client with session token
        client_params = {
            'region_name': region,
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key
        }
        
        if session_token:
            client_params['aws_session_token'] = session_token
            print("🔑 Using temporary credentials with session token")
        
        s3_client = boto3.client('s3', **client_params)
        
        # List all objects in bucket
        print(f"\n📂 Listing all files in bucket '{bucket_name}'...")
        print("-" * 80)
        
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            print("⚠️  Bucket is empty - no files found!")
            return
        
        # Group files by session
        sessions = {}
        total_size = 0
        
        for obj in response['Contents']:
            key = obj['Key']
            size = obj['Size']
            last_modified = obj['LastModified']
            total_size += size
            
            # Extract session info from key (e.g., sessions/user/date-session/device/)
            parts = key.split('/')
            if len(parts) >= 3 and parts[0] == 'sessions':
                session_key = f"{parts[1]}/{parts[2]}"  # user/date-session
                if session_key not in sessions:
                    sessions[session_key] = []
                sessions[session_key].append({
                    'key': key,
                    'size': size,
                    'modified': last_modified
                })
        
        # Display results grouped by session
        print(f"✅ Found {len(response['Contents'])} files in {len(sessions)} session(s)")
        print()
        
        for session_key, files in sessions.items():
            print(f"📁 Session: {session_key}")
            print(f"   Files: {len(files)}")
            
            # Find HTML report
            html_files = [f for f in files if f['key'].endswith('.html')]
            if html_files:
                html_file = html_files[0]
                print(f"   📄 Report: {html_file['key'].split('/')[-1]}")
                print(f"   📅 Modified: {html_file['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Generate presigned URL
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': html_file['key']},
                    ExpiresIn=604800  # 7 days
                )
                print(f"   🔗 URL: {url[:100]}...")
            
            # Count file types
            screenshots = len([f for f in files if f['key'].endswith('.png')])
            if screenshots > 0:
                print(f"   📸 Screenshots: {screenshots}")
            
            session_size = sum(f['size'] for f in files) / (1024 * 1024)
            print(f"   💾 Size: {session_size:.2f} MB")
            print()
        
        print("-" * 80)
        print(f"📊 SUMMARY:")
        print(f"   Total Files: {len(response['Contents'])}")
        print(f"   Total Size: {total_size / (1024 * 1024):.2f} MB")
        print(f"   Total Sessions: {len(sessions)}")
        print()
        
        # Show most recent file
        most_recent = max(response['Contents'], key=lambda x: x['LastModified'])
        print(f"🕐 Most Recent Upload:")
        print(f"   File: {most_recent['Key']}")
        print(f"   Time: {most_recent['LastModified'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Size: {most_recent['Size'] / 1024:.2f} KB")
        print()
        
        print("=" * 80)
        print("✅ S3 VERIFICATION COMPLETE")
        print("=" * 80)
        
    except ClientError as e:
        print(f"❌ Error accessing S3: {e}")
        print(f"   Error Code: {e.response['Error']['Code']}")
        print(f"   Message: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    verify_s3_upload()
