# Test Meta-Discovery
import os
import sys

# Ensure path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from DeepAgents.inter_agent_comms import discover_agents


def test_registry():
    print("--- Testing Agent Discovery Registry ---")

    print("\n1. Listing All Agents:")
    all_agents = discover_agents.invoke({"query": "all"})
    print(all_agents[:200] + "...")  # Print snippet

    print("\n2. Finding Expert for 'Music':")
    music_help = discover_agents.invoke(
        {"query": "I need someone to write lyrics and make a song"}
    )
    print(music_help)

    print("\n3. Finding Expert for 'Video':")
    video_help = discover_agents.invoke({"query": "make a dramatic movie scene"})
    print(video_help)

    print("\n4. Finding Expert for 'Research':")
    data_help = discover_agents.invoke({"query": "find valid statistics about coffee"})
    print(data_help)


if __name__ == "__main__":
    test_registry()
