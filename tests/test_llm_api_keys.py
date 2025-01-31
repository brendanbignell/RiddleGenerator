import unittest
import json
import os
from typing import Dict, Any
import requests
from anthropic import Anthropic
import google.generativeai as genai
from openai import OpenAI
from groq import Groq

class TestLLMApiKeys(unittest.TestCase):
    def setUp(self):
        # Load configuration
        with open('config/llm_config.json', 'r') as f:
            self.config = json.load(f)

    def test_api_keys(self):
        for llm in self.config['llm_configs']:
            provider = llm['provider']
            model = llm['model']
            env_var = llm['env_var']
            api_key = os.getenv(env_var)

            print(f"\nTesting {provider.upper()} API key for model: {model}")
            
            if not api_key:
                print(f"❌ No API key found for {provider} (Environment variable: {env_var})")
                continue

            try:
                # Test each provider's API key
                if provider == "anthropic":
                    client = Anthropic(api_key=api_key)
                    client.messages.create(
                        model=model,
                        max_tokens=10,
                        messages=[{"role": "user", "content": [ {"type": "text", "text": "Hi"} ]}]
                    )
                
                elif provider == "openai":
                    client = OpenAI(api_key=api_key)
                    client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=10
                    )
                
                elif provider == "google":
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model)
                    model.generate_content("Hi")
                
                elif provider == "groq":
                    client = Groq(api_key=api_key)
                    client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=10
                    )
                
                print(f"✅ Valid API key for {provider}")
            
            except Exception as e:
                print(f"❌ Invalid API key for {provider}: {str(e)}")

if __name__ == '__main__':
    unittest.main()
    