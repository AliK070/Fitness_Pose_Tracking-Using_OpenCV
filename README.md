# Smart Fitness Tracker using OpenCV 

## Overview
This tracker uses computer vision and pose detection (via MediaPipe) to evaluate common workouts: curls, push-ups, and squats.

## How Detection Works

### 1. Bicep Curls
- Uses the angle between **shoulder → elbow → wrist** on the right arm.
- A rep is counted when:
  - Angle decreases below 40° (arm up)
  - Then increases past 160° (arm down)
- Tips are triggered if the elbow swings or angle exceeds natural bounds.

### 2. Push-ups
- Uses **left shoulder → elbow → wrist** angle.
- A rep is counted when:
  - Angle drops below 90° (going down)
  - Then exceeds 150° (coming up)
- Tips correct shallow reps or collapsing posture.

### 3. Squats
- Uses **hip → knee → ankle** angle on the right side.
- A rep is counted when:
  - Angle drops below 90° (squat down)
  - Then exceeds 160° (stand up)
- Tips correct depth and knee alignment.

## Outputs
- **CSV logs** with time, mode, rep count, and bad form count.
- **Tips CSV** for feedback history.
- **Recorded video** (AVI) of the session.
