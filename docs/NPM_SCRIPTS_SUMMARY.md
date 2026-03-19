# NPM Scripts - Complete Reference

## Summary of Changes

Added **24 new npm scripts** for AWS S3 cloud storage integration.

---

## New S3 Scripts

### Basic S3 Testing (3 scripts)
| Script | Description | Storage | Browser |
|--------|-------------|---------|---------|
| `npm run test:s3` | Test with S3 (default desktop) | S3 | Headed |
| `npm run test:s3:headless` | Test with S3 (headless) | S3 | Headless |
| `npm run test:s3:browserstack` | BrowserStack + S3 (all devices) | S3 | BrowserStack |

### S3 Desktop Testing (3 scripts)
| Script | Description | Storage | Browser |
|--------|-------------|---------|---------|
| `npm run test:s3:desktop` | Desktop with S3 | S3 | Headed |
| `npm run test:s3:desktop:headless` | Desktop with S3 (headless) | S3 | Headless |
| `npm run test:s3:desktop:headed` | Desktop with S3 (explicit headed) | S3 | Headed |

### S3 Mobile Testing (3 scripts)
| Script | Description | Storage | Browser |
|--------|-------------|---------|---------|
| `npm run test:s3:mobile` | Mobile with S3 | S3 | Headed |
| `npm run test:s3:mobile:headless` | Mobile with S3 (headless) | S3 | Headless |
| `npm run test:s3:mobile:headed` | Mobile with S3 (explicit headed) | S3 | Headed |

### S3 Tablet Testing (3 scripts)
| Script | Description | Storage | Browser |
|--------|-------------|---------|---------|
| `npm run test:s3:tablet` | Tablet with S3 | S3 | Headed |
| `npm run test:s3:tablet:headless` | Tablet with S3 (headless) | S3 | Headless |
| `npm run test:s3:tablet:headed` | Tablet with S3 (explicit headed) | S3 | Headed |

### S3 + BrowserStack Combined (4 scripts)
| Script | Description | Storage | Browser |
|--------|-------------|---------|---------|
| `npm run test:s3:browserstack` | All devices on BrowserStack + S3 | S3 | BrowserStack |
| `npm run test:s3:browserstack:desktop` | Desktop on BrowserStack + S3 | S3 | BrowserStack |
| `npm run test:s3:browserstack:mobile` | Mobile on BrowserStack + S3 | S3 | BrowserStack |
| `npm run test:s3:browserstack:tablet` | Tablet on BrowserStack + S3 | S3 | BrowserStack |

### S3 Matrix Testing (2 scripts)
| Script | Description | Storage | Browser |
|--------|-------------|---------|---------|
| `npm run test:s3:matrix:platforms` | All platforms (D/M/T) → S3 | S3 | Headless |
| `npm run test:s3:matrix:platforms:headed` | All platforms (D/M/T) → S3 | S3 | Headed |

### Local Storage Explicit (5 scripts)
| Script | Description | Storage | Browser |
|--------|-------------|---------|---------|
| `npm run test:local` | Explicit local storage | Local | Headed |
| `npm run test:local:headless` | Explicit local storage (headless) | Local | Headless |
| `npm run test:local:desktop` | Desktop local storage | Local | Headed |
| `npm run test:local:mobile` | Mobile local storage | Local | Headed |
| `npm run test:local:tablet` | Tablet local storage | Local | Headed |

### Info/Help Scripts (3 new)
| Script | Description |
|--------|-------------|
| `npm run info:s3` | Show S3 cloud storage usage |
| `npm run info:browserstack` | Show BrowserStack + S3 usage |
| `npm run info:local` | Show local storage usage |

---

## Usage Examples

### Quick Start (No AWS Setup Required)
```bash
# Use default local storage
npm run test:desktop
```

### S3 Cloud Storage
```bash
# Setup: Create .env with AWS credentials first
npm run test:s3:desktop
```

### BrowserStack + S3 (Cloud Deployment)
```bash
# Setup: AWS credentials + BrowserStack credentials
npm run test:s3:browserstack:mobile
```

### Explicit Local Storage
```bash
# Force local storage even if S3 is configured
npm run test:local:desktop
```

---

## Environment Variables

All S3 scripts use these environment variables:

```bash
# Enable/disable S3 storage
ENABLE_S3_STORAGE=true

# AWS credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# S3 bucket configuration
S3_BUCKET_NAME=accessibility-testing-reports
S3_REGION=us-east-1

# Optional settings
S3_AUTO_CLEANUP_LOCAL=true
S3_PRESIGNED_URL_EXPIRY=604800  # 7 days
```

---

## Script Naming Convention

### Pattern: `test:{storage}:{platform}:{mode}`

- **storage**: `s3`, `local`, or omitted (default)
- **platform**: `desktop`, `mobile`, `tablet`, `browserstack`
- **mode**: `headless`, `headed`, or omitted (default headed)

### Examples:
- `test:s3:desktop:headless` = S3 + Desktop + Headless
- `test:local:mobile` = Local + Mobile + Headed (default)
- `test:s3:browserstack:tablet` = S3 + BrowserStack + Tablet

---

## Storage Decision Tree

```
Do you need cloud storage?
├─ NO → Use default scripts
│   ├─ npm run test:desktop
│   ├─ npm run test:mobile
│   └─ npm run test:tablet
│
└─ YES → Setup AWS S3
    ├─ Local browser testing + S3
    │   ├─ npm run test:s3:desktop
    │   ├─ npm run test:s3:mobile
    │   └─ npm run test:s3:tablet
    │
    └─ BrowserStack testing + S3
        ├─ npm run test:s3:browserstack:desktop
        ├─ npm run test:s3:browserstack:mobile
        └─ npm run test:s3:browserstack:tablet
```

---

## CI/CD Pipeline Examples

### GitHub Actions (S3 + Headless)
```yaml
- name: Run Accessibility Tests
  run: npm run test:s3:desktop:headless
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    S3_BUCKET_NAME: accessibility-reports
```

### GitLab CI (BrowserStack + S3)
```yaml
test:
  script:
    - npm run test:s3:browserstack:mobile
  variables:
    ENABLE_S3_STORAGE: "true"
    USE_BROWSERSTACK: "true"
```

### Jenkins (Matrix + S3)
```groovy
stage('Test All Platforms') {
  steps {
    sh 'npm run test:s3:matrix:platforms'
  }
}
```

---

## Cost Comparison

| Testing Method | Cost/Month | Setup Time |
|----------------|------------|------------|
| Local Storage | Free | 5 minutes |
| S3 Storage | ~$5 | 15 minutes |
| BrowserStack | ~$30-$100 | 10 minutes |
| BrowserStack + S3 | ~$35-$105 | 25 minutes |

---

## Total NPM Scripts

### Before S3 Integration: ~180 scripts
### After S3 Integration: **204 scripts** ✨

**New Scripts Breakdown:**
- S3 Testing: 13 scripts
- S3 + BrowserStack: 4 scripts
- S3 Matrix: 2 scripts
- Local Explicit: 5 scripts
- Info Commands: 3 scripts

---

## Next Steps

1. ✅ **Setup AWS S3** - Follow [S3_SETUP_GUIDE.md](./S3_SETUP_GUIDE.md)
2. ✅ **Configure Environment** - Create `.env` from `.env.s3.template`
3. ✅ **Run First Test** - `npm run test:s3:desktop`
4. ✅ **Integrate CI/CD** - Add to your pipeline
5. ✅ **Share Reports** - Use presigned URLs from S3

---

## Documentation

- **S3 Setup:** [S3_SETUP_GUIDE.md](./S3_SETUP_GUIDE.md)
- **S3 Quick Ref:** [S3_QUICK_REFERENCE.md](./S3_QUICK_REFERENCE.md)
- **NPM Scripts:** [S3_NPM_SCRIPTS.md](./S3_NPM_SCRIPTS.md)
- **All Scripts:** Run `npm run help`
