# pylint: disable=broad-exception-caught
"""
Custom URL fetcher to bypass basic bot detection or handle headers.
"""
import sys
import urllib.request
import urllib.error


def fetch_url(target_url, target_file):
    """
    Fetch content from a URL and save it to a file.
    """
    print(f"Fetching {target_url}...")
    try:
        req = urllib.request.Request(
            target_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            },
        )
        with urllib.request.urlopen(req) as response:
            content = response.read().decode("utf-8")

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Successfully saved content to {target_file}")

    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(f"❌ URL Error: {e.reason}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python custom_fetcher.py <url> <output_file>")
        sys.exit(1)

    input_url = sys.argv[1]
    input_file = sys.argv[2]
    fetch_url(input_url, input_file)


if __name__ == "__main__":
    main()
