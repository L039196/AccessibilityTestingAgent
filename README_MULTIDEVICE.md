# Multi-Device Accessibility Testing Agent

This enhanced accessibility testing agent now supports testing websites across different device types (desktop, mobile, tablet) with device-specific emulation and reporting.

## 🚀 Quick Start

### Testing Mobile Devices
```bash
npm run test:csv:mobile
```

### Testing Tablet Devices
```bash
npm run test:csv:tablet
```

### Testing Desktop Devices
```bash
npm run test:csv:desktop
```

### Testing All Device Types
```bash
npm run test:all
```

## 📁 Results Structure

The agent creates organized results in the following structure:
```
results/
├── accessibility_report_combined.html    # Combined report for all devices
├── desktop/
│   ├── accessibility_report_desktop.html
│   └── screenshots/
│       └── screenshot_desktop_Desktop_*.png
├── mobile/
│   ├── accessibility_report_mobile.html
│   └── screenshots/
│       ├── screenshot_mobile_iPhone13_*.png
│       └── screenshot_mobile_SamsungGalaxyS21_*.png
└── tablet/
    ├── accessibility_report_tablet.html
    └── screenshots/
        ├── screenshot_tablet_iPad_*.png
        └── screenshot_tablet_SamsungGalaxyTab_*.png
```

## 🔧 Configuration

### Device Profiles

The `config.json` file includes predefined device profiles:

#### Mobile Devices
- **iPhone 13**: 390x844 viewport, iOS Safari user agent
- **Samsung Galaxy S21**: 360x800 viewport, Android Chrome user agent

#### Tablet Devices
- **iPad**: 820x1180 viewport, iPadOS Safari user agent
- **Samsung Galaxy Tab**: 768x1024 viewport, Android Chrome user agent

#### Desktop Devices
- **Desktop**: 1920x1080 viewport, Windows Chrome user agent

### Customizing Device Profiles

You can add or modify device profiles in `config.json`:

```json
{
  "device_profiles": {
    "mobile": {
      "Custom Phone": {
        "viewport": {"width": 375, "height": 812},
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
        "deviceScaleFactor": 2,
        "isMobile": true,
        "hasTouch": true
      }
    }
  }
}
```

## 📊 Reports Features

### Device-Specific Information
- Each page report shows the device name and browser used
- Screenshots are organized by device type and specific device
- Summary statistics are calculated per device type

### Enhanced HTML Reports
- **Device badges** showing which device type was tested
- **Device-specific navigation** in the sidebar
- **Mobile-optimized screenshots** with proper naming
- **Responsive design** that works on all devices

## 🎯 Command Line Usage

### Direct Python Commands
```bash
# Test mobile only
python main_parallel.py --csv urls_to_test.csv --device mobile

# Test tablet only
python main_parallel.py --csv urls_to_test.csv --device tablet

# Test desktop only
python main_parallel.py --csv urls_to_test.csv --device desktop

# Test all devices (default)
python main_parallel.py --csv urls_to_test.csv
```

### NPM Scripts (Recommended)
```bash
# Test specific device types
npm run test:mobile
npm run test:tablet
npm run test:desktop

# View reports
npm run view:mobile
npm run view:tablet
npm run view:desktop
npm run view:combined

# Cleanup
npm run clean
npm run clean:results
```

## 🔍 What's Being Tested

### Device-Specific Accessibility Concerns

#### Mobile Testing
- Touch target sizes (minimum 44px)
- Mobile-specific navigation patterns
- Screen reader compatibility on mobile
- Viewport scaling issues
- Mobile-specific form interactions

#### Tablet Testing
- Hybrid touch/mouse interactions
- Landscape/portrait layout issues
- Tablet-specific UI components
- Multi-column layouts
- Touch gesture accessibility

#### Desktop Testing
- Keyboard navigation
- Focus management
- Mouse hover states
- Large screen layouts
- Desktop-specific interactions

### WCAG Compliance
All devices are tested against:
- **WCAG 2.1 Level A** requirements
- **WCAG 2.1 Level AA** requirements
- **Best practices** for accessibility

## 🛠 Technical Implementation

### Browser Emulation
- Uses Playwright's device emulation capabilities
- Properly sets viewport size, user agent, and device properties
- Emulates touch capabilities for mobile/tablet devices
- Sets appropriate device pixel ratios

### Parallel Testing
- Runs multiple browser instances simultaneously
- Each device profile gets its own worker process
- Progress tracking per device type
- Error handling per device/browser combination

### Screenshot Capture
- Device-specific screenshot directories
- Unique naming with device type and name
- Element-level screenshots for violations
- Organized by device type for easy comparison

## 🎨 Report Customization

The HTML reports include:
- **Responsive design** that adapts to viewing device
- **Device-specific styling** with badges and indicators
- **Interactive navigation** with device type filtering
- **Mobile-friendly interface** for viewing on phones/tablets

## 📈 Performance Considerations

### Parallel Processing
- Each device type runs in parallel
- Multiple browsers per device type
- Queue-based URL processing
- Automatic resource cleanup

### Storage Optimization
- Screenshots only for violations
- Compressed PNG format
- Device-specific directories prevent conflicts
- Combined reports reduce duplication

## 🚦 Best Practices

1. **Start with mobile testing** - Most accessibility issues show up on mobile first
2. **Use device-specific URLs** - Some sites have different mobile/desktop versions
3. **Test across browsers** - Both Chromium and WebKit for comprehensive coverage
4. **Review device-specific violations** - Some issues only appear on certain device types
5. **Compare reports** - Use the combined report to see cross-device patterns

## 🔗 Integration

### CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Run Mobile Accessibility Tests
  run: npm run test:csv:mobile

- name: Run Tablet Accessibility Tests
  run: npm run test:csv:tablet

- name: Upload Mobile Report
  uses: actions/upload-artifact@v3
  with:
    name: mobile-accessibility-report
    path: results/mobile/
```

### Automated Scheduling
The existing GitHub Actions workflow can be extended to run device-specific tests:
```yaml
- name: Test All Devices
  run: |
    npm run test:mobile
    npm run test:tablet
    npm run test:desktop
```

## 📞 Support

For issues or questions about multi-device testing:
1. Check the generated reports for device-specific information
2. Review the console output for device emulation details  
3. Verify device profiles in `config.json`
4. Test with individual device types to isolate issues

---

**Happy Testing!** 🎉 The multi-device accessibility testing agent helps ensure your website works for all users across all devices.
