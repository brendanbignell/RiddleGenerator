import os
import json
from anthropic import Anthropic
from openai import OpenAI
from google.generativeai import configure, GenerativeModel
from groq import Groq
from icecream import ic
import google.generativeai as genai
from IPython.display import Markdown

class RiddleGenerator:
    def __init__(self):
        """Initialize RiddleGenerator with API clients"""
        # Load config and set up clients
        self.config = self._load_config()
        self.clients = self._initialize_clients()
        
        # Define the prompt for generating riddles
        self.prompt = """Generate a riddle and its answer in JSON format with two fields: 'riddle' and 'answer'.
            The riddle should be clever and engaging, suitable for all ages.
            Example format:
            {
                "riddle": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. I have roads, but no cars. What am I?",
                "answer": "A map"
            }"""

    def _load_config(self):
        """Load configuration from config/llm_config.json"""
        try:
            with open('config/llm_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Config file not found at config/llm_config.json: {e}")

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
        """Get a riddle from the specified provider and model
        
        Args:
            provider (str): The provider name ('anthropic' or 'openai')
            model (str): The model name (e.g., 'claude-3-haiku' or 'gpt-4')
        """

        result = None

        try:
            ic(f"{provider}: {model}")
            
            if provider == "anthropic":
                client = self.clients.get(provider)
                response = client.messages.create(
                    model=model,
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": self.prompt
                    }]
                )
                content = response.content[0].text
                result = json.loads(content)
                return result
            
            elif provider == "openai":
                client = self.clients.get(provider)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": self.prompt
                    }]
                )
                content = response.choices[0].message.content
                # Extract JSON from the response text
                import re
                json_match = re.search(r'\{.*?\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                raise Exception(f"Could not find JSON in response: {content}")
            
            elif provider == "google":
                client = self.clients.get(provider)
                #ic(response)
                # Ensure the response is properly formatted as JSON
                response = client.generate_content(self.prompt)                
                # Handle potential errors in the response
                if response.text is None or response.text.strip() == "":
                    raise Exception("Empty response from Gemini")
                
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                raise Exception(f"Could not find JSON in Gemini response: {response.text}")
            
            elif provider == "groq":
                client = self.clients.get(provider)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": self.prompt
                    }]
                )
                content = response.choices[0].message.content
                # Extract JSON from the response text
                import re
                json_match = re.search(r'\{.*?\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                raise Exception(f"Could not find JSON in response: {content}")

            return result

        except Exception as e:
            raise Exception(f"Error generating riddle with {provider}: {str(e)}") 