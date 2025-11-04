# 🚀 Quick Start Guide - Accessibility Testing Agent

## ⚡ 1-Minute Start

```bash
# 1. Run a test
python main_parallel.py --csv urls_to_test.csv --device desktop --max-workers 4

# 2. View results
open results/desktop/accessibility_report.html

# 3. Check logs
cat logs/accessibility_agent.log
```

---

## 📋 **CSV Format**

Create `urls_to_test.csv`:
```csv
url,name,requiresAuth,mfaTemplate
https://www.example.com/,Homepage,false,
https://internal.example.com/dashboard,Dashboard,true,lilly
```

---

## 🎯 **Common Commands**

### Basic Test (Public URLs)
```bash
python main_parallel.py --csv public_urls.csv --device desktop
```

### With SSO Authentication
```bash
python main_parallel.py --csv urls_to_test.csv --device desktop --headless=false
```

### Debug Mode
```bash
# Set log_level: "DEBUG" in config.json
python main_parallel.py --csv urls_to_test.csv --device desktop
```

### Multiple Workers
```bash
python main_parallel.py --csv urls_to_test.csv --device desktop --max-workers 8
```

---

## 📊 **View Results**

### HTML Report (Recommended)
```bash
open results/desktop/accessibility_report.html
```

### Logs
```bash
# Real-time monitoring
tail -f logs/accessibility_agent.log

# View all logs
cat logs/accessibility_agent.log

# Filter errors
grep "ERROR" logs/accessibility_agent.log
```

---

## ⚙️ **Configuration** (`config.json`)

```json
{
  "max_workers": 4,              // Parallel tabs (2-8 recommended)
  "headless": false,             // Show browser (true for CI/CD)
  "report_format": "html",       // html/json/md
  "max_retries": 2,              // Retry failed tests
  "log_level": "INFO"            // DEBUG/INFO/WARNING/ERROR
}
```

---

## 🔧 **Troubleshooting**

### No HTML Report Generated
```bash
# Check config.json
"report_format": "html"  # Should be html, not md

# Check results folder
ls -la results/desktop/
```

### SSO Authentication Fails
```bash
# Run with visible browser
python main_parallel.py --csv urls.csv --device desktop --headless=false

# Check credentials in config/mfa-templates.json
```

### Slow Performance
```bash
# Increase workers
--max-workers 8

# Or reduce worker count if memory constrained
--max-workers 2
```

---

## 📈 **Performance Tips**

1. **Optimal Workers**: 4-8 concurrent tabs
2. **Headless Mode**: Faster (use for CI/CD)
3. **Group URLs**: Public first, then private
4. **CSV Organization**: One file per test suite

---

## 🎓 **Best Practices**

### 1. Organize Tests by Environment
```
dev_urls.csv
staging_urls.csv
prod_urls.csv
```

### 2. Monitor Logs
```bash
tail -f logs/accessibility_agent.log
```

### 3. Check Violations
```bash
# Count violations by severity
grep "critical" results/desktop/accessibility_report.html
```

### 4. Share Reports
```bash
# Copy to shared drive
cp results/desktop/accessibility_report.html /shared/reports/
```

---

## ✅ **Success Checklist**

- ✅ CSV file created with correct format
- ✅ Config.json configured
- ✅ Virtual environment activated
- ✅ Dependencies installed (`pip install -r requirements.txt`)
- ✅ Browser launched (for SSO tests)
- ✅ HTML report generated
- ✅ Logs reviewed

---

## 🆘 **Get Help**

1. Check logs: `logs/accessibility_agent.log`
2. View full documentation: `PRIORITY1_IMPLEMENTATION_COMPLETE.md`
3. Review error types: `agent/exceptions.py`

---

**Ready to test? Run your first test now!** 🚀

```bash
python main_parallel.py --csv urls_to_test.csv --device desktop --max-workers 4
```
