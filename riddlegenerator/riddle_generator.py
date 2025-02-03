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
                
                Return in this exact JSON format without any additional text:
                {
                    "type": "word",
                    "riddle": "Your unique riddle here",
                    "answer": "The answer"
                }""",
                
            "math": """Generate a simple arithmetic problem with exact numbers that requires calculation.
                Rules:
                1. Must use specific numbers (not variables)
                2. Must involve basic arithmetic (+, -, *, /)
                3. Should be solvable in 2-3 steps
                4. Answer must be a number
                
                Examples:
                - "If a train travels 60 miles per hour for 2.5 hours, how far does it travel?"
                - "A store offers 20% off a $50 item. What is the final price?"
                - "Three friends split a $45 bill equally. How much does each person pay?"
                
                Return in this exact JSON format without any additional text or newlines in the solution:
                {
                    "type": "math",
                    "riddle": "Your math problem here",
                    "answer": "The numerical answer",
                    "solution": "Brief step-by-step solution"
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
                    # For math riddles, use higher temperature for diversity
                    response = self._get_raw_riddle(provider, model, temperature=0.9)
                    response_data = self._extract_json(response)
                    
                    # Validate math riddle
                    has_numbers = any(char.isdigit() for char in response_data['riddle'])
                    has_math_terms = any(term in response_data['riddle'].lower() 
                                       for term in ['$', '+', '-', '*', '/', '=', '%','plus', 'minus', 
                                                  'times', 'divided', 'multiply', 'add', 'subtract',
                                                  'percent', 'total', 'each', 'per', 'equals', 'many', 'long', 'much', 'count', 'total', 'sum', 'difference', 'product', 'quotient'])
                    
                    if has_numbers and has_math_terms:
                        # Clean up the answer to ensure it's numerical
                        answer = response_data['answer']
                        # Extract just the number from the answer
                        number = re.search(r'[-+]?\d*\.?\d+', str(answer))
                        if number:
                            response_data['answer'] = number.group()
                            break
                    ic(f"Attempt {attempt + 1}: Generated riddle was not mathematical enough, retrying...")
                else:
                    # For word riddles, use moderate temperature
                    response = self._get_raw_riddle(provider, model, temperature=0.7)
                    response_data = self._extract_json(response)
                    break
                    
            if response_data is None:
                raise Exception("Failed to generate valid riddle after multiple attempts")
                
            return response_data
            
        except Exception as e:
            ic(e)
            raise

    def _get_raw_riddle(self, provider, model, temperature=0.7):
        """Get raw response from the model with temperature control"""
        if provider == "openai":
            client = self.clients.get(provider)
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[{
                    "role": "user",
                    "content": self.prompt
                },
                {
                    "role": "system",
                    "content": "For math riddles, you must include numbers and mathematical operations."
                }]
            )
            return response.choices[0].message.content
            
        elif provider == "anthropic":
            client = self.clients.get(provider)
            response = client.messages.create(
                model=model,
                temperature=temperature,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": self.prompt
                }]
            )
            return response.content[0].text
            
        elif provider == "groq":
            client = self.clients.get(provider)
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[{
                    "role": "user",
                    "content": self.prompt
                }]
            )
            return response.choices[0].message.content
            
        elif provider == "google":
            client = self.clients.get(provider)
            response = client.generate_content(
                self.prompt,
                generation_config={"temperature": temperature}
            )
            return response.text

    def _extract_json(self, content):
        """Extract and validate JSON from response"""
        try:
            # Clean the content
            content = content.strip()
            # Remove any text before the first {
            content = content[content.find("{"):]
            # Remove any text after the last }
            content = content[:content.rfind("}") + 1]
            # Replace any newlines in the content with spaces
            content = content.replace("\n", " ")
            # Clean up multiple spaces
            content = " ".join(content.split())
            
            # Parse the JSON
            data = json.loads(content)
            
            # Validate required fields
            required_fields = ["type", "riddle", "answer"]
            if not all(field in data for field in required_fields):
                raise ValueError("Missing required fields in JSON response")
                
            return data
            
        except Exception as e:
            raise Exception(f"JSON parsing error: {str(e)}\nContent: {content}")

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
