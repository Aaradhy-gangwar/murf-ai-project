import cv2
import time
import json
import io
import re
import os
import requests
import subprocess
from pydub import AudioSegment
from PIL import Image
import google.generativeai as genai
from murf import Murf
from dotenv import load_dotenv

def extract_text_list_from_response(response):
    raw_text = response.get('text', [''])[0]
    cleaned_text = re.sub(r'```json\s*|\s*```', '', raw_text, flags=re.IGNORECASE).strip()
    try:
        text_list = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON from response text:", e)
        text_list = [cleaned_text]
    return text_list

def get_gemini_text_response(image_path, prompt):
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image = Image.open(io.BytesIO(image_bytes))
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([image, prompt])
    text = response.text.strip() if response else "NIL"
    return {"text": [text] if text else ["NIL"]}

def play_texts_with_murf(texts, client):
    for idx, text in enumerate(texts, 1):
        print(f"\nProcessing text {idx}: {text}")

        try:
            # Translate text to English (or your target language)
            temptext = client.text.translate(
                target_language="en-US",
                texts=[text],
            )
            playback = temptext.translations[0].translated_text
            print("Translated text:", playback)

            # Generate speech audio
            res = client.text_to_speech.generate(
                text=playback,
                voice_id="en-US-jayden"
            )
            audio_url = res.audio_file

            # Download audio file
            response = requests.get(audio_url)
            if response.ok:
                temp_filename = f"output-{idx}.wav"
                with open(temp_filename, "wb") as f:
                    f.write(response.content)
                print(f"Saved temporary audio as {temp_filename}")

                try:
                    audio = AudioSegment.from_file(temp_filename, format="wav")
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", temp_filename])
                except Exception as e:
                    print("Playback failed:", e)

                try:
                    os.remove(temp_filename)
                    print(f"Deleted {temp_filename}")
                except Exception as e:
                    print("Failed to delete file:", e)

            else:
                print("Failed to download audio file:", response.status_code)
        except Exception as e:
            print(f"Error processing text '{text}': {e}")

def auto_capture_and_extract_and_play():
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

            # Save raw response
            with open("response.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)

            print("Extracted Text Saved to response.json:")
            print(result)

            # Extract individual text strings
            extracted_texts = extract_text_list_from_response(result)
            print("\nIndividual extracted texts:")
            for i, txt in enumerate(extracted_texts, 1):
                print(f"{i}. {txt}")

            # Stream audio for each extracted text via Murf
            play_texts_with_murf(extracted_texts, murf_client)

            print("Waiting 10 seconds before next capture...\n")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    load_dotenv(dotenv_path=".env")

    # Gemini setup
    GEMINI_API_KEY = os.getenv("LLM_call")
    if not GEMINI_API_KEY:
        raise Exception("Gemini API key not found. Set it as environment variable LLM_call.")
    genai.configure(api_key=GEMINI_API_KEY)

    # Murf setup
    MURF_API_KEY = os.getenv("MURF_API_KEY")
    if not MURF_API_KEY:
        raise Exception("Murf API key not found. Set it as environment variable MURF_API_KEY.")
    murf_client = Murf(api_key=MURF_API_KEY)

    input_prompt = """
You are a highly accurate text extractor, helping blind people.
Return only the key textual information from the image in a structured format.
Give the output in plain JSON format like this:
[
  "<clean extracted text here>"
]
If no text is found, still return: ["NIL"]
"""

    auto_capture_and_extract_and_play()
