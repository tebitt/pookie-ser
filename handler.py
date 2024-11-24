import numpy as np
from pydub import AudioSegment
from pydub.playback import play
from rate_limiter import RateLimiter
import aiohttp
import asyncio
import os
import pygame
from moviepy.editor import VideoFileClip

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

        self.rate_limiter = RateLimiter(interval_seconds=5)

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
        self.ser_surprise = float(sum(self.ser_happiness, self.ser_sadness, self.fer_neutral)/3)
        self.ser_fear = float(sum(self.ser_sadness, self.ser_frustration,  self.ser_anger)/3)
        self.ser_disgust = float(sum(self.ser_anger, self.ser_surprise, self.ser_fear)/3)

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
        self.fer_frustration = float(sum(self.fer_anger, self.fer_surprise, self.fer_sadness, self.fer_fear)/4)

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

        asyncio.ensure_future(self.move_eyes(dominant_emotion))
        self.speak(dominant_emotion)
        self.move(dominant_emotion)

    def speak(self, emotion):
        current_path = os.getcwd()
        audio_path = os.path.join(current_path, 'audio', f'{emotion}.wav')
        try:
            sound = AudioSegment.from_file(audio_path)
            play(sound)
        except Exception as e:
            print(f"An error occurred while trying to play the audio: {e}")


    def play_emotion_video(emotion):
        DEMO_EXIST = ['neutral', 'sadness', 'happiness']
        if emotion not in DEMO_EXIST:
            emotion = "neutral"

        current_path = os.getcwd()
        video_path = os.path.join(current_path, 'demo', f'{emotion}.mov')

        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file '{video_path}' not found.")

            pygame.init()

            clip = VideoFileClip(video_path)
            screen = pygame.display.set_mode(clip.size)
            pygame.display.set_caption(f"Playing: {emotion}")

            clock = pygame.time.Clock()
            for frame in clip.iter_frames(fps=24, dtype='uint8'):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return

                pygame.surfarray.blit_array(screen, frame)
                pygame.display.flip()
                clock.tick(24)

            pygame.quit()
        except Exception as e:
            print(f"An error occurred while trying to play the video: {e}")


        


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

