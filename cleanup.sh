#!/bin/bash

# Accessibility Test Agent Cleanup Script
# This script removes temporary files, old screenshots, and system files

echo "🧹 Starting cleanup of Accessibility Test Agent workspace..."

# Navigate to the project directory
cd "$(dirname "$0")"

# Remove macOS system files
echo "📱 Removing macOS .DS_Store files..."
find . -name "*.DS_Store" -delete 2>/dev/null || true

# Remove Python cache files
echo "🐍 Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Clean up old screenshots (keep only 3 most recent per device type)
echo "📸 Cleaning up old screenshots..."
for dir in results/*/screenshots results/*/*/screenshots; do
    if [ -d "$dir" ]; then
        cd "$dir"
        # Keep only 3 most recent screenshots for each prefix
        for prefix in $(ls screenshot_* 2>/dev/null | sed 's/_[^_]*\.png$//' | sort -u); do
            ls -t ${prefix}_*.png 2>/dev/null | tail -n +4 | xargs rm -f 2>/dev/null || true
        done
        cd - > /dev/null
    fi
done

# Remove any temporary files
echo "🗑️  Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true

# Remove log files older than 7 days
echo "📝 Removing old log files..."
find . -name "*.log" -mtime +7 -delete 2>/dev/null || true

# Count remaining files
screenshot_count=$(find results -name "screenshot_*.png" 2>/dev/null | wc -l | tr -d ' ')
echo "✅ Cleanup complete!"
echo "📊 Statistics:"
echo "   - Screenshots remaining: $screenshot_count"
echo "   - Workspace size: $(du -sh . | cut -f1)"

echo "🎯 To run this cleanup regularly, add to your cron job:"
echo "   0 2 * * 0 cd $(pwd) && ./cleanup.sh"
