import unittest
from riddlegenerator.riddle_generator import RiddleGenerator
from icecream import ic

class TestRiddleSolver(unittest.TestCase):
    def setUp(self):
        self.generator = RiddleGenerator()
        self.age_riddle = "In two years I will be twice as old as I was five years ago. How old am I?"
        self.correct_answer = "12"

    def test_age_riddle_solutions(self):
        """Test each model's ability to solve the age riddle"""
        results = {}
        
        # Test each provider
        for config in self.generator.config['llm_configs']:
            provider = config['provider']
            model = config['model']
            
            try:
                response = self.generator.get_raw_response(provider, model, self.age_riddle)
                # Clean up response (remove periods, convert to string)
                answer = str(response).strip().rstrip('.').lower()
                
                # Extract just the number if present
                import re
                numbers = re.findall(r'\d+', answer)
                if numbers:
                    answer = numbers[0]
                
                results[provider] = {
                    'answer': answer,
                    'correct': answer == self.correct_answer,
                    'error': None
                }
                
            except Exception as e:
                results[provider] = {
                    'answer': None,
                    'correct': False,
                    'error': str(e)
                }
        
        # Print results
        print("\nAge Riddle Test Results:")
        print(f"Riddle: {self.age_riddle}")
        print(f"Correct Answer: {self.correct_answer}\n")
        
        for provider, result in results.items():
            if result['error']:
                print(f"{provider}: Error - {result['error']}")
            else:
                print(f"{provider}: {'✓' if result['correct'] else '✗'} (answered: {result['answer']})")
        
        # Assert that at least one model got it right
        correct_answers = sum(1 for r in results.values() if r['correct'])
        self.assertGreater(correct_answers, 0, "None of the models solved the riddle correctly")

if __name__ == '__main__':
    unittest.main()