"""Quick test to verify S3 upload with session token"""
import os
from dotenv import load_dotenv
from agent.storage.s3_storage import S3ReportStorage
from pathlib import Path

# Load environment variables
load_dotenv()

# Check credentials
print("🔍 Checking AWS credentials...")
access_key = os.getenv('AWS_ACCESS_KEY_ID')
secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
session_token = os.getenv('AWS_SESSION_TOKEN')
bucket = os.getenv('S3_BUCKET_NAME')

print(f"✅ Access Key: {access_key[:10]}..." if access_key else "❌ No access key")
print(f"✅ Secret Key: {'*' * 10}..." if secret_key else "❌ No secret key")
print(f"✅ Session Token: {session_token[:20]}..." if session_token else "❌ No session token")
print(f"✅ Bucket: {bucket}" if bucket else "❌ No bucket")

# Initialize S3 storage
try:
    print("\n📦 Initializing S3 storage...")
    s3_storage = S3ReportStorage(
        bucket_name=bucket,
        region='us-east-1',
        access_key=access_key,
        secret_key=secret_key,
        session_token=session_token
    )
    print("✅ S3 storage initialized successfully!")
    
    # Check if we have a results folder to upload
    results_dir = Path("results/desktop")
    if results_dir.exists():
        print(f"\n📂 Found results directory: {results_dir}")
        print(f"📊 Uploading entire folder to S3...")
        
        result = s3_storage.upload_report_folder(
            local_folder_path=str(results_dir),
            user_id="test-user",
            session_id="test-session",
            device_type="desktop"
        )
        
        print(f"\n✅ Upload successful!")
        print(f"📁 Files uploaded: {result['total_files']}")
        print(f"📦 Total size: {result['total_size_mb']:.2f} MB")
        print(f"🔗 Report URL: {result['report_url']}")
        print(f"⏰ URL expires in: 7 days")
        
    else:
        print(f"⚠️ No results directory found at {results_dir}")
        print("Run a test first to generate results")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
