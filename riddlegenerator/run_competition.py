from riddle_competition import RiddleCompetition
from icecream import ic

def main():
    try:
        competition = RiddleCompetition()
        results = competition.run_competition()

        # Print word riddles summary
        print("\nWord Riddles Summary:")
        print(results['word_summary'].to_string(index=False))
        
        # Print math riddles summary
        print("\nMath Riddles Summary:")
        print(results['math_summary'].to_string(index=False))

        # Save detailed results
        results['detailed_results'].to_csv('riddle_competition_results.csv', index=False)
        print("\nDetailed results saved to riddle_competition_results.csv")
    except Exception as e:
        ic(e)
        raise

if __name__ == "__main__":
    main() 