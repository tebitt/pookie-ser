import numpy as np
from pydub import AudioSegment
from pydub.playback import play
import aiohttp
import asyncio
import os
import pygame
import cv2

class Handler:
    def __init__(self, ser_result=None, fer_result=None):
        self.ser_neutral = 0.0
        self.ser_happiness = 0.0
        self.ser_anger = 0.0
        self.ser_sadness = 0.0
        self.ser_frustration = 0.0
        self.ser_surprise = 0.0 #calc
        self.ser_fear = 0.0 #calc
        self.ser_disgust = 0.0 #calc

        self.fer_neutral = 0.0
        self.fer_happiness = 0.0
        self.fer_anger = 0.0
        self.fer_sadness = 0.0
        self.fer_frustration = 0.0 #calc
        self.fer_surprise = 0.0
        self.fer_fear = 0.0
        self.fer_disgust = 0.0

        if ser_result:
            self.set_ser_emotions(ser_result)

        if fer_result is not None and fer_result.size != 0:
            self.set_fer_emotions(fer_result)


    def set_ser_emotions(self, ser_result):
        """
        Parses the SER result and sets individual emotion probabilities.
        """
        self.ser_neutral = float(ser_result['prediction']['prob'].get("neutral", 0.0))
        self.ser_anger = float(ser_result['prediction']['prob'].get("anger", 0.0))
        self.ser_happiness = float(ser_result['prediction']['prob'].get("happiness", 0.0))
        self.ser_sadness = float(ser_result['prediction']['prob'].get("sadness", 0.0))
        self.ser_frustration = float(ser_result['prediction']['prob'].get("frustration", 0.0))
        self.ser_surprise = float(sum([self.ser_happiness, self.ser_sadness, self.fer_neutral])/3)
        self.ser_fear = float(sum([self.ser_sadness, self.ser_frustration,  self.ser_anger])/3)
        self.ser_disgust = float(sum([self.ser_anger, self.ser_surprise, self.ser_fear])/3)

    def set_fer_emotions(self, fer_result):
        """
        Parses the FER result and sets individual emotion probabilities.
        """
        self.fer_neutral = float(fer_result[0][0])
        self.fer_happiness = float(fer_result[0][1])
        self.fer_sadness = float(fer_result[0][2])
        self.fer_surprise = float(fer_result[0][3])
        self.fer_fear = float(fer_result[0][4])
        self.fer_disgust = float(fer_result[0][5])
        self.fer_anger = float(fer_result[0][6])
        self.fer_frustration = float(sum([self.fer_anger, self.fer_surprise, self.fer_sadness, self.fer_fear])/4)

    def get_dominant_emotion_ser(self):
        """
        Determines the dominant emotion based on the highest probability.
        """
        emotions = {
            "neutral": self.ser_neutral,
            "anger": self.ser_anger,
            "happiness": self.ser_happiness,
            "sadness": self.ser_sadness,
            "frustration": self.ser_frustration,
            "surprise": self.ser_surprise,
            "fear": self.ser_fear,
            "disgust": self.ser_disgust,
        }

        dominant_emotion = max(emotions, key=emotions.get)
        return dominant_emotion

    def get_dominant_emotion_fer(self):
        """
        Determines the dominant emotion based on the highest probability.
        """
        emotions = {
            "neutral": self.fer_neutral,
            "anger": self.fer_anger,
            "happiness": self.fer_happiness,
            "sadness": self.fer_sadness,
            "frustration": self.fer_disgust,
            "surprise": self.fer_surprise,
            "fear": self.fer_fear,
            "disgust": self.fer_disgust,
        }
        dominant_emotion = max(emotions, key=emotions.get)
        return dominant_emotion

    def get_dominant_emotion(self, ser_emotion, fer_emotion):
        """
        Determines the dominant emotion based on the highest probability.
        """
        emotions = {
            "neutral": max(self.ser_neutral, self.fer_neutral),
            "anger": max(self.ser_anger, self.fer_anger),
            "happiness": max(self.ser_happiness, self.fer_happiness),
            "sadness": max(self.ser_sadness, self.fer_sadness),
            "frustration": max(self.ser_frustration, self.fer_disgust),
            "surprise": max(self.ser_surprise, self.fer_surprise),
            "fear": max(self.ser_fear, self.fer_fear),
            "disgust": max(self.ser_disgust, self.fer_disgust),
        }
        dominant_emotion = max(emotions, key=emotions.get)
        print(f"SER Dominant Emotion: {ser_emotion}")
        print(f"FER Dominant Emotion: {fer_emotion}")
        print(f"Combined Dominant Emotion: {dominant_emotion}")
        return dominant_emotion


    def handle_robot_behavior(self):
        """
        Controls the robot's eyes, voice, and movement based on the dominant SER emotion.
        """
        ser_emotion = self.get_dominant_emotion_ser()
        fer_emotion = self.get_dominant_emotion_fer()

        dominant_emotion = self.get_dominant_emotion(ser_emotion, fer_emotion)

        async def execute_actions():
            await self.move_eyes(fer_emotion)  # Wait for eyes to finish moving
            await asyncio.gather(
                self.move(fer_emotion),
            )

        self.speak(fer_emotion)
        asyncio.ensure_future(execute_actions())

    def speak(self, emotion):
        current_path = os.getcwd()
        audio_path = os.path.join(current_path, 'audio', f'{emotion}.wav')
        try:
            sound = AudioSegment.from_file(audio_path)
            play(sound)
        except Exception as e:
            print(f"An error occurred while trying to play the audio: {e}")


    async def move(self, emotion):
        DEMO_EXIST = ['neutral', 'sadness', 'happiness']
        if emotion not in DEMO_EXIST:
            emotion = "neutral"

        # Construct the video path
        current_path = os.getcwd()
        video_path = os.path.join(current_path, 'demo', f'{emotion}.mp4')

        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file '{video_path}' not found.")

            # Initialize Pygame
            pygame.init()
            pygame.display.set_caption(f"Playing: {emotion}")

            # Open the video file with OpenCV
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"Unable to open video: {video_path}")

            # Get video dimensions
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30  # Default to 30 FPS if FPS is unavailable

            # Create Pygame window
            screen = pygame.display.set_mode((width, height))

            # Main loop to play video
            clock = pygame.time.Clock()
            while cap.isOpened():
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        cap.release()
                        pygame.quit()
                        return

                ret, frame = cap.read()
                if not ret:
                    break

                # Convert OpenCV frame (BGR) to Pygame surface (RGB)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

                # Display the frame in Pygame
                screen.blit(frame, (0, 0))
                pygame.display.flip()

                # Maintain video frame rate
                clock.tick(fps)

            # Clean up after playback
            cap.release()
            pygame.quit()

        except Exception as e:
            print(f"An error occurred: {e}")


    async def move_eyes(self, expression):
        EYES_SERVER_URL = f"http://127.0.0.1:8081/set_status?mood={expression}"
        try:
             async with aiohttp.ClientSession() as session:
                    async with session.get(EYES_SERVER_URL) as response:
                        if response.status == 200:
                            print("Eyes moved successfully")
                        else:
                            print(f"Failed to move eyes. Status code: {response.status}")
        except Exception as e:
            print(f"Error sending request: {e}")
            return None, None

