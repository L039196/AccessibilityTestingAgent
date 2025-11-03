"""
Enhanced CSV loader for AccessibilityTestingAgent with SSO support
"""

import csv
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TestConfig:
    """Configuration for a single test from CSV"""
    url: str
    name: str = ""
    requires_auth: bool = False
    mfa_template: str = ""
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'TestConfig':
        """Create TestConfig from a CSV row dictionary"""
        return cls(
            url=row.get('url', '').strip(),
            name=row.get('name', '').strip(),
            requires_auth=row.get('requiresAuth', '').lower() == 'true',
            mfa_template=row.get('mfaTemplate', '').strip()
        )

def load_enhanced_csv(csv_path: str) -> List[TestConfig]:
    """
    Load test configurations from enhanced CSV format
    Supports both simple (url only) and enhanced (url,name,requiresAuth,mfaTemplate) formats
    """
    configs = []
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        # Detect CSV format by reading first few lines
        content = f.read()
        f.seek(0)
        
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if not headers:
            raise ValueError("CSV file appears to be empty or invalid")
        
        print(f"📋 CSV Headers detected: {headers}")
        
        # Check if we have the enhanced format
        has_enhanced_format = all(field in headers for field in ['url', 'name', 'requiresAuth', 'mfaTemplate'])
        
        if has_enhanced_format:
            print("✅ Enhanced CSV format detected with SSO support")
        else:
            print("ℹ️ Simple CSV format detected, treating all URLs as public")
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
            try:
                if has_enhanced_format:
                    config = TestConfig.from_csv_row(row)
                else:
                    # Simple format - just URL column
                    url = row.get('url', list(row.values())[0] if row.values() else '').strip()
                    if not url:
                        continue
                    config = TestConfig(
                        url=url,
                        name=f"Page {row_num - 1}",
                        requires_auth=False,
                        mfa_template=""
                    )
                
                if config.url:  # Only add if URL is not empty
                    configs.append(config)
                    auth_status = "🔒 Private" if config.requires_auth else "🌐 Public"
                    template_info = f" ({config.mfa_template})" if config.mfa_template else ""
                    print(f"   {auth_status}: {config.url}{template_info}")
                
            except Exception as e:
                print(f"⚠️ Warning: Could not parse row {row_num}: {e}")
                continue
    
    print(f"📊 Loaded {len(configs)} test configurations")
    return configs

def load_urls_from_csv(csv_path: str) -> List[str]:
    """
    Legacy function for backward compatibility
    Returns just the URLs from the CSV
    """
    configs = load_enhanced_csv(csv_path)
    return [config.url for config in configs]
