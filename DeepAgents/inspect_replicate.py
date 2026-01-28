import replicate
from dotenv import load_dotenv

load_dotenv("DeepAgents/.env")


def inspect_minimax():
    print("--- Inspecting Minimax Schema ---")
    try:
        # Get the model
        model = replicate.models.get("minimax/music-01")
        # Get latest version
        version = model.latest_version
        if not version:
            print("No latest version found.")
            return

        print(f"Model Version: {version.id}")

        # Print Input Schema
        # The schema is usually in 'openapi_schema' property of version
        # replicate python client exposes it?
        # Let's check available attributes
        print(
            "Schema Keys:",
            version.openapi_schema.keys()
            if hasattr(version, "openapi_schema")
            else "No schema attr",
        )

        if hasattr(version, "openapi_schema"):
            inputs = (
                version.openapi_schema.get("components", {})
                .get("schemas", {})
                .get("Input", {})
            )
            properties = inputs.get("properties", {})
            print("\nINPUT ARGUMENTS:")
            for key, val in properties.items():
                desc = val.get("description", "No description")
                req = "Required" if key in inputs.get("required", []) else "Optional"
                print(f"- {key} ({req}): {desc[:100]}...")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    inspect_minimax()
