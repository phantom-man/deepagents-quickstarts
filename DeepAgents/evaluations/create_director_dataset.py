import os
import datetime
from dotenv import load_dotenv
from langsmith import Client

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

def create_dataset():
    client = Client()
    dataset_name = "Director-Commercial-Tests-v1"
    
    # Check if exists
    if client.has_dataset(dataset_name=dataset_name):
        print(f"Dataset {dataset_name} already exists.")
        return

    print(f"Creating dataset: {dataset_name}...")
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Test cases for the Director Agent commercial generation.",
    )

    # 1. Spicy Taco
    client.create_example(
        inputs={"input_text": "Create a 15-second commercial for 'Volcano Tacos' - extremely spicy."},
        outputs={"reference_elements": ["close-up of taco", "steam or fire visual", "rapid cuts", "red color palette"]},
        dataset_id=dataset.id,
    )

    # 2. Luxury Car
    client.create_example(
        inputs={"input_text": "Teaser for the new 'Nebula X' electric sedan. Smooth, silent, futuristic."},
        outputs={"reference_elements": ["wide shot of car", "gliding camera movement", "blue/silver palette", "silence or quiet audio cue"]},
        dataset_id=dataset.id,
    )

    # 3. Old Coffee House
    client.create_example(
        inputs={"input_text": "Nostalgic ad for 'Grandma's Coffee'. Warm, slow, 1950s vibe."},
        outputs={"reference_elements": ["warm lighting", "slow pan", "steam rising", "sepia or film grain"]},
        dataset_id=dataset.id,
    )

    print(f"Dataset {dataset_name} created with 3 examples.")

if __name__ == "__main__":
    create_dataset()
