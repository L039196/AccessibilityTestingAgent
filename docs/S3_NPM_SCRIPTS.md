# S3 Cloud Storage - NPM Scripts Guide

Quick reference for running accessibility tests with AWS S3 cloud storage integration.

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Basic S3 Testing](#basic-s3-testing)
- [Platform-Specific S3 Tests](#platform-specific-s3-tests)
- [BrowserStack + S3 Combined](#browserstack--s3-combined)
- [Local Storage (Explicit)](#local-storage-explicit)
- [Matrix Testing with S3](#matrix-testing-with-s3)
- [Environment Variables](#environment-variables)

---

## Prerequisites

### 1. AWS Setup
Complete the [S3 Setup Guide](./S3_SETUP_GUIDE.md) first to:
- Create AWS account
- Set up IAM user
- Create S3 bucket
- Configure environment variables

### 2. Environment Variables
Create `.env` file with AWS credentials:
```bash
ENABLE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=accessibility-testing-reports
S3_REGION=us-east-1
S3_AUTO_CLEANUP_LOCAL=true
```

---

## Basic S3 Testing

### Test with S3 Storage (Default Desktop)
```bash
npm run test:s3
```

### Test with S3 Storage (Headless)
```bash
npm run test:s3:headless
```

**Output:**
```
✅ Successfully uploaded report to S3
📊 Report URL: https://bucket.s3.amazonaws.com/...?presigned_params
⏰ URL expires in: 7 days
📁 Files uploaded: 15 (HTML + screenshots)
💾 Total size: 2.5 MB
🧹 Local files cleaned up
```

---

## Platform-Specific S3 Tests

### Desktop Testing with S3
```bash
# Headed mode (browser visible)
npm run test:s3:desktop

# Headless mode
npm run test:s3:desktop:headless

# Explicitly headed
npm run test:s3:desktop:headed
```

### Mobile Testing with S3
```bash
# Default mobile (iOS)
npm run test:s3:mobile

# Headless mode
npm run test:s3:mobile:headless

# Headed mode
npm run test:s3:mobile:headed
```

### Tablet Testing with S3
```bash
# Default tablet (iOS)
npm run test:s3:tablet

# Headless mode
npm run test:s3:tablet:headless

# Headed mode
npm run test:s3:tablet:headed
```

---

## BrowserStack + S3 Combined

Test on real devices via BrowserStack **AND** store reports in S3 cloud.

### Desktop on BrowserStack + S3
```bash
npm run test:s3:browserstack:desktop
```

### Mobile on BrowserStack + S3
```bash
npm run test:s3:browserstack:mobile
```

### Tablet on BrowserStack + S3
```bash
npm run test:s3:browserstack:tablet
```

### All BrowserStack Devices + S3
```bash
npm run test:s3:browserstack
```

**Use Case:** Perfect for cloud-deployed chat UI where tests run remotely on BrowserStack and reports are stored in S3 for access via presigned URLs.

---

## Local Storage (Explicit)

Run tests **WITHOUT** S3 storage (local storage only).

### Desktop Local
```bash
npm run test:local:desktop
```

### Mobile Local
```bash
npm run test:local:mobile
```

### Tablet Local
```bash
npm run test:local:tablet
```

### Headless Local
```bash
npm run test:local:headless
```

**Note:** These scripts explicitly disable S3 even if `ENABLE_S3_STORAGE=true` is set in `.env`.

---

## Matrix Testing with S3

Run multiple platform tests with S3 storage.

### Test All Platforms (Headless)
```bash
npm run test:s3:matrix:platforms
```
Runs: Desktop → Mobile → Tablet (all headless, all to S3)

### Test All Platforms (Headed)
```bash
npm run test:s3:matrix:platforms:headed
```
Runs: Desktop → Mobile → Tablet (browsers visible, all to S3)

---

## Environment Variables

### Inline Override
Override environment variables for a single test run:

```bash
# Enable S3 for one test only
ENABLE_S3_STORAGE=true npm run test:desktop

# Use different bucket
S3_BUCKET_NAME=my-other-bucket npm run test:s3:desktop

# Disable auto-cleanup
S3_AUTO_CLEANUP_LOCAL=false npm run test:s3:mobile
```

### Permanent Configuration
Edit `.env` file:
```bash
# Enable/disable S3 globally
ENABLE_S3_STORAGE=true

# Auto-cleanup local files after S3 upload
S3_AUTO_CLEANUP_LOCAL=true

# Presigned URL expiry (seconds)
S3_PRESIGNED_URL_EXPIRY=604800  # 7 days
```

---

## Script Comparison

| Script | Storage | Browser | Platform |
|--------|---------|---------|----------|
| `npm run test:desktop` | Local | Headed | Desktop |
| `npm run test:s3:desktop` | S3 | Headed | Desktop |
| `npm run test:local:desktop` | Local (explicit) | Headed | Desktop |
| `npm run test:s3:desktop:headless` | S3 | Headless | Desktop |
| `npm run test:s3:browserstack:desktop` | S3 | BrowserStack | Desktop |

---

## Common Workflows

### Development (Local)
```bash
npm run test:local:desktop
```
- Fastest
- No AWS credentials needed
- Reports in `./results/`

### CI/CD Pipeline (S3)
```bash
npm run test:s3:desktop:headless
```
- Headless for speed
- Reports uploaded to S3
- Presigned URLs in output

### Cloud Chat UI (BrowserStack + S3)
```bash
npm run test:s3:browserstack:mobile
```
- Real device testing
- Cloud storage
- Shareable report URLs

### Comprehensive Testing (Matrix + S3)
```bash
npm run test:s3:matrix:platforms
```
- All platforms tested
- All reports in S3
- Batch presigned URLs

---

## Troubleshooting

### Error: "AWS credentials not found"
**Solution:** Create `.env` file with AWS credentials:
```bash
cp .env.s3.template .env
# Edit .env with your AWS credentials
```

### Error: "S3 bucket does not exist"
**Solution:** Create bucket or update `.env`:
```bash
S3_BUCKET_NAME=your-existing-bucket
```

### Reports not cleaning up locally
**Solution:** Enable auto-cleanup:
```bash
S3_AUTO_CLEANUP_LOCAL=true npm run test:s3:desktop
```

### Presigned URL expired
**Solution:** Generate new URL:
```bash
# URLs expire after 7 days by default
# Re-run the test to generate new URLs
npm run test:s3:desktop
```

---

## Cost Optimization Tips

### Use Headless Mode for CI/CD
```bash
# Faster + cheaper (less CPU usage)
npm run test:s3:desktop:headless
```

### Enable Auto-Cleanup
```bash
# Reduce local storage + S3 redundancy
S3_AUTO_CLEANUP_LOCAL=true
```

### Set Short Lifecycle Policies
Configure S3 bucket to auto-delete old reports:
- 7 days: For temporary reports
- 30 days: For compliance (default)
- 90 days: For long-term storage

### Use S3 Intelligent-Tiering
Enable in S3 bucket settings:
- Frequently accessed: S3 Standard
- Infrequently accessed: S3 IA (cheaper)
- Archive: S3 Glacier (cheapest)

---

## Next Steps

1. ✅ Complete [S3 Setup Guide](./S3_SETUP_GUIDE.md)
2. ✅ Configure `.env` with AWS credentials
3. ✅ Run first S3 test: `npm run test:s3:desktop`
4. ✅ Share presigned URLs with team
5. ✅ Integrate into CI/CD pipeline
6. ✅ Configure lifecycle policies for cost optimization

---

## Support

- **S3 Setup:** See [S3_SETUP_GUIDE.md](./S3_SETUP_GUIDE.md)
- **S3 Quick Ref:** See [S3_QUICK_REFERENCE.md](./S3_QUICK_REFERENCE.md)
- **BrowserStack:** See [BROWSERSTACK_GUIDE.md](./BROWSERSTACK_GUIDE.md)
- **General Usage:** Run `npm run help`
