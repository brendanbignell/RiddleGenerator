import os
import json
from anthropic import Anthropic
from openai import OpenAI
from groq import Groq
import google.generativeai as genai
from icecream import ic
import re
from pathlib import Path
from difflib import SequenceMatcher

class RiddleGenerator:
    def __init__(self):
        """Initialize RiddleGenerator with API clients"""
        self.config = self._load_config()
        self.clients = self._initialize_clients()
        self.used_riddles = []  # Track used riddles
        
        # Define prompts for different types of riddles
        self.prompts = {
            "word": """Generate a unique and original word riddle with its answer in JSON format. 
                Return in this exact JSON format with no additional text:
                {
                    "type": "word",
                    "riddle": "Your unique riddle here",
                    "answer": "The answer"
                }""",
                
            "math": """Generate a simple arithmetic problem with exact numbers.
                Return in this exact JSON format with no additional text:
                {
                    "type": "math",
                    "riddle": "Your math problem here",
                    "answer": "The numerical answer",
                    "solution": "Brief step-by-step solution"
                }"""
        }
        
        self.prompt = self.prompts["word"]  # Default prompt

    def _load_config(self):
        """Load configuration from config/llm_config.json"""
        try:
            root_dir = Path(__file__).parent.parent
            config_path = root_dir / 'config' / 'llm_config.json'
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    def _initialize_clients(self):
        """Initialize API clients"""
        try:
            clients = {}
            for config in self.config['llm_configs']:
                provider = config['provider']
                if provider == "anthropic":
                    clients[provider] = Anthropic(api_key=config['api_key'])
                elif provider == "openai":
                    clients[provider] = OpenAI(api_key=config['api_key'])
                elif provider == "groq":
                    clients[provider] = Groq(api_key=config['api_key'])
                elif provider == "google":
                    genai.configure(api_key=config['api_key'])
                    clients[provider] = genai
            return clients
        except Exception as e:
            raise Exception(f"Failed to initialize clients: {str(e)}")

    def _normalize_text(self, text):
        """Normalize text for comparison"""
        text = str(text).lower()
        text = re.sub(r'[^\w\s]', '', text)
        filler_words = ['i', 'am', 'a', 'an', 'the', 'but', 'and', 'or', 'what']
        words = text.split()
        words = [w for w in words if w not in filler_words]
        return ' '.join(words)

    def _is_similar_riddle(self, new_riddle, similarity_threshold=0.6):
        """Check if a riddle is too similar to previously used ones"""
        normalized_new = self._normalize_text(new_riddle)
        key_words = set(normalized_new.split())
        
        for old_riddle in self.used_riddles:
            normalized_old = self._normalize_text(old_riddle)
            old_words = set(normalized_old.split())
            
            common_words = key_words.intersection(old_words)
            if len(common_words) >= 3:
                return True
                
            similarity = SequenceMatcher(None, normalized_new, normalized_old).ratio()
            if similarity > similarity_threshold:
                return True
                
        return False

    def _extract_json(self, content):
        """Extract and validate JSON from response"""
        try:
            # Clean the content
            content = content.strip()
            start = content.find("{")
            end = content.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found")
            
            json_str = content[start:end]
            json_str = re.sub(r'\s+', ' ', json_str)
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate required fields
            if "type" not in data or "riddle" not in data or "answer" not in data:
                raise ValueError("Missing required fields")
                
            return data
            
        except Exception as e:
            ic(f"JSON parsing error: {str(e)}\nContent: {content}")
            raise

    def get_riddle(self, provider, model):
        """Get a riddle from the specified provider"""
        response = self._get_raw_riddle(provider, model)
        return self._extract_json(response)

    def _get_raw_riddle(self, provider, model, temperature=0.7):
        """Get raw response from the model"""
        try:
            if provider == "google":
                client = self.clients.get(provider)
                response = client.generate_content(self.prompt)
                return response.text
                
            elif provider == "groq":
                client = self.clients.get(provider)
                response = client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=[{"role": "user", "content": self.prompt}]
                )
                return response.choices[0].message.content
                
            elif provider == "openai":
                client = self.clients.get(provider)
                response = client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=[{"role": "user", "content": self.prompt}]
                )
                return response.choices[0].message.content
                
            elif provider == "anthropic":
                client = self.clients.get(provider)
                response = client.messages.create(
                    model=model,
                    temperature=temperature,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": self.prompt}]
                )
                return response.content[0].text
                
        except Exception as e:
            ic(f"Error getting response from {provider}: {str(e)}")
            raise

    def get_raw_response(self, provider, model, prompt):
        """Get a raw response for answer evaluation"""
        return self._get_raw_riddle(provider, model, temperature=0.3)
