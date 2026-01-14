import sys
from pylint.lint import Run
from pylint.reporters.text import TextReporter

print("Starting Pylint check...")
try:
    with open("pylint_out.txt", "w", encoding="utf-8") as f:
        # Run Pylint on the file
        # We need to ensure we run it on the file path relative to cwd
        Run(["DeepAgents/graphs/agency_graph.py"], reporter=TextReporter(f), exit=False)
    print("Pylint check finished. Output written to pylint_out.txt")
except Exception as e:
    print(f"Error running Pylint: {e}")
