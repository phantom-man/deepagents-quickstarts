from google import genai
from dotenv import load_dotenv

# Load env for safety, though we rely on ADC
load_dotenv()

PROJECT_ID = "crafty-hook-483415-b3"
LOCATION = "us-central1"
# Imagen 3 model
MODEL_ID = "imagen-3.0-generate-001"

print("--- Probing Image Generation (Storyboard Mode) ---")
print(f"Project: {PROJECT_ID}")

try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    print(f"Requesting IMAGE from {MODEL_ID}...")
    response = client.models.generate_images(
        model=MODEL_ID,
        prompt="A cinematic storyboard sketch of a robot discovering a gentle flower in a harsh wasteland, detailed, atmospheric",
        config={'aspect_ratio': '16:9'}
    )
    
    if response.generated_images:
        gen_img = response.generated_images[0]
        output_file = "storyboard_test.png"
        
        # Robust Save
        img_data = None
        if hasattr(gen_img, "image") and hasattr(gen_img.image, "image_bytes"):
            img_data = gen_img.image.image_bytes
        elif hasattr(gen_img, "image_bytes"):
            img_data = gen_img.image_bytes
            
        if img_data:
            with open(output_file, "wb") as f:
                f.write(img_data)
            print(f"✅ SUCCESS! Image saved to {output_file}")
        else:
            print(f"⚠️ Image object structure unknown: {dir(gen_img)}")
        print("⚠️ No images returned.")

except Exception as e:
    print(f"❌ IMAGE GENERATION FAILED: {e}")
