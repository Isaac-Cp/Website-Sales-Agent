import sys
import os

with open("debug_out.txt", "w") as f:
    f.write("Starting debug run...\n")
    try:
        from main import main
        f.write("Main imported successfully.\n")
        # Set sys.argv for the test
        sys.argv = ["main.py", "--query", "Electrician near Chicago", "--limit", "2"]
        f.write(f"Running main with args: {sys.argv}\n")
        main()
        f.write("Main finished successfully.\n")
    except Exception as e:
        f.write(f"An error occurred: {e}\n")
        import traceback
        f.write(traceback.format_exc())
