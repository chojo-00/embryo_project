# evenness.py

import numpy as np
import cv2
import os

def get_evenness_grade(npy_path):
    if not os.path.exists(npy_path):
        raise FileNotFoundError(f"파일 없음: {npy_path}")

    data = np.load(npy_path, allow_pickle=True).item()
    
    print(f"[📂 .npy 불러오기 성공]: {npy_path}")
    print(f"[📐 데이터 키]: {list(data.keys())}")
    
    mask = data['masks']

    unique_ids = np.unique(mask)
    unique_ids = unique_ids[unique_ids != 0]

    circularities = []
    for cell_id in unique_ids:
        binary_mask = np.uint8(mask == cell_id)
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            continue
        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        if area < 50 or perimeter == 0:
            continue
        circularity = (4 * np.pi * area) / (perimeter ** 2)
        circularities.append(circularity)

    circularities = np.array(circularities)
    RDM = np.mean(np.abs(circularities - np.median(circularities)) / np.median(circularities)) * 100
    CV = (np.std(circularities) / np.mean(circularities)) * 100
    
    print(f"[📊 RDM]: {RDM:.2f}")
    print(f"[📊 CV]: {CV:.2f}")

    def classify(RDM, CV):
        if RDM <= 2.5 and CV <= 3.0:
            return "1등급"
        elif RDM <= 4.5 and CV <= 5.5:
            return "2등급"
        elif RDM <= 6.0 and CV <= 7.5:
            return "3등급"
        else:
            return "4등급"

    return classify(RDM, CV)
