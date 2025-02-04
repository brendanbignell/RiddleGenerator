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
import random

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
                api_key = os.getenv(f"{provider.upper()}_API_KEY")
                
                if not api_key:
                    ic(f"Warning: No API key found for {provider}")
                    continue
                    
                try:
                    if provider == "anthropic":
                        clients[provider] = Anthropic(api_key=api_key)
                    elif provider == "openai":
                        clients[provider] = OpenAI(api_key=api_key)
                    elif provider == "groq":
                        clients[provider] = Groq(api_key=api_key)
                    elif provider == "google":
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-pro')
                        clients[provider] = model
                except Exception as e:
                    ic(f"Failed to initialize {provider}: {str(e)}")
                    continue
                    
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
            
            # Handle multi-line JSON by joining lines
            lines = content.split('\n')
            content = ' '.join(line.strip() for line in lines)
            
            # Find the first { and last }
            start = content.find("{")
            end = content.rfind("}") + 1
            if start == -1 or end <= 0:
                # Try to fix incomplete JSON by adding missing brace
                if start >= 0 and '"answer":' in content:
                    content = content + "}"
                    end = len(content)
                else:
                    raise ValueError("No JSON object found")
            
            # Extract and parse JSON
            json_str = content[start:end]
            # Remove any escaped quotes and normalize spacing
            json_str = json_str.replace('\\"', '"').replace('\\n', ' ')
            json_str = re.sub(r'\s+', ' ', json_str)
            
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common JSON formatting issues
                json_str = json_str.replace("'", '"')  # Replace single quotes with double quotes
                json_str = re.sub(r'([{,])\s*(\w+):', r'\1 "\2":', json_str)  # Quote unquoted keys
                data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["type", "riddle", "answer"]
            if not all(field in data for field in required_fields):
                raise ValueError(f"Missing required fields. Found: {list(data.keys())}")
            
            # Convert all values to strings
            result = {
                "type": str(data["type"]),
                "riddle": str(data["riddle"]).strip(),
                "answer": str(data["answer"]).strip()
            }
            
            # Add solution if present
            if "solution" in data:
                result["solution"] = str(data["solution"]).strip()
            
            return result
            
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

    def get_raw_response(self, provider, model, prompt, system_prompt=None):
        """Get raw response from the model with error handling"""
        try:
            if provider == "google":
                client = self.clients.get(provider)
                if system_prompt:
                    prompt = f"{system_prompt}\n\n{prompt}"
                response = client.generate_content(prompt)
                return response.text.strip()
                
            elif provider == "groq":
                client = self.clients.get(provider)
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                response = client.chat.completions.create(
                    model=model,
                    temperature=0.1,  # Lower temperature for math problems
                    messages=messages
                )
                return response.choices[0].message.content.strip()
                
            elif provider == "openai":
                client = self.clients.get(provider)
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                response = client.chat.completions.create(
                    model=model,
                    temperature=0.1,  # Lower temperature for math problems
                    messages=messages
                )
                return response.choices[0].message.content.strip()
                
            elif provider == "anthropic":
                client = self.clients.get(provider)
                response = client.messages.create(
                    model=model,
                    temperature=0.1,  # Lower temperature for math problems
                    max_tokens=1024,
                    system=system_prompt if system_prompt else None,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
                
        except Exception as e:
            ic(f"Error getting response from {provider}: {str(e)}")
            raise

    def _get_unique_riddle(self, provider, model, riddle_type, max_attempts=3):
        """Get a unique riddle of specified type"""
        attempts = 0
        last_error = None
        
        while attempts < max_attempts:
            try:
                self.generator.prompt = self.generator.prompts[riddle_type]
                riddle_data = self.generator.get_riddle(provider, model)
                
                # Skip similarity check for math riddles
                if riddle_type == "math" or not self.generator._is_similar_riddle(riddle_data['riddle']):
                    self.used_riddles.append(riddle_data['riddle'])
                    return riddle_data
                    
                ic(f"Attempt {attempts + 1}: Generated similar riddle, trying again...")
                
            except Exception as e:
                last_error = e
                ic(f"Attempt {attempts + 1} failed: {str(e)}")
                
            attempts += 1
            
        # If we failed to get a unique riddle, use a default one
        if riddle_type == "math":
            num1 = random.randint(2, 10)
            num2 = random.randint(2, 5)
            result = num1 * num2
            return {
                "type": "math",
                "riddle": f"If you have {num1} items and multiply them by {num2}, how many do you have?",
                "answer": str(result),  # Convert to string
                "solution": f"Multiply {num1} by {num2} to get {result}"
            }
        else:
            return {
                "type": "word",
                "riddle": "I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I?",
                "answer": "An echo"
            }
