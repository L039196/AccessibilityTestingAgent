import asyncio
import gymnasium as gym
from agent.controller import BrowserController
from agent.analyzer import MultimodalAnalyzer
import numpy as np
from PIL import Image
import io

class WebsiteEnv(gym.Env):
    """A custom Gym environment for website accessibility testing."""
    def __init__(self, start_url: str, analyzer: MultimodalAnalyzer, controller: BrowserController):
        super().__init__()
        self.start_url = start_url
        self.browser_controller = controller
        self.analyzer = analyzer
        self.page = None
        
        # Action space: dynamically determined by the number of interactive elements
        self.action_space = gym.spaces.Discrete(1) # Start with 1 (scroll)
        self.observation_space = gym.spaces.Dict({
            "screenshot": gym.spaces.Box(low=0, high=255, shape=(720, 1280, 3), dtype=np.uint8),
        })
        self.current_page_data = None
        self.interactive_elements = []
        self.visited_states = set()

    async def async_reset(self):
        """Asynchronous reset method."""
        if not self.browser_controller.browser:
            await self.browser_controller.start()
        
        if self.page:
            await self.page.close()
            
        self.page = await self.browser_controller.browser.new_page()
        self.current_page_data = await self.browser_controller.capture_page_data(self.start_url)
        self.visited_states.add(self.current_page_data['dom'])
        
        await self._update_state()
        
        return self._get_observation(), {}

    async def async_step(self, action: int):
        """Asynchronous step method."""
        # Perform the action
        await self.browser_controller.perform_action(self.page, action, self.interactive_elements)
        
        # Get new state
        self.current_page_data = await self.browser_controller.capture_page_data(self.page.url)
        
        # Calculate reward
        reward = 0
        new_issues_found = 0
        
        if self.current_page_data['dom'] not in self.visited_states:
            self.visited_states.add(self.current_page_data['dom'])
            issues_report = await self.analyzer.find_contextual_issues(self.current_page_data)
            new_issues_found = len(issues_report.split("Issue:")) -1
            reward += new_issues_found * 10 # High reward for new issues
            reward += 1 # Small reward for discovering a new state
        else:
            reward -= 5 # Penalty for revisiting a state
            
        await self._update_state()
        
        # For now, we end the episode after one step for simplicity
        done = True
        
        return self._get_observation(), reward, done, False, {"issues_found": new_issues_found}

    async def _update_state(self):
        """Update interactive elements and action space."""
        self.interactive_elements = await self.browser_controller.get_interactive_elements(self.current_page_data['dom'])
        num_actions = len(self.interactive_elements) + 1 # +1 for scroll
        self.action_space = gym.spaces.Discrete(num_actions)

    def _get_observation(self):
        """Processes page data into an observation."""
        screenshot_bytes = self.current_page_data['screenshot']
        img = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        img = img.resize((1280, 720))
        
        return { "screenshot": np.array(img) }

    async def async_close(self):
        """Asynchronous close method."""
        if self.page:
            await self.page.close()
        await self.browser_controller.stop()

    # Sync wrappers for Gym compatibility if needed, though we'll call async methods directly
    def reset(self, **kwargs):
        return asyncio.run(self.async_reset())

    def step(self, action):
        return asyncio.run(self.async_step(action))

    def close(self):
        return asyncio.run(self.async_close())
