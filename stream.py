import os
import subprocess
from dotenv import load_dotenv
from murf import Murf

# Load environment variables
load_dotenv(dotenv_path=".env")
api_key = os.getenv("MURF_API_KEY")

client = Murf(api_key=api_key)

# Stream the audio (returns a generator yielding chunks)
res = client.text_to_speech.stream(
    text="Hi, how can I help you this fine day?",
    voice_id="en-US-natalie"
)

temp_filename = "output_stream.wav"

try:
    with open(temp_filename, "wb") as f:
        # res is a generator yielding byte chunks, write each chunk
        for chunk in res:
            if chunk:
                f.write(chunk)
    print(f"Saved streamed audio to {temp_filename}")

    # Play the audio using ffplay (make sure ffplay is installed)
    subprocess.run(["ffplay", "-nodisp", "-autoexit", temp_filename])

finally:
    try:
        os.remove(temp_filename)
        print(f"Deleted {temp_filename}")
    except Exception as e:
        print(f"Could not delete {temp_filename}: {e}")
