import numpy as np
from playsound import playsound
from rate_limiter import RateLimiter
import aiohttp

class Handler:
    def __init__(self, ser_result=None, fer_result=None):
        self.ser_neutral = 0.0
        self.ser_happiness = 0.0
        self.ser_anger = 0.0
        self.ser_sadness = 0.0
        self.ser_frustration = 0.0

        self.fer_neutral = 0.0
        self.fer_happiness = 0.0
        self.fer_anger = 0.0
        self.fer_sadness = 0.0
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
        }
        dominant_emotion = max(emotions, key=emotions.get)
        print(f"SER Dominant Emotion: {dominant_emotion}")
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
            "surprise": self.fer_surprise,
            "fear": self.fer_fear,
            "disgust": self.fer_disgust,
        }
        dominant_emotion = max(emotions, key=emotions.get)
        print(f"FER Dominant Emotion: {dominant_emotion}")
        return dominant_emotion

    def handle_robot_behavior(self):
        """
        Controls the robot's eyes, voice, and movement based on the dominant SER emotion.
        """
        ser_emotion = self.get_dominant_emotion_ser()
        fer_emotion = self.get_dominant_emotion_fer()

        self.move_eyes(fer_emotion)
        # self.speak(ser_emotion)
        self.move(fer_emotion)

    def speak(self, emotion):
        audio_path = f'audio/{emotion}.wav'
        try:
            playsound(audio_path)
        except Exception as e:
            print(f"An error occurred while trying to play the audio: {e}")


    def move(self, action):
        print(f"Moving robot: {action}")
        # Additional behaviors based on other emotions

    def move_eyes(self, expression):
        EYES_SERVER_URL = f"http://127.0.0.1:8081/set_status?mood={expression}"
        try:
             with aiohttp.ClientSession() as session:
                    with session.get(EYES_SERVER_URL) as response:
                        if response.status == 200:
                            print("Eyes moved successfully")
                        else:
                            print(f"Failed to move eyes. Status code: {response.status}")
        except Exception as e:
            print(f"Error sending request: {e}")
            return None, None

