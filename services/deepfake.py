import cv2
import numpy as np
import requests
import tempfile

def download_video(url):
    r = requests.get(url, stream=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")

    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            tmp.write(chunk)

    tmp.close()
    return tmp.name


def analyze_frames(video_path):
    cap = cv2.VideoCapture(video_path)

    fake_score = 0
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # basit anomali kontrolü
        blur = cv2.Laplacian(gray, cv2.CV_64F).var()

        if blur < 50:  # düşük kalite → şüpheli
            fake_score += 1

        if frame_count > 20:
            break

    cap.release()

    if frame_count == 0:
        return 0

    return int((fake_score / frame_count) * 100)


def detect_deepfake(video_url):
    try:
        path = download_video(video_url)
        score = analyze_frames(path)

        status = "güvenli"
        if score > 60:
            status = "deepfake şüpheli"

        return {
            "score": score,
            "status": status
        }

    except Exception as e:
        return {
            "score": 0,
            "status": "analiz edilemedi"
        }