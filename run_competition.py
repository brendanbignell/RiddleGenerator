from riddlegenerator.riddle_competition import RiddleCompetition

def main():
    competition = RiddleCompetition()
    results = competition.run_competition()

    # Print summary
    print("\nCompetition Summary:")
    print(results['summary'].to_string(index=False))

    # Save detailed results
    results['detailed_results'].to_csv('riddle_competition_results.csv', index=False)
    print("\nDetailed results saved to riddle_competition_results.csv")

if __name__ == "__main__":
    main() 