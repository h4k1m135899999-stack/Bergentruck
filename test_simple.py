# test_simple.py
import cv2
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if ret:
        frame_small = cv2.resize(frame, (320, 240))
        cv2.imshow('Teste', frame_small)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
cap.release()
cv2.destroyAllWindows()
