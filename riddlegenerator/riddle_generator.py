import os
import json
from anthropic import Anthropic
from openai import OpenAI
from groq import Groq
import google.generativeai as genai
from icecream import ic
import re
from pathlib import Path

class RiddleGenerator:
    def __init__(self):
        """Initialize RiddleGenerator with API clients"""
        # Load config and set up clients
        self.config = self._load_config()
        self.clients = self._initialize_clients()
        
        # Define prompts for different types of riddles
        self.prompts = {
            "word": """Generate a unique and original word riddle with its answer in JSON format. 
                The riddle should be:
                1. Different from common riddles (avoid classics like echo, wind, silence)
                2. Creative and unexpected
                3. Suitable for all ages
                4. Clear and logical
                
                Return in this exact JSON format:
                {
                    "type": "word",
                    "riddle": "Your unique riddle here",
                    "answer": "The answer"
                }""",
                
            "math": """You are a mathematical riddle creator. Generate ONLY mathematical riddles that involve numbers, calculations, or mathematical logic.
                The riddle MUST require mathematical calculation to solve.
                
                Examples of good math riddles:
                1. "In 2 years I will be twice as old as I was 5 years ago. How old am I?"
                2. "Three numbers add up to 30. The second number is twice the first, and the third is three times the first. What are the numbers?"
                3. "A train travels 120 miles at 60 mph. Another train travels the same route at 40 mph. How much earlier does the first train arrive?"
                
                DO NOT generate word riddles or riddles without numbers.
                
                Return in this exact JSON format:
                {
                    "type": "math",
                    "riddle": "Your mathematical riddle here",
                    "answer": "The numerical answer",
                    "solution": "Step by step explanation showing the calculations"
                }"""
        }
        
        # Default prompt is word riddle
        self.prompt = self.prompts["word"]

    def _load_config(self):
        """Load configuration from config/llm_config.json"""
        try:
            # Get the project root directory (two levels up from this file)
            root_dir = Path(__file__).parent.parent
            config_path = root_dir / 'config' / 'llm_config.json'
            
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Config file not found at {config_path}: {e}")

    def _initialize_clients(self):
        """Initialize API clients for each provider"""
        clients = {}
        
        for config in self.config["llm_configs"]:
            provider = config["provider"]
            api_key = os.getenv(config["env_var"])
            
            if not api_key:
                continue  # Skip if API key not found
                
            if provider == "anthropic":
                clients[provider] = Anthropic(api_key=api_key)
            elif provider == "openai":
                clients[provider] = OpenAI(api_key=api_key)
            elif provider == "groq":
                clients[provider] = Groq(api_key=api_key)
            elif provider == "google":
                genai.configure(api_key=api_key)
                clients[provider] = genai.GenerativeModel(model_name=config["model"])
                
        return clients

    def get_riddle(self, provider, model):
        """Get a riddle from the specified provider and model"""
        try:
            response_data = None
            max_attempts = 3
            
            for attempt in range(max_attempts):
                if "math" in self.prompt:
                    # For math riddles, verify it contains numbers
                    response = self._get_raw_riddle(provider, model)
                    response_data = self._extract_json(response)
                    
                    # Validate math riddle
                    if (any(char.isdigit() for char in response_data['riddle']) and 
                        any(char.isdigit() for char in response_data['answer'])):
                        break
                    ic(f"Attempt {attempt + 1}: Generated riddle was not mathematical enough, retrying...")
                else:
                    # For word riddles, just get the response
                    response = self._get_raw_riddle(provider, model)
                    response_data = self._extract_json(response)
                    break
                    
            if response_data is None:
                raise Exception("Failed to generate valid riddle after multiple attempts")
                
            return response_data
            
        except Exception as e:
            ic(e)
            raise

    def _get_raw_riddle(self, provider, model):
        """Get raw response from the model"""
        if provider == "openai":
            client = self.clients.get(provider)
            response = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": self.prompt
                },
                {
                    "role": "system",
                    "content": "For math riddles, you must include numbers and require calculation."
                }]
            )
            return response.choices[0].message.content
        elif provider == "anthropic":
            client = self.clients.get(provider)
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": self.prompt
                }]
            )
            return response.content[0].text
        elif provider == "google":
            client = self.clients.get(provider)
            response = client.generate_content(self.prompt)
            return response.text
        elif provider == "groq":
            client = self.clients.get(provider)
            response = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": self.prompt
                }]
            )
            return response.choices[0].message.content

    def _extract_json(self, content):
        """Extract and validate JSON from response"""
        import re
        json_match = re.search(r'\{.*?\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise Exception(f"Could not find JSON in response: {content}")

    def get_raw_response(self, provider, model, prompt):
        """Get a raw text response from the LLM"""
        try:
            if provider == "groq":
                response = self.clients[provider].chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content.strip()
                
            elif provider == "openai":
                response = self.clients[provider].chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content.strip()
                
            elif provider == "anthropic":
                response = self.clients[provider].messages.create(
                    model=model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
                
            elif provider == "google":
                response = self.clients[provider].generate_content(prompt)
                return response.text.strip()
                
        except Exception as e:
            ic(e)
            raise Exception(f"Error getting response from {provider}: {str(e)}") 
