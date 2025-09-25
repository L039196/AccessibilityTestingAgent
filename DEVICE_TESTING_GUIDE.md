# Device Testing Guide

This guide covers all available device testing options for the Automated Accessibility Testing Agent.

## Available Devices

### Mobile Devices (📱)

#### iOS Devices
- **iPhone 15 Pro** - Latest flagship with iOS 17 (393×852, 3x scaling)
- **iPhone 14** - Previous generation flagship (390×844, 3x scaling)
- **iPhone 13** - Popular model with good market share (390×844, 3x scaling)
- **iPhone 12** - Widely adopted model (390×844, 3x scaling)
- **iPhone SE** - Compact device for testing smaller screens (375×667, 2x scaling)

#### Android Devices
- **Samsung Galaxy S24 Ultra** - Latest Samsung flagship (384×832, 3x scaling)
- **Samsung Galaxy S23** - Previous Samsung flagship (360×780, 3x scaling)
- **Samsung Galaxy S21** - Popular Samsung device (360×800, 3x scaling)
- **Google Pixel 8** - Latest Google device (412×915, 2.75x scaling)
- **Google Pixel 7** - Popular Google device (412×915, 2.75x scaling)
- **OnePlus 11** - Popular alternative Android (412×919, 3x scaling)

### Tablet Devices (📟)

#### iOS Tablets
- **iPad Pro 12.9** - Large professional tablet (1024×1366, 2x scaling)
- **iPad Air** - Mid-range iPad (820×1180, 2x scaling)
- **iPad** - Standard iPad (820×1180, 2x scaling)
- **iPad Mini** - Compact tablet (768×1024, 2x scaling)

#### Android/Windows Tablets
- **Samsung Galaxy Tab S9** - Latest Samsung tablet (800×1280, 2.5x scaling)
- **Samsung Galaxy Tab** - Standard Android tablet (768×1024, 2x scaling)
- **Surface Pro** - Windows tablet with touch (912×1368, 2x scaling)
- **Amazon Fire HD 10** - Budget tablet option (800×1280, 1.5x scaling)

### Desktop Devices (🖥️)
- **Desktop 1920x1080** - Full HD standard (Windows Chrome)
- **Desktop 1440x900** - MacBook standard (macOS Safari)
- **Desktop 1366x768** - Common laptop resolution (Windows Chrome)
- **Desktop 2560x1440** - High-resolution display (Windows Chrome)

## Testing Commands

### Individual Device Testing

#### Mobile Devices
```bash
# iOS Devices
npm run test:iphone15      # iPhone 15 Pro
npm run test:iphone14      # iPhone 14
npm run test:iphone13      # iPhone 13
npm run test:iphone-se     # iPhone SE

# Android Devices
npm run test:galaxy-s24    # Samsung Galaxy S24 Ultra
npm run test:galaxy-s23    # Samsung Galaxy S23
npm run test:galaxy-s21    # Samsung Galaxy S21
npm run test:pixel8        # Google Pixel 8
npm run test:pixel7        # Google Pixel 7
npm run test:oneplus11     # OnePlus 11
```

#### Tablet Devices
```bash
# iOS Tablets
npm run test:ipad-pro      # iPad Pro 12.9
npm run test:ipad-air      # iPad Air
npm run test:ipad          # iPad
npm run test:ipad-mini     # iPad Mini

# Android/Windows Tablets
npm run test:galaxy-tab-s9 # Samsung Galaxy Tab S9
npm run test:surface-pro   # Microsoft Surface Pro
npm run test:fire-hd       # Amazon Fire HD 10
```

### Batch Testing

#### Platform-Specific Testing
```bash
npm run test:ios-devices      # Test iPhone 15 Pro, iPad Pro, iPad Air
npm run test:android-devices  # Test Galaxy S24, Pixel 8, Galaxy Tab S9
npm run test:popular-mobile   # Test iPhone 15, Galaxy S24, Pixel 8
npm run test:popular-tablets  # Test iPad Pro, Galaxy Tab S9, Surface Pro
```

#### Device Type Testing
```bash
npm run test:mobile    # Test all mobile devices
npm run test:tablet    # Test all tablet devices
npm run test:desktop   # Test all desktop resolutions
npm run test:all       # Test all device types
```

### Direct Command Line Usage

You can also use the Python script directly with specific device combinations:

```bash
# Test specific device
./venv/bin/python main_parallel.py --csv urls_to_test.csv --device mobile --device-name "iPhone 15 Pro"

# Test specific tablet
./venv/bin/python main_parallel.py --csv urls_to_test.csv --device tablet --device-name "iPad Pro 12.9"

# Test all devices of a type
./venv/bin/python main_parallel.py --csv urls_to_test.csv --device mobile
```

## Device Selection Strategy

### For Comprehensive Testing
- **Mobile**: iPhone 15 Pro, Samsung Galaxy S24 Ultra, Google Pixel 8
- **Tablet**: iPad Pro 12.9, Samsung Galaxy Tab S9, Surface Pro
- **Desktop**: 1920×1080, 1440×900, 1366×768

### For Quick Testing
- **Mobile**: iPhone 13, Samsung Galaxy S21
- **Tablet**: iPad, Samsung Galaxy Tab
- **Desktop**: 1920×1080

### For Market Share Focus
- **iOS**: iPhone 15 Pro, iPhone 14, iPad Air
- **Android**: Samsung Galaxy S24, Google Pixel 8, Samsung Galaxy Tab S9
- **Budget**: iPhone SE, Amazon Fire HD 10

## Results Structure

Each device test creates organized results:

```
results/
├── mobile/
│   ├── accessibility_report_mobile.html
│   ├── screenshots/
│   │   ├── iPhone_15_Pro/
│   │   ├── Samsung_Galaxy_S24_Ultra/
│   │   └── Google_Pixel_8/
│   └── reports/
├── tablet/
│   ├── accessibility_report_tablet.html
│   ├── screenshots/
│   │   ├── iPad_Pro_12.9/
│   │   ├── Samsung_Galaxy_Tab_S9/
│   │   └── Surface_Pro/
│   └── reports/
└── desktop/
    ├── accessibility_report_desktop.html
    ├── screenshots/
    └── reports/
```

## Device Capabilities

### Touch Capabilities
- **Mobile**: All devices support touch
- **Tablet**: All devices support touch
- **Desktop**: No touch support (mouse/keyboard only)

### Screen Densities
- **1x**: Standard desktop displays
- **1.5x**: Budget tablets (Fire HD)
- **2x**: Standard tablets, iPhone SE
- **2.5x**: High-end tablets (Galaxy Tab S9)
- **2.75x**: Google Pixel devices
- **3x**: Modern flagship phones

### Browser Engines
- **iOS devices**: WebKit (Safari)
- **Android devices**: Chromium (Chrome)
- **Desktop**: Chromium (Chrome) or WebKit (Safari)

## Best Practices

1. **Start with popular devices** for initial testing
2. **Test edge cases** with smallest (iPhone SE) and largest (iPad Pro) screens
3. **Include both orientations** by testing different aspect ratios
4. **Consider market share** in your target demographic
5. **Test accessibility across platforms** to ensure WCAG compliance
6. **Use batch commands** for efficiency
7. **Review device-specific reports** for targeted insights

## Viewing Results

```bash
# View specific device type results
npm run view:mobile
npm run view:tablet  
npm run view:desktop

# View combined results
npm run view:combined
```

## Troubleshooting

### Device Not Found
If you get a "Device not found" error, check the available devices:
- Mobile: iPhone 15 Pro, iPhone 14, iPhone 13, iPhone 12, iPhone SE, Samsung Galaxy S24 Ultra, Samsung Galaxy S23, Samsung Galaxy S21, Google Pixel 8, Google Pixel 7, OnePlus 11
- Tablet: iPad Pro 12.9, iPad Air, iPad, iPad Mini, Samsung Galaxy Tab S9, Samsung Galaxy Tab, Surface Pro, Amazon Fire HD 10
- Desktop: Desktop 1920x1080, Desktop 1440x900, Desktop 1366x768, Desktop 2560x1440

### Command Issues
- Ensure the virtual environment is activated: `source venv/bin/activate`
- Make sure Playwright browsers are installed: `playwright install`
- Verify the CSV file exists and has the correct format

## Configuration

All device profiles are stored in `config.json` under `device_profiles`. You can modify viewport sizes, user agents, and device capabilities as needed for your testing requirements.
