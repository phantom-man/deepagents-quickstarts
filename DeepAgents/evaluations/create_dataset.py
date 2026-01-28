import os

from dotenv import load_dotenv
from langsmith import Client

# Load environment variables
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")))


def create_dataset():
    client = Client()
    dataset_name = "Director-Commercial-Tests-v1"

    # Check if dataset exists
    if client.has_dataset(dataset_name=dataset_name):
        print(f"Dataset '{dataset_name}' already exists. Skipping creation.")
        return

    # Create dataset
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Dataset for testing the Director Agent's ability to plan commercial shoots.",
    )

    # Define examples
    examples = [
        {
            "inputs": {
                "input_text": "I need a 30-second commercial for a new caffeinated sparkling water called 'ZapFizz'. It should target gamers."
            },
            "outputs": {
                "reference_elements": [
                    "Target Audience: Gamers",
                    "Tone: High Energy",
                    "Product: ZapFizz",
                    "Duration: 30 seconds",
                ]
            },
        },
        {
            "inputs": {
                "input_text": "Create a storyboard for a luxury watch brand 'Chronos'. Elegant, silent luxury, black and white visuals."
            },
            "outputs": {
                "reference_elements": [
                    "Brand: Chronos",
                    "Tone: Elegant / Silent Luxury",
                    "Visual Style: Black and White",
                    "Product Focus: Watches",
                ]
            },
        },
        {
            "inputs": {
                "input_text": "We are launching 'EcoSneaks', shoes made from recycled plastic. The ad should be outdoorsy and inspiring."
            },
            "outputs": {
                "reference_elements": [
                    "Product: EcoSneaks",
                    "Material: Recycled Plastic",
                    "Setting: Outdoors",
                    "Mood: Inspiring",
                ]
            },
        },
    ]

    # Add examples to proposed dataset
    client.create_examples(
        inputs=[e["inputs"] for e in examples],
        outputs=[e["outputs"] for e in examples],
        dataset_id=dataset.id,
    )

    print(f"Created dataset '{dataset_name}' with {len(examples)} examples.")


if __name__ == "__main__":
    create_dataset()
