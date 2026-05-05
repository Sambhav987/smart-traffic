import cv2
import threading
import time
import numpy as np
# from roboflow import Roboflow
# import supervision as sv
from django.conf import settings
from .models import Congestion, Accident, HistoricData
from django.utils import timezone
import os
from ultralytics import YOLO
import smtplib
from email.message import EmailMessage
from core.services.push import send_push

# Initialize Roboflow Model Globally
# model = None
# try:
#     rf = Roboflow(api_key="PVgUMg8Yz2wXAXLrBSEB")
#     project = rf.workspace().project("vehicle-detection-bz0yu")
#     model = project.version(4).model
# except Exception as e:
#     print(f"Global Roboflow model failed to load: {e}")
#     model = None

# Using YOLOv8
model = YOLO("yolo26n.pt")
intersection_id = 1
intersection_name = "Ruby Crossing"
# Simplified Singleton for State
class TrafficStateManager:
    def __init__(self):
        self.detection_counts = {"Top": 0, "Right": 0, "Left": 0, "Bottom": 0}
        self.signals = {"Top": "GREEN", "Right": "RED", "Left": "RED", "Bottom": "GREEN"}
        self.signal_group = 0 # 0: U-D Green, 1: L-R Green
        self.congestion_threshold = 6
        self.last_switch_time = time.time()
        self.min_time = 5
        self.max_time = 15
        self.lock = threading.Lock()
        self.video_sources = {"Top": None, "Right": None, "Left": None, "Bottom": None}
        self.last_congestion_log_time = 0
        self.last_historic_data_log_time = 0

    def update(self, section, count):
        with self.lock:
            self.detection_counts[section] = count
            self.check_congestion()
            self.update_signals()
            self.add_historic_record()

    def set_video_source(self, section, source):
        with self.lock:
            self.video_sources[section] = source

    def get_video_source(self, section):
        return self.video_sources.get(section, None)

    def add_historic_record(self):
        car_counts = self.detection_counts
        current_time = time.time()
        
        # Rate limit database writes to once every 60 seconds
        if current_time - self.last_historic_data_log_time > 60:
            timestamp_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                total = sum(car_counts.values())
                HistoricData.objects.create(timestamp=timestamp_str, num_cars_left=car_counts["Left"], num_cars_right=car_counts["Right"], num_cars_top=car_counts["Top"], num_cars_bottom=car_counts["Bottom"], total_cars=total)
                print(f"Logged Historic Data: {total} cars at {timestamp_str}")
                self.last_historic_data_log_time = current_time
            except Exception as e:
                print(f"Error logging historic data: {e}")

            
    def check_congestion(self):
        max_section = max(self.detection_counts, key=self.detection_counts.get)
        max_count = self.detection_counts[max_section]

        if max_count > self.congestion_threshold:
            current_time = time.time()
            # Rate limit database writes to once every 5 seconds
            if current_time - self.last_congestion_log_time > 30:
                timestamp_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    Congestion.objects.create(timestamp=timestamp_str, num_cars=max_count, section=max_section)
                    print(f"Logged Congestion: {max_count} cars at {timestamp_str} in {max_section} section")
                    self.last_congestion_log_time = current_time
                except Exception as e:
                    print(f"Error logging congestion: {e}")

                user = "demo69lemonade@gmail.com"
                password = "njtfjabmchkgqdkr"  # Use app password if 2FA is enabled

                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(user, password)
                msg = EmailMessage()
                msg.set_content(f"Hello, a congestion has been detected with {max_count} cars at {timestamp_str} in {max_section} section")
                msg['from'] = user
                msg['to'] = "sambhavagarwal6@gmail.com"
                msg['subject'] = f"Congestion detected at {timestamp_str}"
                server.send_message(msg)
                
                send_push(
                    title="Congestion detected",
                    body=f"At {max_section}",
                    data={
                        "intersectionId": intersection_id,
                        "intersectionName": intersection_name,
                    },
                )

    def update_signals(self):
        current_time = time.time()
        elapsed = current_time - self.last_switch_time
        
        count_up_down = self.detection_counts["Top"] + self.detection_counts["Bottom"]
        count_left_right = self.detection_counts["Right"] + self.detection_counts["Left"]
        
        # new part
        
        total = count_up_down + count_left_right

        if self.signal_group == 0 and count_left_right == 0:
            return
        if self.signal_group == 1 and count_up_down == 0:
            return
        
        if total > 0:
            ud_ratio = count_up_down / total
            lr_ratio = count_left_right / total
        else:
            ud_ratio = lr_ratio = 0.5
            
        min_green = 5
        max_green = 15

        ud_green_time = min_green + ud_ratio * (max_green - min_green)
        lr_green_time = min_green + lr_ratio * (max_green - min_green)
                
        
        if self.signal_group == 0:
            if elapsed > ud_green_time:
                self.signal_group = 1
                self.last_switch_time = current_time

        else:
            if elapsed > lr_green_time:
                self.signal_group = 0
                self.last_switch_time = current_time
        
        
        # changed the below part 
        '''
        # Don't switch if the opposing group has no cars waiting
        if self.signal_group == 0 and count_left_right == 0:
            return
        if self.signal_group == 1 and count_up_down == 0:
            return

        # Logic from original script
        if self.signal_group == 0: # U-D Green (Top/Bottom? Check original logic)
            # Original: signal_up_down=1 (Top/Bottom Green if logic holds)
            # If L-R traffic > 1.25 * U-D AND min time passed
            if (count_left_right > 1.25 * count_up_down and elapsed > self.min_time) or elapsed > self.max_time:
                self.signal_group = 1
                self.last_switch_time = current_time
        else: # L-R Green
            if (count_up_down > 1.25 * count_left_right and elapsed > self.min_time) or elapsed > self.max_time:
                self.signal_group = 0
                self.last_switch_time = current_time
        '''
        if self.signal_group == 0:
            # Top/Bottom Green
            self.signals["Top"] = "GREEN"
            self.signals["Bottom"] = "GREEN"
            self.signals["Right"] = "RED"
            self.signals["Left"] = "RED"
        else:
            # Right/Left Green
            self.signals["Top"] = "RED"
            self.signals["Bottom"] = "RED"
            self.signals["Right"] = "GREEN"
            self.signals["Left"] = "GREEN"

# Global Instance
traffic_state = TrafficStateManager()

class VideoCamera:
    def __init__(self, section):
        self.section = section
        source = traffic_state.get_video_source(section)
        
        self.video = None
        if source is not None:
             # Verify if source is a valid file path if it's a string
            if isinstance(source, str) and not os.path.exists(source):
                print(f"Warning: Video file not found: {source}. Reverting to None.")
            else:
                self.video = cv2.VideoCapture(source)

        # self.box_annotator = sv.BoxAnnotator()
        # self.label_annotator = sv.LabelAnnotator()

    def __del__(self):
        if self.video:
            self.video.release()

    def get_frame(self):
        image = None
        if self.video:
            success, image = self.video.read()
            if not success:
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                success, image = self.video.read()
                if not success:
                    # Backend fallback: Black frame
                    image = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(image, f"No Signal: {self.section}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
             # No source selected
            image = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(image, "Select Source", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(image, f"Section: {self.section}", (200, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)

        # Resize for performance and UI consistency
        if image is not None:
            image = cv2.resize(image, (640, 480))


        count = 0
        # Use global model
        if model:
            try:
                # for roboflow
                # result = model.predict(image, confidence=40, overlap=30).json()
                # detections = sv.Detections.from_inference(result)
                # labels = [item["class"] for item in result["predictions"]]
                # count = len(detections)
                
                # image = self.box_annotator.annotate(scene=image, detections=detections)
                # image = self.label_annotator.annotate(scene=image, detections=detections, labels=labels)

                # for yolo
                result = model(image, conf=0.40, iou=0.70, classes=[1, 2, 3, 4, 5, 6, 7, 8], verbose=False)
                count = len(result[0].boxes)
                image = result[0].plot()

            except Exception as e:
                print(f"Prediction Error: {e}")

        # Update State
        traffic_state.update(self.section, count)

        # Draw Overlay
        signal = traffic_state.signals[self.section]
        color = (0, 255, 0) if signal == "GREEN" else (0, 0, 255)
        
        # Draw a traffic light box
        cv2.rectangle(image, (10, 10), (100, 60), (0, 0, 0), -1)
        cv2.circle(image, (30, 35), 15, color, -1)
        cv2.putText(image, str(count), (60, 45), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
