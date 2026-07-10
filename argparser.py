import argparse

def main():
    # 1. Initialize the parser
    parser = argparse.ArgumentParser(
        description="A sample script demonstrating Python's argparse module."
    )

    # 2. Add a positional argument (required by default)
    parser.add_argument(
        "filename", 
        help="The name of the file to process"
    )

    # 3. Add an optional argument that expects a value (with a default)
    parser.add_argument(
        "-n", "--count", 
        type=int, 
        default=1, 
        help="Number of times to process the file (default: 1)"
    )

    # 4. Add an optional boolean flag (True if present, False if absent)
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Increase output verbosity"
    )

    # 5. Parse the command-line arguments
    args = parser.parse_args()

    # 6. Use the arguments in your script logic
    if args.verbose:
        print(f"Starting the process in verbose mode...")
        print(f"Target file: {args.filename}")
        print(f"Execution count: {args.count}")

    for i in range(args.count):
        print(f"[{i + 1}] Processing {args.filename}...")

if __name__ == "__main__":
    main()
    