import subprocess
import requests
import os
from pydub import AudioSegment

RATE = 16000
CHANNELS = 2
TEMP_DIR = 'temp'
WAVE_OUTPUT_PATH = TEMP_DIR +'/recorded_audio.wav'
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"

def ensure_temp_directory_exists():
    """Ensure that the temp directory exists."""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

def record_audio(output_filename: str):
    """Record audio from microphone using ffmpeg and save it to a file."""
    print("Press Enter to start recording...")
    input()

    print("Recording... Press Enter again to stop recording.")

    command = [
        "ffmpeg",
        "-y",
        "-f", "avfoundation",
        "-i", ":0",
        "-ar", str(RATE),
        "-ac", str(CHANNELS),
        output_filename
    ]

    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        input()

        process.terminate()

        stdout, stderr = process.communicate()

        print(f"FFmpeg output:\n{stdout.decode()}")
        print(f"FFmpeg errors:\n{stderr.decode()}")

        if os.path.exists(output_filename):
            print(f"Recording saved successfully to {output_filename}")
        else:
            print(f"Recording failed, file {output_filename} does not exist.")

    except Exception as e:
        print(f"An error occurred during recording: {e}")

def send_audio_to_server(audio_filename: str, server_url: str):
    """Send the audio file to the server as a POST request."""
    if not os.path.exists(audio_filename):
        print(f"Audio file {audio_filename} does not exist.")
        return None

    with open(audio_filename, 'rb') as audio_file:
        files = {'audios': (WAVE_OUTPUT_FILENAME, audio_file, 'audio/wav')}
        response = requests.post(server_url, files=files)
        return response

def process_audio_with_pydub(audio_filename: str):
    """Use pydub to load and process the audio file."""
    if not os.path.exists(audio_filename):
        print(f"Audio file {audio_filename} does not exist.")
        return None

    audio = AudioSegment.from_wav(audio_filename)

    normalized_audio = audio.normalize()

    normalized_audio.export(audio_filename, format="wav")
    print(f"Audio processed and saved using pydub to {audio_filename}")

def start_recording_session():
    """Starts the recording session, processes audio, and sends it to the server."""
    while True:
        ensure_temp_directory_exists()
        record_audio(WAVE_OUTPUT_PATH)
        process_audio_with_pydub(WAVE_OUTPUT_PATH)

        server_url = "http://localhost:8000/predict"
        response = send_audio_to_server(WAVE_OUTPUT_PATH, server_url)

        if response:
            display_server_response(response)

        if os.path.exists(WAVE_OUTPUT_PATH):
            os.remove(WAVE_OUTPUT_PATH)
            print(f"File {WAVE_OUTPUT_PATH} removed after sending to server.")

        print("\nRecording session completed. Starting a new session...\n")

def display_server_response(response):
    """Display the server response in the desired format."""
    try:
        json_response = response.json()
        for item in json_response:
            print(f"Name: {item['name']}")
            print("Probabilities:")
            for emotion, prob in item['prob'].items():
                print(f"  {emotion}: {prob}%")
    except Exception as e:
        print(f"Error displaying server response: {e}")

if __name__ == "__main__":
    start_recording_session()
