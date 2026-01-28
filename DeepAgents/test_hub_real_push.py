"""
REAL verification of LangSmith Hub Push.
Creates a unique prompt artifact, pushes it, and verifies the commit.
"""

import datetime
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client


def run_test():
    client = Client()

    # 1. Create Unique Data
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.datetime.now().isoformat()
    repo_name = f"test-verification-{unique_id}"

    print("🧪 Starting Real Push Test")
    print(f"   Target Repo: {repo_name}")
    print(f"   Timestamp:   {timestamp}")

    # 2. Construct Prompt
    content = f"This is a verification artifact created at {timestamp}. ID: {unique_id}"
    prompt = ChatPromptTemplate.from_messages(
        [("system", content), ("user", "{input}")]
    )

    # 3. PUSH (Real mutation)
    print("\n🚀 Attempting Push...")
    try:
        url = client.push_prompt(repo_name, object=prompt)
        print(f"   ✅ Push Success! URL: {url}")
    except Exception as e:
        print(f"   ❌ Push Failed: {e}")
        return False

    # 4. PULL (Verify Persistence)
    print("\n📡 Attempting Verification Pull...")
    try:
        remote_prompt = client.pull_prompt(repo_name)

        # Verify Content Matches
        # Check first message (System)
        remote_content = remote_prompt.messages[0].prompt.template

        if remote_content == content:
            print("   ✅ Content Verified Match!")
            print(f"      Sent: '{content}'")
            print(f"      Got:  '{remote_content}'")
            return True
        else:
            print("   ❌ Content Mismatch!")
            print(f"      Sent: '{content}'")
            print(f"      Got:  '{remote_content}'")
            return False

    except Exception as e:
        print(f"   ❌ Pull Failed: {e}")
        return False


if __name__ == "__main__":
    success = run_test()
    if success:
        print("\n🎉 TEST PASSED: Hub is fully read/write capable.")
    else:
        print("\n🔥 TEST FAILED")
        exit(1)
