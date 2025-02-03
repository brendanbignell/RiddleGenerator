import argparse
from icecream import ic
from riddlegenerator.riddle_competition import RiddleCompetition



def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Run an LLM riddle competition')
    parser.add_argument('--rounds', type=int, default=2,
                       help='Number of riddles each LLM will ask (default: 2)')
    parser.add_argument('--output', type=str, default='riddle_competition_results.csv',
                       help='Output file for detailed results (default: riddle_competition_results.csv)')
    
    args = parser.parse_args()
    
    try:
        # Initialize competition with specified number of rounds
        competition = RiddleCompetition(riddles_per_llm=args.rounds)
        results = competition.run_competition()

        # Print word riddles summary
        print("\nWord Riddles Summary:")
        print(results['word_summary'].to_string(index=False))
        
        # Print math riddles summary
        print("\nMath Riddles Summary:")
        print(results['math_summary'].to_string(index=False))

        # Save detailed results
        results['detailed_results'].to_csv(args.output, index=False)
        print(f"\nDetailed results saved to {args.output}")
        
    except Exception as e:
        ic(e)
        raise

if __name__ == "__main__":
    main() 