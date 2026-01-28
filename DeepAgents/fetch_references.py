# pylint: disable=broad-exception-caught
"""
Script to download reference documentation for DeepAgents context.
"""

import os
import urllib.request


def download_references():
    """Download predefined reference URLs to local files."""

    # Define the references to download
    references = {
        "gemini_api.html": "https://ai.google.dev/api/python/google/generativeai",
        "langchain_docs.html": "https://python.langchain.com/docs/get_started/introduction",
        "python_docs.html": "https://docs.python.org/3/",
    }

    # Create the directory if it doesn't exist
    output_dir = "references"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    print("Downloading references...")

    for filename, url in references.items():
        filepath = os.path.join(output_dir, filename)
        try:
            # specific headers to avoid being blocked by some sites
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                content = response.read().decode("utf-8")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Downloaded: {filename}")
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")

    print("\nDone! References are saved in the 'references/' folder.")


if __name__ == "__main__":
    download_references()
