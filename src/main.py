"""
main.py
Author: Ali K
License: MIT
GitHub: https://github.com/AliK070

────────────────────────────────────────────────────
Smart Fitness Tracker using Pose Detection (MediaPipe)
────────────────────────────────────────────────────

Frameworks/Libraries Used:
- OpenCV: https://docs.opencv.org/
- MediaPipe: https://developers.google.com/mediapipe
- Tkinter (GUI): https://docs.python.org/3/library/tkinter.html
- NumPy: https://numpy.org/
- PIL (Pillow): https://pillow.readthedocs.io/en/stable/

"""

import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import datetime
import csv
import time
import os


mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_draw = mp.solutions.drawing_utils


reps, direction, bad_form_count = 0, 0, 0
form_feedback, last_tip_time = "", 0
recorded_data, tip_log = [], []
mode, goal_reps = "Curl", 10
tracking_active, countdown_active = False, False
countdown_start_time, session_num = 0, 1
video_writer, video_filepath = None, ""



def calculate_angle(a, b, c):
    """
    Calculates the angle between three points.
    Args: a, b, c - Lists of (x, y) coordinates.
    Returns: Angle in degrees.
    """
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba, bc = a - b, c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

def throttle_tip(message):
    
    global last_tip_time, form_feedback, tip_log
    now = time.time()
    if now - last_tip_time > 2:
        form_feedback = message
        tip_log.append((datetime.datetime.now().strftime("%H:%M:%S"), mode, message))
        last_tip_time = now


def evaluate_form_curl(angle, shoulder_y, wrist_y):
    if wrist_y < shoulder_y - 0.1:
        throttle_tip("Keep elbows down and steady.")
    elif angle < 20 or angle > 170:
        throttle_tip("Avoid swinging, control motion.")

def evaluate_form_pushup(angle):
    if angle > 170:
        throttle_tip("Go lower for a full rep.")
    elif angle < 60:
        throttle_tip("Don't collapse, keep control.")

def evaluate_form_squat(hip_y, knee_y, angle):
    if hip_y < knee_y - 0.05:
        throttle_tip("Go lower into your squat.")
    elif angle > 170 or angle < 70:
        throttle_tip("Keep knees aligned and stable.")



def save_session():
  
    global session_num, recorded_data, tip_log, video_writer
    if video_writer:
        video_writer.release()
    session_num += 1

    session_dir = os.path.join("recordings", f"session_{session_num - 1}", mode)
    os.makedirs(session_dir, exist_ok=True)

    if video_filepath and os.path.exists(video_filepath):
        os.rename(video_filepath, os.path.join(session_dir, os.path.basename(video_filepath)))

    with open(os.path.join(session_dir, "data.csv"), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Mode", "Reps", "Bad Form Count"])
        writer.writerows(recorded_data)

    with open(os.path.join(session_dir, "tips.csv"), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Mode", "Tip"])
        writer.writerows(tip_log)

def reset_session():
    
    global reps, direction, bad_form_count, form_feedback, recorded_data, tip_log
    global tracking_active, countdown_active, video_writer, video_filepath

    reps = direction = bad_form_count = 0
    form_feedback = ""
    recorded_data.clear()
    tip_log.clear()
    tracking_active = False
    countdown_active = True
    progress.set(0)
    tip_label.config(text="Tip: ")
    reps_label.config(text="Reps: 0")
    countdown_start_time = time.time()

    if video_writer:
        video_writer.release()

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = 20.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_filepath = f"temp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
    video_writer = cv2.VideoWriter(video_filepath, fourcc, fps, (width, height))

def set_mode_and_start():
    
    global goal_reps, mode, countdown_active, countdown_start_time
    try:
        g = int(entry_goal.get())
        if g <= 0:
            raise ValueError
        goal_reps = g
        mode = mode_var.get()
        reset_session()
        countdown_start_time = time.time()
    except ValueError:
        messagebox.showerror("Invalid Input", "Enter a positive integer for reps.")



def camera_loop():
  
    global reps, direction, tracking_active, form_feedback
    global countdown_active, countdown_start_time

    ret, frame = cap.read()
    if not ret:
        root.after(10, camera_loop)
        return

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)
    annotated = frame.copy()

    # Countdown overlay
    if countdown_active:
        elapsed = time.time() - countdown_start_time
        count_num = 5 - int(elapsed)
        if count_num > 0:
            cv2.putText(annotated, f"Get Ready: {count_num}", (50, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 6)
        else:
            countdown_active = False
            tracking_active = True
            global last_tip_time
            last_tip_time = time.time()

    elif tracking_active and results.pose_landmarks:
        mp_draw.draw_landmarks(annotated, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        lm = results.pose_landmarks.landmark

        if mode == "Curl":
            shoulder, elbow, wrist = [lm[12].x, lm[12].y], [lm[14].x, lm[14].y], [lm[16].x, lm[16].y]
            angle = calculate_angle(shoulder, elbow, wrist)
            if angle < 40 and direction == 0:
                direction = 1
            if angle > 160 and direction == 1:
                reps += 1
                direction = 0
                recorded_data.append([datetime.datetime.now().strftime("%H:%M:%S"), mode, reps, bad_form_count])
            evaluate_form_curl(angle, shoulder[1], wrist[1])

        elif mode == "Push-up":
            shoulder, elbow, wrist = [lm[11].x, lm[11].y], [lm[13].x, lm[13].y], [lm[15].x, lm[15].y]
            angle = calculate_angle(shoulder, elbow, wrist)
            if angle < 90 and direction == 0:
                direction = 1
            if angle > 150 and direction == 1:
                reps += 1
                direction = 0
                recorded_data.append([datetime.datetime.now().strftime("%H:%M:%S"), mode, reps, bad_form_count])
            evaluate_form_pushup(angle)

        else:  # Squat
            hip, knee, ankle = [lm[24].x, lm[24].y], [lm[26].x, lm[26].y], [lm[28].x, lm[28].y]
            angle = calculate_angle(hip, knee, ankle)
            if angle < 90 and direction == 0:
                direction = 1
            if angle > 160 and direction == 1:
                reps += 1
                direction = 0
                recorded_data.append([datetime.datetime.now().strftime("%H:%M:%S"), mode, reps, bad_form_count])
            evaluate_form_squat(hip[1], knee[1], angle)

        progress.set(min((reps / goal_reps) * 100, 100))
        progress_bar.update()
        reps_label.config(text=f"Reps: {reps}/{goal_reps}")

        if reps >= goal_reps:
            tracking_active = False
            save_session()
            messagebox.showinfo("Complete", f"{mode} goal reached! Session saved.")

    cv2.putText(annotated, f"Reps: {reps}/{goal_reps}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)

    if video_writer and not countdown_active:
        video_writer.write(annotated)

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    main_display.imgtk = ImageTk.PhotoImage(image=img)
    main_display.configure(image=main_display.imgtk)

    wire_img = Image.fromarray(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
    wire_display.imgtk = ImageTk.PhotoImage(image=wire_img)
    wire_display.configure(image=wire_display.imgtk)

    tip_label.config(text=f"Tip: {form_feedback}")
    root.after(10, camera_loop)


cap = cv2.VideoCapture(0)
root = tk.Tk()
root.title("Smart Fitness Tracker")
root.configure(bg="#222222")
root.minsize(1000, 600)


style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", background="#444", foreground="white", font=("Segoe UI", 10), padding=6)
style.map("TButton", background=[('active', '#666')])
style.configure("TLabel", background="#222", foreground="white")
style.configure("Horizontal.TProgressbar", background="#76c7c0")


container = tk.Frame(root, bg="#222")
container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


video_frame = tk.Frame(container, bg="#111")
video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
main_display = tk.Label(video_frame, bg="#111")
main_display.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
wire_display = tk.Label(video_frame, bg="#111")
wire_display.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)


control_frame = tk.Frame(container, bg="#222", width=300)
control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
mode_var = tk.StringVar(value="Curl")
ttk.Label(control_frame, text="Mode:").pack(anchor="w", pady=(10, 2), padx=10)
ttk.OptionMenu(control_frame, mode_var, "Curl", "Curl", "Push-up", "Squat").pack(anchor="w", padx=10, pady=(0, 10), fill=tk.X)
ttk.Label(control_frame, text="Target Reps:").pack(anchor="w", padx=10)
entry_goal = ttk.Entry(control_frame, width=10)
entry_goal.insert(0, "10")
entry_goal.pack(anchor="w", padx=10, pady=(0, 15))
ttk.Button(control_frame, text="▶ Start New Session", command=set_mode_and_start).pack(anchor="w", padx=10, pady=(0, 10), fill=tk.X)
ttk.Button(control_frame, text="❌ Quit & Save", command=lambda: (save_session(), cap.release(), root.destroy())).pack(anchor="w", padx=10, pady=(0, 20), fill=tk.X)
progress = tk.DoubleVar()
progress_bar = ttk.Progressbar(control_frame, maximum=100, variable=progress, length=250)
progress_bar.pack(padx=10, pady=(0, 5), fill=tk.X)
reps_label = ttk.Label(control_frame, text="Reps: 0/10", font=("Segoe UI", 12, "bold"))
reps_label.pack(anchor="w", padx=10, pady=(0, 15))
tip_label = ttk.Label(control_frame, text="Tip: ", wraplength=250)
tip_label.pack(anchor="w", padx=10, pady=(0, 10))



camera_loop()
root.mainloop()
cap.release()
cv2.destroyAllWindows()
