# AWS S3 Integration Guide

## 📋 Overview

This guide shows how to configure AWS S3 storage for accessibility test reports. S3 storage is **optional** - the agent works perfectly with local storage. Use S3 when deploying to cloud environments or when you need centralized report storage.

---

## 🎯 When to Use S3

**Use S3 when:**
- ✅ Deploying to cloud (AWS, Docker, Kubernetes)
- ✅ Building a chat UI or web interface
- ✅ Multiple users need access to reports
- ✅ Need long-term report storage
- ✅ Want automatic cleanup (30-day lifecycle)

**Use Local Storage when:**
- ✅ Running on local development machine
- ✅ Quick testing/debugging
- ✅ Single user environment
- ✅ Want to keep costs at zero

---

## 🔧 Setup Instructions

### **Step 1: Create AWS Account** (if you don't have one)

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Follow the registration process
4. Add payment method (required, but has free tier)

**AWS Free Tier includes:**
- 5 GB storage (12 months)
- 20,000 GET requests
- 2,000 PUT requests

### **Step 2: Create IAM User**

1. Log into AWS Console
2. Go to **IAM** → **Users** → **Create User**
3. User name: `accessibility-agent-s3`
4. Enable: ☑️ **Programmatic access**
5. Click **Next**

### **Step 3: Set Permissions**

**Option A - Quick Setup (Full S3 Access):**
1. Select: **Attach existing policies directly**
2. Search for: `AmazonS3FullAccess`
3. Check the box
4. Click **Next** → **Create User**

**Option B - Restricted Access (Recommended for Production):**
1. Select: **Create inline policy**
2. Click **JSON** tab
3. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::accessibility-testing-reports",
        "arn:aws:s3:::accessibility-testing-reports/*"
      ]
    }
  ]
}
```

4. Click **Review** → **Create Policy**

### **Step 4: Download Credentials**

⚠️ **IMPORTANT: This is your only chance to download the secret key!**

1. After creating the user, you'll see:
   - **Access key ID**: `AKIAIOSFODNN7EXAMPLE`
   - **Secret access key**: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

2. Click **Download .csv** or copy both values
3. Store them securely (password manager or .env file)

### **Step 5: Create S3 Bucket**

1. Go to **S3** → **Create Bucket**
2. **Bucket name**: `accessibility-testing-reports`
   - Must be globally unique
   - Try: `lilly-accessibility-reports` or `your-company-accessibility`
3. **Region**: `us-east-1` (or your preferred region)
4. **Block Public Access**: ☑️ **Keep enabled** (for security)
5. **Bucket Versioning**: Disabled
6. **Encryption**: ☑️ Enable (SSE-S3)
7. Click **Create Bucket**

### **Step 6: Configure Lifecycle Policy (Auto-Cleanup)**

1. Open your bucket
2. Go to **Management** → **Lifecycle rules**
3. Click **Create lifecycle rule**
4. Rule name: `auto-delete-old-reports`
5. Scope: ☑️ **Apply to all objects**
6. Lifecycle rule actions:
   - ☑️ **Expire current versions of objects**
   - Days after object creation: **30**
7. Click **Create rule**

This will automatically delete reports older than 30 days.

---

## ⚙️ Configuration

### **Method 1: Environment Variables (Recommended)**

Create a `.env` file in your project root:

```bash
# AWS S3 Configuration
ENABLE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET_NAME=accessibility-testing-reports
S3_REGION=us-east-1

# Optional Settings
S3_AUTO_CLEANUP_LOCAL=true
S3_PRESIGNED_URL_EXPIRY=604800
USER_ID=your_username
```

**⚠️ Security: Add `.env` to `.gitignore`**

```bash
echo ".env" >> .gitignore
```

### **Method 2: Configuration File**

Edit `config/s3_config.json`:

```json
{
  "s3_config": {
    "enabled": true,
    "bucket_name": "accessibility-testing-reports",
    "region": "us-east-1",
    "auto_cleanup_local": true,
    "presigned_url_expiry_seconds": 604800
  },
  "aws_credentials": {
    "use_environment_variables": true
  }
}
```

Then set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

---

## 🧪 Test the Integration

### **Quick Test Script**

Create `test_s3.py`:

```python
#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from agent.storage.s3_storage import S3ReportStorage

load_dotenv()

# Test S3 connection
storage = S3ReportStorage(
    bucket_name=os.getenv('S3_BUCKET_NAME'),
    region=os.getenv('S3_REGION')
)

# Check bucket access
bucket_info = storage.get_bucket_size()
print(f"✅ Connected to S3!")
print(f"   Bucket: {bucket_info['bucket_name']}")
print(f"   Objects: {bucket_info['total_objects']}")
print(f"   Size: {bucket_info['total_size_mb']:.2f} MB")
```

Run it:
```bash
python test_s3.py
```

### **Full Integration Test**

Run a test with S3 enabled:

```bash
# Set environment variable
export ENABLE_S3_STORAGE=true

# Run test
python main_parallel.py --csv urls_to_test.csv --device desktop --headless=true
```

Expected output:
```
✅ S3 storage enabled - Bucket: accessibility-testing-reports
📍 Region: us-east-1
...
📤 Uploading to S3...
✅ Uploaded to S3: 15 files
📊 Report URL: https://s3.amazonaws.com/...
⏰ URL expires in: 7 days
🗑️ Local files cleaned up (available on S3)
```

---

## 📊 Usage Examples

### **With S3 Enabled:**

```bash
# Desktop test with S3
ENABLE_S3_STORAGE=true python main_parallel.py --csv urls_to_test.csv --device desktop

# Mobile test with S3
ENABLE_S3_STORAGE=true python main_parallel.py --csv urls_to_test.csv --device mobile-ios

# BrowserStack + S3
ENABLE_S3_STORAGE=true python main_parallel.py --csv urls_to_test.csv --browserstack
```

### **Without S3 (Local Only):**

```bash
# Default behavior - local storage
python main_parallel.py --csv urls_to_test.csv --device desktop

# Explicitly disable S3
ENABLE_S3_STORAGE=false python main_parallel.py --csv urls_to_test.csv
```

### **NPM Scripts:**

Add to `package.json`:

```json
{
  "scripts": {
    "test:s3": "ENABLE_S3_STORAGE=true ./venv/bin/python main_parallel.py --csv urls_to_test.csv --device desktop",
    "test:local": "ENABLE_S3_STORAGE=false ./venv/bin/python main_parallel.py --csv urls_to_test.csv --device desktop"
  }
}
```

---

## 💰 Cost Estimate

**Typical Usage (100 tests/day, 30-day retention):**

```
Storage:
• ~500 MB per day
• ~15 GB per month (with 30-day auto-cleanup)
• 15 GB × $0.023/GB = $0.35/month

Data Transfer:
• ~50 GB downloads per month (viewing reports)
• 50 GB × $0.09/GB = $4.50/month

Total: ~$5/month

First 12 months: FREE (AWS Free Tier)
```

**Cost Optimization Tips:**
1. Enable lifecycle policy (auto-delete after 30 days)
2. Use CloudFront CDN for frequent report viewing
3. Compress reports before upload
4. Set shorter presigned URL expiry (reduces costs)

---

## 🔒 Security Best Practices

### **DO:**
✅ Use IAM users (not root account)  
✅ Enable server-side encryption  
✅ Block public access on bucket  
✅ Use presigned URLs (expires in 7 days)  
✅ Rotate access keys every 90 days  
✅ Store credentials in `.env` (not in code)  
✅ Add `.env` to `.gitignore`  

### **DON'T:**
❌ Commit credentials to git  
❌ Use root account credentials  
❌ Make bucket public  
❌ Share access keys  
❌ Hard-code credentials in source  
❌ Give full S3 access (use restricted policy)  

---

## 🐛 Troubleshooting

### **Issue: "Access Denied"**

```
❌ S3 upload failed: Access Denied
```

**Solution:**
1. Check IAM user has S3 permissions
2. Verify credentials in `.env` are correct
3. Ensure bucket name matches exactly
4. Check bucket region matches config

### **Issue: "Bucket does not exist"**

```
❌ The specified bucket does not exist
```

**Solution:**
1. Create the bucket in AWS Console
2. Verify bucket name spelling
3. Check you're in the correct AWS region

### **Issue: "Invalid credentials"**

```
❌ Failed to initialize S3 client: Invalid credentials
```

**Solution:**
1. Verify `AWS_ACCESS_KEY_ID` is set correctly
2. Verify `AWS_SECRET_ACCESS_KEY` is set correctly
3. Check no extra spaces in `.env` file
4. Try regenerating credentials in AWS Console

### **Issue: "SSL Certificate Error"**

```
❌ SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution (for corporate networks):**
```bash
# Temporarily disable SSL verification (development only)
export PYTHONHTTPSVERIFY=0
```

Or install corporate root certificate.

---

## 📁 Report Structure in S3

```
s3://accessibility-testing-reports/
├── sessions/
│   ├── user123/
│   │   ├── 2026-03-15-abc12345/
│   │   │   ├── desktop/
│   │   │   │   ├── accessibility_report.html
│   │   │   │   ├── screenshots/
│   │   │   │   │   ├── violation_1.png
│   │   │   │   │   └── violation_2.png
│   │   │   │   └── data.json
│   │   │   ├── mobile-ios/
│   │   │   └── mobile-android/
│   │   └── 2026-03-16-def67890/
│   └── user456/
```

**Path Template:**
```
sessions/{user_id}/{date}-{session_id}/{device_type}/
```

---

## 🔗 Additional Resources

- **AWS S3 Documentation**: https://docs.aws.amazon.com/s3/
- **boto3 Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **AWS Free Tier**: https://aws.amazon.com/free/
- **IAM Best Practices**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## 📝 Summary

**Required to Enable S3:**
1. ✅ AWS Account
2. ✅ IAM User with S3 permissions
3. ✅ Access Key ID and Secret Access Key
4. ✅ S3 Bucket created
5. ✅ Environment variables set in `.env`
6. ✅ `ENABLE_S3_STORAGE=true`

**That's it! Your reports will now be stored in S3 with automatic cleanup and secure access.**

---

*Last Updated: March 15, 2026*
