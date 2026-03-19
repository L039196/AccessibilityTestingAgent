# S3 Integration - Quick Reference

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install boto3 python-dotenv
```

### 2. Create `.env` File
```bash
ENABLE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
S3_BUCKET_NAME=accessibility-testing-reports
S3_REGION=us-east-1
```

### 3. Run Test
```bash
python main_parallel.py --csv urls_to_test.csv --device desktop
```

---

## 📋 Configuration Files

### `.env` (Credentials - DO NOT COMMIT)
```bash
ENABLE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET_NAME=accessibility-testing-reports
S3_REGION=us-east-1
S3_AUTO_CLEANUP_LOCAL=true
USER_ID=your_username
```

### `config/s3_config.json` (Settings)
```json
{
  "s3_config": {
    "enabled": false,
    "bucket_name": "",
    "region": "us-east-1",
    "auto_cleanup_local": true,
    "presigned_url_expiry_seconds": 604800
  }
}
```

---

## 🔑 Required AWS Resources

| Resource | Description | How to Get |
|----------|-------------|------------|
| **AWS Account** | Your AWS account | https://aws.amazon.com |
| **IAM User** | User with S3 permissions | IAM → Users → Create User |
| **Access Key** | API credentials | User → Security Credentials |
| **S3 Bucket** | Storage bucket | S3 → Create Bucket |

---

## ⚙️ Configuration Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLE_S3_STORAGE` | Yes | `false` | Enable/disable S3 |
| `AWS_ACCESS_KEY_ID` | Yes* | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Yes* | - | AWS secret key |
| `S3_BUCKET_NAME` | Yes* | - | Bucket name |
| `S3_REGION` | No | `us-east-1` | AWS region |
| `S3_AUTO_CLEANUP_LOCAL` | No | `true` | Delete local after upload |
| `S3_PRESIGNED_URL_EXPIRY` | No | `604800` | URL expiry (seconds) |

*Required only when S3 is enabled

---

## 🎯 Common Commands

### Enable S3
```bash
export ENABLE_S3_STORAGE=true
python main_parallel.py --csv urls_to_test.csv
```

### Disable S3 (Local Only)
```bash
export ENABLE_S3_STORAGE=false
python main_parallel.py --csv urls_to_test.csv
```

### Test S3 Connection
```python
from agent.storage.s3_storage import S3ReportStorage
storage = S3ReportStorage('bucket-name', 'us-east-1')
print(storage.get_bucket_size())
```

---

## 💰 Cost Estimate

**Typical Usage:** ~$5/month
- Storage (15 GB): $0.35/month
- Data Transfer (50 GB): $4.50/month
- **First year:** FREE (AWS Free Tier)

---

## 🔒 Security Checklist

- [ ] Created IAM user (not root)
- [ ] Downloaded access keys
- [ ] Created `.env` file
- [ ] Added `.env` to `.gitignore`
- [ ] S3 bucket has public access blocked
- [ ] Enabled server-side encryption
- [ ] Configured lifecycle policy (30-day cleanup)

---

## 🐛 Quick Troubleshooting

| Error | Solution |
|-------|----------|
| Access Denied | Check IAM permissions |
| Bucket not found | Verify bucket name & region |
| Invalid credentials | Check AWS keys in `.env` |
| SSL error | Corporate network - see docs |

---

## 📊 Report URL Format

After successful upload:
```
📊 Report URL: https://s3.amazonaws.com/bucket/.../report.html?X-Amz-...
⏰ URL expires in: 7 days
```

**URL Structure:**
```
s3://bucket/sessions/{user}/{date}-{session}/{device}/report.html
```

---

## 📖 Full Documentation

See: `docs/S3_SETUP_GUIDE.md` for complete setup instructions.

---

*Quick Reference - March 2026*
