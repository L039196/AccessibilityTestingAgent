import asyncio
import argparse
import os
from agent.controller import BrowserController
from agent.analyzer import MultimodalAnalyzer
from agent.reporter import ReportGenerator
from agent.environment import WebsiteEnv
from agent.rl_agent import SimpleRLAgent

async def main(url: str, api_key: str, max_steps: int = 10):
    """
    Main function to run the accessibility test agent.
    """
    print("Starting Accessibility Test Agent with RL...")

    # 1. Initialize components
    browser_controller = BrowserController()
    analyzer = MultimodalAnalyzer(api_key=api_key)
    reporter = ReportGenerator(report_format="md")
    env = WebsiteEnv(start_url=url, analyzer=analyzer, controller=browser_controller)
    
    try:
        # 2. Reset environment and initialize agent
        observation, info = await env.async_reset()
        agent = SimpleRLAgent(env.action_space)
        
        total_reward = 0
        all_issues = ""

        # 3. RL Training Loop
        for step in range(max_steps):
            print(f"--- Step {step + 1}/{max_steps} ---")
            
            # Agent chooses an action
            agent.set_action_space(env.action_space)
            action = agent.choose_action()
            
            # Environment performs the action
            observation, reward, done, truncated, info = await env.async_step(action)
            
            # Agent learns from the reward
            agent.update_q_table(action, reward)
            
            total_reward += reward
            
            # Collect issues if any were found
            if info.get("issues_found", 0) > 0:
                # Re-analyze to get the detailed report for the main report
                issues_report = await analyzer.find_contextual_issues(env.current_page_data)
                all_issues += f"\n\n### Issues found on {env.page.url}\n\n{issues_report}"

            if done:
                print("Episode finished.")
                # In a more complex scenario, we might not break here,
                # but reset to a new page or state.
                break
        
        # 4. Generate and save the final report
        print("Generating final report...")
        report_content = reporter.generate_report(url, all_issues)
        report_filename = "accessibility_rl_report.md"
        reporter.save_report(report_content, report_filename)
        print(f"Report saved to {os.path.abspath(report_filename)}")
        print(f"Total reward: {total_reward}")

    finally:
        # 5. Clean up
        await env.async_close()
        print("Agent finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Automated Accessibility Testing Agent.")
    parser.add_argument("url", type=str, help="The URL of the website to test.")
    parser.add_argument("--api-key", type=str, default=os.environ.get("GOOGLE_API_KEY"),
                        help="Your Google API key for the generative model. Defaults to GOOGLE_API_KEY environment variable.")
    parser.add_argument("--max-steps", type=int, default=10, help="Maximum steps for the RL agent to explore.")
    
    args = parser.parse_args()

    if not args.api_key:
        raise ValueError("API key must be provided either via --api-key argument or GOOGLE_API_KEY environment variable.")

    asyncio.run(main(args.url, args.api_key, args.max_steps))
