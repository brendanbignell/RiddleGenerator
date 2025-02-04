# Riddle generation and solving competition amongst multiple LLMs
Test using Cursor.AI as a development environment.  
A simple project to test used different LLMs together in a colaborative fashion.  

Generate riddles using multiple LLMs and test which LLM is the best at solving riddles.

You can install all dependencies with:
      `pip install -r requirements.txt`

Make sure you have your API keys set in your environment variables:

`OPENAI_API_KEY=your_key_here`

`ANTHROPIC_API_KEY=your_key_here`

`GROQ_API_KEY=your_key_here`

`GOOGLE_API_KEY=your_key_here`

## Example output:

`python run_competition.py`

=== groq is asking riddles ===  

Round 1  
Riddle: In the heart of darkness, I shine bright. I'm not a flame, though I can be warm. I can be a beacon, but I'm not a light. What am I?  
Correct Answer: A Star  
openai answered: A star.  
google answered: Hope  
anthropic answered: Hope  

Round 2  
Riddle: What is 6 x 9 - 3?  
Correct Answer: 51  
Solution: 6 x 9 = 54, then subtract 3 to get 51  
openai answered: 51  
google answered: 45  
anthropic answered: 51  

=== openai is asking riddles ===  

Round 1  
Riddle: I can be cracked, made, told, and played. What am I?  
Correct Answer: A joke  
groq answered: Joke.  
google answered: Joke  
anthropic answered: A joke  

Round 2  
Riddle: What is 15 + 27?  
Correct Answer: 42  
Solution: Add the two numbers together: 15 + 27 = 42.  
groq answered: 42  
google answered: 42  
anthropic answered: 42  

=== google is asking riddles ===  

Round 1  
Attempt 1: Generated similar riddle, trying again...  
Riddle: What is always coming, but never arrives?  
Correct Answer: Tomorrow  
groq answered: Tomorrow.  
openai answered: Tomorrow.  
anthropic answered: Tomorrow  

Round 2  
Riddle: What is 234 + 109?  
Correct Answer: 343  
Solution: Add the ones place: 4 + 9 = 13. Carry the 1 and add the tens place: 3 + 0 + 1 = 4. Add the hundreds place: 2 + 1 = 3.  
groq answered: 343  
openai answered: 343  
anthropic answered: 343  

=== anthropic is asking riddles ===  

Round 1  
Riddle: I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?  
Correct Answer: map  
groq answered: A map.  
openai answered: A map.  
google answered: A map  

Round 2  
Riddle: What is 17 × 6 + 23?  
Correct Answer: 125  
Solution: 1. Multiply 17 × 6 = 102, 2. Add 23 to 102, 3. Result is 125  
groq answered: 107  
openai answered: 145  
google answered: 127  

Word Riddles Summary:  
      LLM  Word Riddles Correct  Total Questions  Word Success Rate  
     groq                     3              3.0             100.00  
   openai                     3              3.0             100.00  
   google                     2              3.0              66.67  
anthropic                     2              3.0              66.67  

Math Riddles Summary:  
      LLM  Math Riddles Correct  Total Questions  Math Success Rate  
anthropic                     3              3.0             100.00  
     groq                     2              3.0              66.67  
   openai                     2              3.0              66.67  
   google                     1              3.0              33.33  

Detailed results saved to riddle_competition_results.csv  
