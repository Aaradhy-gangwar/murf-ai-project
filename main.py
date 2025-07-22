import os
import requests
import subprocess
from dotenv import load_dotenv
from pydub import AudioSegment

# Load environment variables
load_dotenv(dotenv_path=".env")
api_key = os.getenv("MURF_API_KEY")

# Assuming Murf is a valid client
from murf import Murf
client = Murf(api_key=api_key)

# Generate TTS audio
res = client.text_to_speech.generate(
    text="There is much to be said",
    voice_id="en-US-jayden"
)

# Get the audio URL
audio_url = res.audio_file
response = requests.get(audio_url)

if response.ok:
    temp_filename = "output-1.wav"

    # Save to file
    with open(temp_filename, "wb") as f:
        f.write(response.content)
    print(f"Saved temporary audio as {temp_filename}")

    try:
        # Load the audio (optional — just to verify it's readable)
        audio = AudioSegment.from_file(temp_filename, format="wav")

        # Use ffplay via subprocess (non-blocking subprocess can cause issues, so we wait)
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


