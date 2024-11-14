import cv2
import numpy as np
import time
import threading
import random
import math
import multiprocessing
import os
from fastapi import FastAPI
import atexit

# Define constants
BGCOLOR = (0, 0, 0)        # Background color (black)
MAINCOLOR = (0, 255, 0)    # Main eye color (green)
HAPPYCOLOR = (255, 255, 0)   # Eye color during happiness mode (cyan)
SADCOLOR = (0, 255, 255)     # Eye color during sadness mode (yellow)

app = FastAPI()


class RoboEyes:
    def __init__(self, screenWidth=640, screenHeight=480, fps=50):
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight
        self.frameInterval = 1 / fps
        self.fpsTimer = 0
        
        # Eye state (open/closed)
        self.eyeL_open = True
        self.eyeR_open = True

        # Eyes geometry
        self.eyeL_x = int(screenWidth * 0.25)
        self.eyeL_y = int(screenHeight * 0.5)
        self.eyeR_x = int(screenWidth * 0.75)
        self.eyeR_y = int(screenHeight * 0.5)

        # Eye properties for normal and happiness modes
        self.normal_eye_size = (75, 75)
        self.happy_eye_size = (90, 90)  # Eyes are slightly larger in happiness mode
        self.sad_eye_size = (85, 85)
        self.default_eye_color = MAINCOLOR       # Default eye color
        self.happy_color = HAPPYCOLOR    # Yellow color for happiness mode
        self.sad_color = SADCOLOR        # Cyan color for sadness mode

        # Happiness mode
        self.happiness_mode = False
        self.happiness_duration = random.uniform(3, 6)  # Randomized happiness duration
        self.happiness_start_time = None
        self.happiness_phase = 0         # 0: Full circle, 1: Half-circle, 2: Full circle again

        # Sadness mode
        self.sadness_mode = False
        self.sadness_duration = random.uniform(3, 6)
        self.sadness_start_time = None
        self.sadness_phase = 0

        # Animation timers for blinking
        self.blink_duration = random.uniform(0.1, 0.4)  # Randomize blink duration
        self.last_blink_time = time.time()
        self.blinking = False

        # Random blink interval during idle (between 3 to 6 seconds)
        self.next_blink_interval = random.uniform(3, 6)

        # Idle state and timer
        self.idle = False
        self.idle_interval = random.uniform(2, 5)  # Random idle movement interval
        self.last_idle = time.time()

    def init_window(self):
        self.window_name = 'RoboEyes'
        cv2.namedWindow(self.window_name)

    def express_happiness(self):
        self.happiness_mode = True
        self.happiness_start_time = time.time()

    def express_sadness(self):
        self.sadness_mode = True
        self.sadness_start_time = time.time()

    def draw_eyes(self, frame):
        # Determine if happiness mode is active
        if self.happiness_mode:
            current_eye_size = self.happy_eye_size
            current_eye_color = self.happy_color
            # Draw eyes according to the happiness phase
            if self.happiness_phase == 0:  # Full circle
                cv2.ellipse(frame, (self.eyeL_x, self.eyeL_y), current_eye_size, 0, 0, 360, current_eye_color, -1)
                cv2.ellipse(frame, (self.eyeR_x, self.eyeR_y), current_eye_size, 0, 0, 360, current_eye_color, -1)
            elif self.happiness_phase == 1:  # Half-circle (outline only)
                cv2.ellipse(frame, (self.eyeL_x, self.eyeL_y), current_eye_size, 0, 180, 360, current_eye_color, 5)
                cv2.ellipse(frame, (self.eyeR_x, self.eyeR_y), current_eye_size, 0, 180, 360, current_eye_color, 5)
            elif self.happiness_phase == 2:  # Back to full circle
                cv2.ellipse(frame, (self.eyeL_x, self.eyeL_y), current_eye_size, 0, 0, 360, current_eye_color, -1)
                cv2.ellipse(frame, (self.eyeR_x, self.eyeR_y), current_eye_size, 0, 0, 360, current_eye_color, -1)

        elif self.sadness_mode:
            current_eye_size = self.sad_eye_size
            current_eye_color = self.sad_color
            teardrop_offset_x = -90
            teardrop_offset_y = 46
            teardrop_circle_radius = 10
            triangle_height = 25
            triangle_width = 20

            if self.sadness_phase == 0:  # Teary eyes
                cv2.ellipse(frame, (self.eyeL_x, self.eyeL_y), current_eye_size, 0, -190, -420, current_eye_color, -1)
                cv2.ellipse(frame, (self.eyeR_x, self.eyeR_y), current_eye_size, 0, 10, 240, current_eye_color, -1)
            elif self.sadness_phase == 1:  # 
                slant_angle = math.radians(10)
                offset_x = int(current_eye_size[0] * math.cos(slant_angle))
                offset_y = int(current_eye_size[0] * math.sin(slant_angle))
                cv2.line(frame, (self.eyeL_x - offset_x, self.eyeL_y + offset_y), (self.eyeL_x + offset_x, self.eyeL_y - offset_y), current_eye_color, 5)
                cv2.line(frame, (self.eyeR_x - offset_x, self.eyeR_y - offset_y), (self.eyeR_x + offset_x, self.eyeR_y + offset_y), current_eye_color, 5)
            elif self.sadness_phase == 2:  # Back to full circle
                cv2.ellipse(frame, (self.eyeL_x, self.eyeL_y), current_eye_size, 0, -190, -420, current_eye_color, -1)
                cv2.ellipse(frame, (self.eyeR_x, self.eyeR_y), current_eye_size, 0, 10, 240, current_eye_color, -1)

            triangle_pts_left = np.array([
                    [self.eyeL_x + teardrop_offset_x, self.eyeL_y + teardrop_offset_y + teardrop_circle_radius - 40],
                    [self.eyeL_x + teardrop_offset_x - triangle_width // 2, self.eyeL_y + teardrop_offset_y + teardrop_circle_radius + triangle_height - 40],
                    [self.eyeL_x + teardrop_offset_x + triangle_width // 2, self.eyeL_y + teardrop_offset_y + teardrop_circle_radius + triangle_height - 40]
                ])
            cv2.fillPoly(frame, [triangle_pts_left], (255, 255, 0))
            cv2.circle(frame, (self.eyeL_x + teardrop_offset_x, self.eyeL_y + teardrop_offset_y), teardrop_circle_radius, (255, 255, 0), -1)

            triangle_pts_right = np.array([
                [self.eyeR_x - teardrop_offset_x, self.eyeR_y + teardrop_offset_y + teardrop_circle_radius - 40],
                [self.eyeR_x - teardrop_offset_x - triangle_width // 2, self.eyeR_y + teardrop_offset_y + teardrop_circle_radius + triangle_height - 40],
                [self.eyeR_x - teardrop_offset_x + triangle_width // 2, self.eyeR_y + teardrop_offset_y + teardrop_circle_radius + triangle_height - 40]
            ])
            cv2.fillPoly(frame, [triangle_pts_right], (255, 255, 0))
            cv2.circle(frame, (self.eyeR_x - teardrop_offset_x, self.eyeR_y + teardrop_offset_y), teardrop_circle_radius, (255, 255, 0), -1)

        else:
            # Normal mode (full circle or closed line based on blink state)
            current_eye_size = self.normal_eye_size
            current_eye_color = self.default_eye_color
            if self.eyeL_open:
                cv2.ellipse(frame, (self.eyeL_x, self.eyeL_y), current_eye_size, 0, 0, 360, current_eye_color, -1)
            else:
                cv2.line(frame, (self.eyeL_x - current_eye_size[0], self.eyeL_y), 
                         (self.eyeL_x + current_eye_size[0], self.eyeL_y), current_eye_color, 5)

            if self.eyeR_open:
                cv2.ellipse(frame, (self.eyeR_x, self.eyeR_y), current_eye_size, 0, 0, 360, current_eye_color, -1)
            else:
                cv2.line(frame, (self.eyeR_x - current_eye_size[0], self.eyeR_y), 
                         (self.eyeR_x + current_eye_size[0], self.eyeR_y), current_eye_color, 5)

    def blink(self):
        
        current_time = time.time()

        # Check if it's time to blink based on the random blink interval
        if not self.blinking and current_time - self.last_blink_time >= self.next_blink_interval:
            # Start blinking
            self.eyeL_open = False
            self.eyeR_open = False
            self.blinking = True
            self.blink_start_time = current_time
        elif self.blinking and current_time - self.blink_start_time >= self.blink_duration:
            # End blinking after the blink duration
            self.eyeL_open = True
            self.eyeR_open = True
            self.blinking = False
            self.last_blink_time = current_time
            # Set a new random interval for the next blink
            self.next_blink_interval = random.uniform(3, 6)

    def idle_movement(self):
        # Only perform idle movement if not blinking
        if not self.blinking:
            current_time = time.time()
            if current_time - self.last_idle > self.idle_interval:
                # Random idle eye movements (both eyes move together)
                movement = random.randint(-10, 10)
                self.eyeL_x += movement
                self.eyeR_x += movement
                self.last_idle = current_time
                # Randomize the idle interval
                self.idle_interval = random.uniform(2, 5)

    def handle_happiness_mode(self):
        current_time = time.time()

        if self.happiness_mode:
            elapsed_time = current_time - self.happiness_start_time
            if elapsed_time < self.happiness_duration / 2:
                self.happiness_phase = 0  # Teary eyes
            elif elapsed_time < self.happiness_duration / 2 + random.uniform(1, 2) and self.happiness_phase != 2:
                self.happiness_phase = 1  # Half-line with tear
            else:
                self.happiness_phase = 2  # Back to teary eyes

        if elapsed_time >= self.happiness_duration:
                with open ('temp/current_mood.txt', 'w') as f:
                    f.write('neutral')
                    f.close()
                self.happiness_mode = False



    def handle_sadness_mode(self):
        current_time = time.time()

        if self.sadness_mode:
            elapsed_time = current_time - self.sadness_start_time
            if elapsed_time < self.sadness_duration / 2:
                self.sadness_phase = 0  # Teary eyes
            elif elapsed_time < self.sadness_duration / 2 + random.uniform(0.1, 0.4) and self.sadness_phase != 2:
                self.sadness_phase = 1  # Half-line with tear
            else:
                self.sadness_phase = 2  # Back to teary eyes

        if elapsed_time >= self.sadness_duration:
                with open ('temp/current_mood.txt', 'w') as f:
                    f.write('neutral')
                    f.close()
                self.sadness_mode = False

    def update(self, status_queue):
        # Create a blank black screen
        frame = np.zeros((self.screenHeight, self.screenWidth, 3), dtype=np.uint8)

        self.blink()    
        # Check for new mood status from the queue
        if not status_queue.empty():
            mood = status_queue.get()
            if mood == "happiness":
                self.happiness_mode = True
                self.happiness_start_time = time.time()
            elif mood == "sadness":
                self.sadness_mode = True
                self.sadness_start_time = time.time()        
        if self.happiness_mode:
            self.handle_happiness_mode()
        elif self.sadness_mode:
            self.handle_sadness_mode()
        else:
            self.idle_movement()
            
        # Draw the eyes
        self.draw_eyes(frame)

        # Show the frame
        cv2.imshow(self.window_name, frame)

    def run(self, status_queue):
        self.init_window()
        while True:
            self.update(status_queue)
            cv2.waitKey(1)

default_mood = 'neutral'
with open ('temp/current_mood.txt', 'w') as f:
    f.write(default_mood)
    f.close()

@app.get("/set_status")
async def set_status(mood: str):
    current_mood = read_current_mood()
    if current_mood != mood:
        with open ('temp/current_mood.txt', 'w') as f:
            f.write(mood)
            f.close()
        status_queue.put(mood)
        current_mood = mood
        return {"message": f"{mood.capitalize()} mode activated"}
    else:
        return {"message": "Mood is already active"}

def run_fastapi():
    import uvicorn
    uvicorn.run(app, port=8081)

def run_eye_process(status_queue):
    robo_eyes = RoboEyes()
    robo_eyes.run(status_queue)

def read_current_mood():
    with open ('temp/current_mood.txt', 'r') as f:
        current_mood = f.read()
        f.close()
    return current_mood

if __name__ == "__main__":
    status_queue = multiprocessing.Queue()

    # Run FastAPI server in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.start()

    # Create RoboEyes object and start the rendering process in a separate process
    eye_process = multiprocessing.Process(target=run_eye_process, args=(status_queue,))
    eye_process.start()

def cleanup():
    """Delete the temp/current_mood.txt file on program exit."""
    try:
        os.remove('temp/current_mood.txt')
        print("Cleanup complete: Deleted temp/current_mood.txt")
    except FileNotFoundError:
        print("Cleanup skipped: temp/current_mood.txt not found")
    except Exception as e:
        print(f"Cleanup error: {e}")


atexit.register(cleanup)