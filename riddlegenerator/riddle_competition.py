from riddlegenerator.riddle_generator import RiddleGenerator
import pandas as pd
from icecream import ic
from difflib import SequenceMatcher
import re
import random

class RiddleCompetition:
    def __init__(self, riddles_per_llm=10):
        self.generator = RiddleGenerator()
        # Separate scores for word and math riddles
        self.scores = {
            "groq": {"word": 0, "math": 0},
            "openai": {"word": 0, "math": 0},
            "google": {"word": 0, "math": 0},
            "anthropic": {"word": 0, "math": 0}
        }
        self.riddles_per_llm = riddles_per_llm  # Use the provided value
        self.used_riddles = []
        
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

    def _normalize_text(self, text):
        """Normalize text for comparison"""
        text = str(text).lower()
        text = re.sub(r'[^\w\s]', '', text)
        filler_words = ['i', 'am', 'a', 'an', 'the', 'but', 'and', 'or', 'what']
        words = text.split()
        words = [w for w in words if w not in filler_words]
        return ' '.join(words)

    def _get_unique_riddle(self, provider, model, riddle_type, max_attempts=3):
        """Get a unique riddle of specified type"""
        attempts = 0
        last_error = None
        
        while attempts < max_attempts:
            try:
                self.generator.prompt = self.generator.prompts[riddle_type]
                riddle_data = self.generator.get_riddle(provider, model)
                
                # Skip similarity check for math riddles
                if riddle_type == "math" or not self._is_similar_riddle(riddle_data['riddle']):
                    self.used_riddles.append(riddle_data['riddle'])
                    return riddle_data
                    
                ic(f"Attempt {attempts + 1}: Generated similar riddle, trying again...")
                
            except Exception as e:
                last_error = e
                ic(f"Attempt {attempts + 1} failed: {str(e)}")
                
            attempts += 1
            
        # If we failed to get a unique riddle, use a default one
        if riddle_type == "math":
            return {
                "type": "math",
                "riddle": f"If you have {random.randint(2, 10)} items and multiply them by {random.randint(2, 5)}, how many do you have?",
                "answer": str(random.randint(4, 50)),
                "solution": "Multiply the numbers"
            }
        else:
            return {
                "type": "word",
                "riddle": "I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I?",
                "answer": "An echo"
            }

    def run_competition(self):
        """Run the riddle competition between LLMs"""
        results = []
        active_providers = set()  # Track which providers are still active
        
        # Each LLM takes turns being the riddler
        for riddler_provider, riddler_model in self._get_llm_configs():
            try:
                ic(f"\n=== {riddler_provider} is asking riddles ===")
                active_providers.add(riddler_provider)
                
                # Ask specified number of riddles
                for round_num in range(self.riddles_per_llm):
                    ic(f"\nRound {round_num + 1}")
                    
                    try:
                        # Get a unique riddle from the riddler
                        riddle_data = self._get_unique_riddle(riddler_provider, riddler_model, 
                            "word" if round_num < self.riddles_per_llm/2 else "math")
                        riddle = riddle_data['riddle']
                        correct_answer = riddle_data['answer']
                        solution = riddle_data.get('solution', '')
                        
                        ic(f"Riddle: {riddle}")
                        ic(f"Correct Answer: {correct_answer}")
                        if solution:
                            ic(f"Solution: {solution}")
                        
                        # Each other LLM tries to solve it
                        for solver_provider, solver_model in self._get_llm_configs():
                            if solver_provider != riddler_provider and solver_provider in active_providers:
                                try:
                                    # Get the solver's answer
                                    prompt = f"Answer this riddle with just the answer, no explanation: {riddle}"
                                    response = self.generator.get_raw_response(solver_provider, solver_model, prompt)
                                    ic(f"{solver_provider} answered: {response}")
                                    
                                    # Record the result
                                    results.append({
                                        'Round': round_num + 1,
                                        'Type': riddle_data['type'],
                                        'Riddler': riddler_provider,
                                        'Solver': solver_provider,
                                        'Riddle': riddle,
                                        'Correct Answer': correct_answer,
                                        'Solution': solution,
                                        'Given Answer': response,
                                        'Is Correct': self._check_answer(response, correct_answer)
                                    })
                                    
                                except Exception as e:
                                    ic(f"Error with solver {solver_provider}: {str(e)}")
                                    active_providers.discard(solver_provider)
                                    ic(f"{solver_provider} has been removed from the competition")
                                    
                    except Exception as e:
                        ic(f"Error in round {round_num + 1}: {str(e)}")
                        continue
                        
            except Exception as e:
                ic(f"Error with riddler {riddler_provider}: {str(e)}")
                active_providers.discard(riddler_provider)
                ic(f"{riddler_provider} has been removed from the competition")
                
        return self._generate_report(results)

    def _check_answer(self, given_answer, correct_answer):
        """Check if the given answer matches the correct answer"""
        # Normalize both answers for comparison
        given = self._normalize_text(str(given_answer))
        correct = self._normalize_text(str(correct_answer))
        
        # For math riddles, extract numbers and compare
        if any(char.isdigit() for char in correct):
            given_nums = re.findall(r'\d+', given)
            correct_nums = re.findall(r'\d+', correct)
            return given_nums == correct_nums
            
        # For word riddles, check if answers are similar enough
        return SequenceMatcher(None, given, correct).ratio() > 0.8

    def _get_llm_configs(self):
        """Get list of (provider, model) tuples from config"""
        return [(config['provider'], config['model']) 
                for config in self.generator.config['llm_configs']]

    def _generate_report(self, results):
        """Generate a summary report of the competition"""
        # Create detailed results DataFrame
        df = pd.DataFrame(results)
        
        # Create summary tables for each riddle type
        summaries = {}
        for riddle_type in ['word', 'math']:
            total_questions = len(self._get_llm_configs()) * (self.riddles_per_llm/2) - (self.riddles_per_llm/2)
            summary = pd.DataFrame({
                'LLM': list(self.scores.keys()),
                f'{riddle_type.capitalize()} Riddles Correct': [scores[riddle_type] for scores in self.scores.values()],
                'Total Questions': [total_questions] * len(self.scores),
            })
            summary[f'{riddle_type.capitalize()} Success Rate'] = (
                summary[f'{riddle_type.capitalize()} Riddles Correct'] / summary['Total Questions'] * 100
            ).round(2)
            summary = summary.sort_values(f'{riddle_type.capitalize()} Success Rate', ascending=False)
            summaries[riddle_type] = summary
        
        return {
            'detailed_results': df,
            'word_summary': summaries['word'],
            'math_summary': summaries['math']
        } 