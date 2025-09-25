import asyncio
import argparse
import json
import csv
from agent.agent import Agent, Config
from agent.crawler import Crawler
from agent.local_analyzer import LocalAnalyzer
from agent.reporter import ReportGenerator

def load_config(config_path: str) -> dict:
    """Loads the configuration from a JSON file."""
    if config_path:
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def load_urls_from_csv(csv_path: str) -> list[str]:
    """Loads a list of URLs from a CSV file."""
    urls = []
    with open(csv_path, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        for row in reader:
            if row:
                urls.append(row[0])
    return urls

async def main(url: str, max_pages: int, config_path: str, csv_path: str, device_type: str = None, device_name: str = None):
    """
    Main function to run the local accessibility test agent.
    """
    config_data = load_config(config_path)
    urls_to_test = []

    if csv_path:
        print(f"Loading URLs from {csv_path}...")
        urls_to_test = load_urls_from_csv(csv_path)
        if not urls_to_test:
            raise ValueError("CSV file is empty or could not be read.")
        # Use the first URL from CSV as the base_url if no explicit url is given
        if not url:
            url = urls_to_test[0]
    
    # CLI arguments override config file settings
    if url:
        config_data['base_url'] = url
    if max_pages is not None:
        config_data['max_pages'] = max_pages
    if device_type:
        config_data['device_types'] = [device_type]
    
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

    config = Config(
        base_url=config_data.pop('base_url'),
        **config_data
    )
    
    # Initialize components
    crawler = Crawler(base_url=config.base_url, max_pages=config.max_pages)
    analyzer = LocalAnalyzer(axe_rules=config.axe_rules)
    reporter = ReportGenerator()

    # Inject components into the agent
    agent = Agent(config, crawler, analyzer, reporter, urls_to_test=urls_to_test or None)
    await agent.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Automated Accessibility Testing Agent.")
    parser.add_argument("url", type=str, nargs='?', default=None, help="The base URL of the website to test (overrides config). Not required if using --csv.")
    parser.add_argument("--max-pages", type=int, default=None, help="The maximum number of pages to crawl and test (overrides config).")
    parser.add_argument("--config", type=str, default="config.json", help="Path to the configuration file.")
    parser.add_argument("--csv", type=str, default=None, help="Path to a CSV file containing a list of URLs to test.")
    parser.add_argument("--device", type=str, choices=["desktop", "mobile-ios", "mobile-android", "tablet-ios", "tablet-android"], default=None, help="Specific device type to test (overrides config).")
    parser.add_argument("--device-name", type=str, default=None, help="Specific device name to test (requires --device).")
    
    args = parser.parse_args()
    
    # Validate device-name requires device
    if args.device_name and not args.device:
        parser.error("--device-name requires --device to be specified")
    
    asyncio.run(main(args.url, args.max_pages, args.config, args.csv, args.device, args.device_name))
