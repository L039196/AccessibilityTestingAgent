import asyncio
import argparse
import json
import csv
import os
from dotenv import load_dotenv
from agent.agent import Agent, Config
from agent.crawler import Crawler
from agent.local_analyzer import LocalAnalyzer
from agent.reporter import ReportGenerator
from agent.csv_loader import load_enhanced_csv, load_urls_from_csv
from agent.s3_config_loader import S3ConfigLoader

# Load environment variables from .env file
load_dotenv()

def load_config(config_path: str) -> dict:
    """Loads the configuration from a JSON file."""
    if config_path:
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

async def main(url: str, max_pages: int, config_path: str, csv_path: str, device_type: str = None, device_name: str = None, headless: bool = None, parallel: bool = None, max_workers: int = None, additional_workers: int = None, use_sso: bool = False, sso_provider: str = None):
    """
    Main function to run the local accessibility test agent with SSO support.
    """
    config_data = load_config(config_path)
    test_configs = []

    if csv_path:
        print(f"Loading URLs from {csv_path}...")
        # Load enhanced CSV format with SSO support
        test_configs = load_enhanced_csv(csv_path)
        
        if not test_configs:
            raise ValueError("CSV file is empty or could not be read.")
        # Use the first URL from CSV as the base_url if no explicit url is given
        if not url:
            url = test_configs[0].url
    
    # CLI arguments override config file settings
    if url:
        config_data['base_url'] = url
    if max_pages is not None:
        config_data['max_pages'] = max_pages
    if device_type:
        config_data['device_types'] = [device_type]
    if headless is not None:
        config_data['headless'] = headless
    if parallel is not None:
        config_data['parallel'] = parallel
    if max_workers is not None:
        config_data['max_workers'] = max_workers
    if additional_workers is not None:
        config_data['additional_workers'] = additional_workers
    
    # Auto-enable SSO if any test requires auth
    if test_configs and any(tc.requires_auth for tc in test_configs):
        config_data['use_sso'] = True
        # Use the first mfa_template found, or default to 'lilly'
        mfa_template = next((tc.mfa_template for tc in test_configs if tc.mfa_template), 'lilly')
        config_data['sso_provider'] = sso_provider or mfa_template or 'lilly'
        print(f"🔐 SSO enabled automatically - detected auth requirement with provider: {config_data['sso_provider']}")
    elif use_sso:
        config_data['use_sso'] = True
        config_data['sso_provider'] = sso_provider or 'lilly'
        config_data['additional_workers_per_device'] = additional_workers
    
    # If device_name is specified, filter the device profiles
    if device_name and device_type:
        # Parse device type
        if device_type.startswith('mobile-'):
            form_factor = 'mobile'
            platform = device_type.replace('mobile-', '')
        elif device_type.startswith('tablet-'):
            form_factor = 'tablet'  
            platform = device_type.replace('tablet-', '')
        else:
            form_factor = device_type
            platform = None
            
        if 'device_profiles' in config_data:
            if platform and form_factor in config_data['device_profiles'] and platform in config_data['device_profiles'][form_factor]:
                # Keep only the specified device
                if device_name in config_data['device_profiles'][form_factor][platform]:
                    config_data['device_profiles'][form_factor][platform] = {
                        device_name: config_data['device_profiles'][form_factor][platform][device_name]
                    }
                else:
                    available_devices = list(config_data['device_profiles'][form_factor][platform].keys())
                    raise ValueError(f"Device '{device_name}' not found in {form_factor}-{platform} devices. Available: {available_devices}")
            elif not platform and form_factor in config_data['device_profiles']:
                # Desktop case
                if device_name in config_data['device_profiles'][form_factor]:
                    config_data['device_profiles'][form_factor] = {
                        device_name: config_data['device_profiles'][form_factor][device_name]
                    }
                else:
                    available_devices = list(config_data['device_profiles'][form_factor].keys())
                    raise ValueError(f"Device '{device_name}' not found in {form_factor} devices. Available: {available_devices}")

    if 'base_url' not in config_data:
        raise ValueError("The base URL must be provided either via a command-line argument, a CSV file, or in the config file.")

    # Load S3 configuration
    s3_config = S3ConfigLoader.load_config()
    is_valid, error_msg = S3ConfigLoader.validate_config(s3_config)
    
    if s3_config.get('enabled') and not is_valid:
        print(f"⚠️ S3 configuration error: {error_msg}")
        print("ℹ️ Continuing with local storage only")
        s3_config['enabled'] = False
    
    # Debug: Print config_data to see what's being passed
    print("🔍 Debug - config_data keys:", list(config_data.keys()))

    config = Config(
        base_url=config_data.pop('base_url'),
        **config_data
    )
    
    # Merge S3 configuration into agent config
    config = S3ConfigLoader.merge_with_agent_config(config, s3_config)
    
    if config.enable_s3_storage:
        print(f"✅ S3 storage enabled - Bucket: {config.s3_bucket_name}")
        print(f"📍 Region: {config.s3_region}")
    else:
        print("ℹ️ S3 storage disabled - using local storage")
    
    # Initialize components
    crawler = Crawler(base_url=config.base_url, max_pages=config.max_pages)
    analyzer = LocalAnalyzer(axe_rules=config.axe_rules)
    reporter = ReportGenerator()

    # Inject components into the agent - pass TestConfig objects directly
    agent = Agent(config, crawler, analyzer, reporter, urls_to_test=test_configs or None)
    await agent.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Automated Accessibility Testing Agent.")
    parser.add_argument("url", type=str, nargs='?', default=None, help="The base URL of the website to test (overrides config). Not required if using --csv.")
    parser.add_argument("--max-pages", type=int, default=None, help="The maximum number of pages to crawl and test (overrides config).")
    parser.add_argument("--config", type=str, default="config.json", help="Path to the configuration file.")
    parser.add_argument("--csv", type=str, default=None, help="Path to a CSV file containing a list of URLs to test.")
    parser.add_argument("--device", type=str, choices=["desktop", "mobile-ios", "mobile-android", "tablet-ios", "tablet-android"], default=None, help="Specific device type to test (overrides config).")
    parser.add_argument("--device-name", type=str, default=None, help="Specific device name to test (requires --device).")
    parser.add_argument("--headless", type=str, choices=["true", "false"], default=None, help="Run browser in headless mode (true) or headed mode (false).")
    parser.add_argument("--parallel", type=str, choices=["true", "false"], default=None, help="Run tests in parallel (true) or sequential (false) mode.")
    parser.add_argument("--max-workers", type=int, default=None, help="Maximum number of parallel worker browsers (default: 8).")
    parser.add_argument("--additional-workers", type=int, default=None, help="Additional workers per device for parallelization (default: 2).")
    parser.add_argument("--sso", action="store_true", help="Enable SSO authentication for testing authenticated pages.")
    parser.add_argument("--sso-provider", type=str, choices=["lilly", "microsoft", "okta", "auth0"], default="lilly", help="SSO provider to use (default: lilly).")
    parser.add_argument("--headed", action="store_true", help="Run browsers in headed mode (visible). Default is headless.")
    
    args = parser.parse_args()
    
    # Validate device-name requires device
    if args.device_name and not args.device:
        parser.error("--device-name requires --device to be specified")
    
    # Convert headless string to boolean, or handle --headed flag
    headless = None
    if args.headless:
        headless = args.headless.lower() == "true"
    elif args.headed:
        headless = False  # --headed means not headless
    
    # Convert parallel string to boolean
    parallel = None
    if args.parallel:
        parallel = args.parallel.lower() == "true"
    
    asyncio.run(main(args.url, args.max_pages, args.config, args.csv, args.device, args.device_name, headless, parallel, args.max_workers, args.additional_workers, args.sso, args.sso_provider))
