from riddle_generator import RiddleGenerator
import pandas as pd
from icecream import ic
from difflib import SequenceMatcher
import re
import random

class RiddleCompetition:
    def __init__(self):
        self.generator = RiddleGenerator()
        # Separate scores for word and math riddles
        self.scores = {
            "groq": {"word": 0, "math": 0},
            "openai": {"word": 0, "math": 0},
            "google": {"word": 0, "math": 0},
            "anthropic": {"word": 0, "math": 0}
        }
        self.riddles_per_llm = 10  # 5 word riddles, 5 math riddles
        self.used_riddles = []
        
    def _is_similar_riddle(self, new_riddle, similarity_threshold=0.7):
        """Check if a riddle is too similar to previously used ones"""
        # Clean and normalize the riddle text
        new_riddle = re.sub(r'[^\w\s]', '', new_riddle.lower())
        
        for old_riddle in self.used_riddles:
            old_riddle = re.sub(r'[^\w\s]', '', old_riddle.lower())
            similarity = SequenceMatcher(None, new_riddle, old_riddle).ratio()
            if similarity > similarity_threshold:
                return True
        return False

    def _get_unique_riddle(self, provider, model, riddle_type, max_attempts=3):
        """Get a unique riddle of specified type"""
        attempts = 0
        last_error = None
        
        while attempts < max_attempts:
            try:
                self.generator.prompt = self.generator.prompts[riddle_type]
                riddle_data = self.generator.get_riddle(provider, model)
                if not self._is_similar_riddle(riddle_data['riddle']):
                    self.used_riddles.append(riddle_data['riddle'])
                    return riddle_data
                ic(f"Attempt {attempts + 1}: Riddle was too similar, trying again...")
            except Exception as e:
                last_error = e
                ic(f"Attempt {attempts + 1} failed: {str(e)}")
            attempts += 1
            
        raise Exception(f"Failed to generate unique {riddle_type} riddle after {max_attempts} attempts. Last error: {str(last_error)}")

    def run_competition(self):
        """Run the riddle competition between LLMs"""
        results = []
        
        # Each LLM takes turns being the riddler
        for riddler_provider, riddler_model in self._get_llm_configs():
            ic(f"\n=== {riddler_provider} is asking riddles ===")
            
            # Alternate between word and math riddles
            for round_num in range(self.riddles_per_llm):
                riddle_type = "word" if round_num < self.riddles_per_llm/2 else "math"
                ic(f"\nRound {round_num + 1} - {riddle_type.upper()} RIDDLE")
                
                # Get a unique riddle from the riddler
                riddle_data = self._get_unique_riddle(riddler_provider, riddler_model, riddle_type)
                riddle = riddle_data['riddle']
                correct_answer = riddle_data['answer']
                solution = riddle_data.get('solution', '')  # Only present for math riddles
                
                ic(f"Riddle: {riddle}")
                ic(f"Correct Answer: {correct_answer}")
                if solution:
                    ic(f"Solution: {solution}")
                
                # Each other LLM tries to solve it
                for solver_provider, solver_model in self._get_llm_configs():
                    if solver_provider != riddler_provider:
                        # Get the solver's answer
                        prompt = f"Answer this {riddle_type} riddle with just the answer, no explanation: {riddle}"
                        response = self.generator.get_raw_response(solver_provider, solver_model, prompt)
                        ic(f"{solver_provider} answered: {response}")
                        
                        # Ask riddler to evaluate the answer
                        eval_prompt = f"""Given the {riddle_type} riddle: "{riddle}"
                            The correct answer is: "{correct_answer}"
                            The proposed answer is: "{response}"
                            Is this answer correct? Reply with only 'yes' or 'no'."""
                        
                        evaluation = self.generator.get_raw_response(
                            riddler_provider, riddler_model, eval_prompt).lower().strip()
                        
                        # Record the result
                        is_correct = evaluation == 'yes'
                        if is_correct:
                            self.scores[solver_provider][riddle_type] += 1
                        
                        results.append({
                            'Round': round_num + 1,
                            'Type': riddle_type,
                            'Riddler': riddler_provider,
                            'Solver': solver_provider,
                            'Riddle': riddle,
                            'Correct Answer': correct_answer,
                            'Solution': solution if riddle_type == 'math' else '',
                            'Given Answer': response,
                            'Is Correct': is_correct
                        })

        return self._generate_report(results)

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