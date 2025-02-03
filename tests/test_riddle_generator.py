from unittest.mock import Mock, patch
from riddlegenerator.riddle_generator import RiddleGenerator
import unittest
import json
from icecream import ic

class TestRiddleGenerator(unittest.TestCase):
    """Test cases for RiddleGenerator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = RiddleGenerator()
    
    def test_get_riddle_gemini(self):
        """Test getting a riddle from Gemini"""
        result = self.generator.get_riddle("google", "gemini-1.5-flash")
        self.assertIn('riddle', result)
        self.assertIn('answer', result)
        ic(result['riddle'])
        ic(result['answer'])

    def test_get_riddle_groq(self):
        """Test getting a riddle from Groq"""
        result = self.generator.get_riddle("groq", "llama3-8b-8192")
        self.assertIn('riddle', result)
        self.assertIn('answer', result)
        ic(result['riddle'])
        ic(result['answer'])
 
    def test_get_riddle_anthropic(self):
        """Test getting a riddle from Claude"""
        result = self.generator.get_riddle("anthropic", "claude-3-5-haiku-latest")
        self.assertIn('riddle', result)
        self.assertIn('answer', result)
        ic(result['riddle'])
        ic(result['answer'])
    
    def test_get_riddle_openai(self):
        """Test getting a riddle from OpenAI"""
        result = self.generator.get_riddle("openai", "gpt-4o-mini-2024-07-18")
        self.assertIn('riddle', result)
        self.assertIn('answer', result)
        ic(result['riddle'])
        ic(result['answer'])

if __name__ == '__main__':
    unittest.main() 