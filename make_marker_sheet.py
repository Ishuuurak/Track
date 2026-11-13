"""Makes marker_sheet.png: an A4 page of identical markers to print and cut into stickers.
Run:  python make_marker_sheet.py
"""
import cv2, numpy as np
d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
m = cv2.aruco.generateImageMarker(d, 7, 300)
cell = cv2.copyMakeBorder(m, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)
cell = cv2.copyMakeBorder(cell, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=180)
H, W = 1754, 1240
sheet = np.full((H, W), 255, np.uint8)
ch, cw = cell.shape
for r in range(H // ch):
    for c in range(W // cw):
        sheet[r*ch:(r+1)*ch, c*cw:(c+1)*cw] = cell
cv2.imwrite("marker_sheet.png", sheet)
print("Saved marker_sheet.png - print at 100% scale, no fit-to-page")
