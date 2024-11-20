from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import List
import os
import asyncio
import subprocess
from vistec_ser.inference.inference import infer_sample, setup_server
from datetime import datetime
import threading
from queue import Queue
import time

from handler import Handler
from eye import RoboEyes

# Global objects that will be initialized in lifespan
recorder = None
predictor = None
prediction_queue = Queue()  # Shared queue between recorder and predictor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize global objects
    global recorder, predictor
    
    # Setup server components
    config_path = "config.yaml"
    model, thaiser_module, temp_dir = setup_server(config_path)
    
    # Initialize recorder and predictor
    recorder = AudioRecorder(temp_dir, prediction_queue)
    predictor = PredictionWorker(model, thaiser_module, prediction_queue)
    
    # Start recording thread
    recording_thread = threading.Thread(target=recorder.start_recording_loop, daemon=True)
    recording_thread.start()
    
    # Start prediction thread
    prediction_thread = threading.Thread(target=predictor.prediction_loop, daemon=True)
    prediction_thread.start()
    
    yield  # Server is running
    
    # Cleanup
    recorder.stop()
    predictor.stop()

app = FastAPI(lifespan=lifespan)

class AudioRecorder:
    def __init__(self, temp_dir, queue):
        self.temp_dir = temp_dir
        self.current_recording = None
        self.stop_flag = False
        self.prediction_queue = queue

    def start_recording_loop(self):
        while not self.stop_flag:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"{self.temp_dir}/recorded_audio_{timestamp}.wav"
            
            # Start recording
            command = [
                "ffmpeg",
                "-y",
                "-f", "avfoundation",
                "-i", ":0",
                "-t", "5",
                "-ar", "16000",
                "-ac", "2",
                audio_filename
            ]
            
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)  # Wait for recording to complete
            process.terminate()
            
            # Add to prediction queue
            self.prediction_queue.put(audio_filename)
            
            # Clean up old recordings
            self._cleanup_old_files()

    def _cleanup_old_files(self):
        # Keep only the last 5 recordings
        files = sorted([f for f in os.listdir(self.temp_dir) if f.startswith("recorded_audio")])
        for old_file in files[:-1]:
            try:
                os.remove(os.path.join(self.temp_dir, old_file))
            except:
                pass

    def stop(self):
        self.stop_flag = True

class PredictionWorker:
    def __init__(self, model, thaiser_module, queue):
        self.model = model
        self.thaiser_module = thaiser_module
        self.stop_flag = False
        self.latest_prediction = None
        self.prediction_queue = queue

    def prediction_loop(self):
        while not self.stop_flag:
            try:
                # Get the next audio file from queue
                audio_filename = self.prediction_queue.get(timeout=1)

                # Process the audio file
                inference_loader = self.thaiser_module.extract_feature([audio_filename])
                inference_results = [infer_sample(self.model, sample, emotions=self.thaiser_module.emotions)
                                   for sample in inference_loader]
                
                # Store the latest prediction
                self.latest_prediction = inference_results[0] if inference_results else None
                # Clean up the processed file
                try:
                    os.remove(audio_filename)
                except:
                    pass
                
            except:
                # No audio file in queue
                pass

    def stop(self):
        self.stop_flag = True

    def get_latest_prediction(self):
        return self.latest_prediction

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "healthy"}

@app.get("/get_latest_prediction")
async def get_latest_prediction():
    if predictor is None:
        return {"error": "Server not fully initialized"}
    
    prediction = predictor.get_latest_prediction()
    return {"prediction": prediction if prediction is not None else None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", port=8080, reload=True) 