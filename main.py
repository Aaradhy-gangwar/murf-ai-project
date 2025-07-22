import cv2
import time
import json
import io
from PIL import Image
import google.generativeai as genai
import os

GEMINI_API_KEY = os.getenv("LLM_call")  # Load from environment variable
if not GEMINI_API_KEY:
    raise Exception("Gemini API key not found. Set it as environment variable LLM_call.")
genai.configure(api_key=GEMINI_API_KEY)

# === Prompt ===
input_prompt = """
You are a highly accurate text extractor, helping blind people.
Return only the key textual information from the image in a structured format.
Give the output in plain JSON format like this:
[
  "<clean extracted text here>"
]
If no text is found, still return: ["NIL"]
"""

# === OCR function ===
def get_gemini_text_response(image_path, prompt):
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image = Image.open(io.BytesIO(image_bytes))
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([image, prompt])
    text = response.text.strip() if response else "NIL"
    return {"text": [text] if text else ["NIL"]}

# === Camera auto-capture every 15 seconds ===
def auto_capture_and_extract():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot access webcam.")
        return

    try:
        while True:
            print("\nCapturing image in 3 seconds...")
            time.sleep(3)

            ret, frame = cap.read()
            if not ret:
                print("Failed to capture image.")
                continue

            image_path = "captured_image.jpg"
            cv2.imwrite(image_path, frame)
            print("Image captured and saved.")

            print("Sending to Gemini for OCR...")
            result = get_gemini_text_response(image_path, input_prompt)

            with open("response.json", "w") as f:
                json.dump(result, f, indent=4)

            print("Extracted Text Saved to response.json:")
            print(result)

            print("Waiting 10 seconds before next capture...\n")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n Stopped by user.")

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    auto_capture_and_extract()
