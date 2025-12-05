import argparse

from solver import solve_problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["examples", "assignment"], required=True)
    parser.add_argument("--force-schedule", default=None)
    args = parser.parse_args()

    if args.mode == "examples":
        problem_file = "example-problems.csv"
        output_file = "example-solutions.csv"
    else:
        problem_file = "problems.csv"
        output_file = "solutions.csv"

    solve_problems(problem_file, output_file, force_schedule=args.force_schedule)


if __name__ == "__main__":
    main()
