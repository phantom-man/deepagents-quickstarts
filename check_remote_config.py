import json
from dotenv import load_dotenv
from langsmith import Client

# Load Env
from pathlib import Path
env_path = Path(__file__).parent / "DeepAgents" / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def inspect_remote_config():
    repo_name = "deepagents-system-config"
    print(f"🔍 Pulling '{repo_name}' from LangSmith Hub...")
    
    client = Client()
    try:
        # Pull the prompt object
        prompt_obj = client.pull_prompt(repo_name)
        
        # Extract the system message content (where the JSON lives)
        # Usually it's the first message in the messages list
        if hasattr(prompt_obj, 'messages') and len(prompt_obj.messages) > 0:
            system_msg = prompt_obj.messages[0]
            if hasattr(system_msg, 'content'): # BaseMessage
                content = system_msg.content
            elif hasattr(system_msg, 'prompt') and hasattr(system_msg.prompt, 'template'): # ChatPromptTemplate sometimes nests
                 content = system_msg.prompt.template
            else:
                content = str(system_msg)
                
            print("\n✅ Remote Content Found:")
            print("-" * 40)
            print(content)
            print("-" * 40)
            
            try:
                # Try to parse as JSON to confirm it's valid config
                data = json.loads(content)
                print("\n📊 Key Analysis:")
                for section in data:
                    print(f"  - [{section}]")
                    if isinstance(data[section], dict):
                        for key in data[section]:
                            print(f"    - {key}: {data[section][key]}")
            except json.JSONDecodeError:
                print("\n⚠️ Content is not valid JSON.")
        else:
            print("❌ Prompt object has no messages or structure I recognize.")
            print(prompt_obj)

    except Exception as e:
        print(f"❌ Failed to pull or inspect: {e}")

if __name__ == "__main__":
    inspect_remote_config()
