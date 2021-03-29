import cv2
import face_detector
import time


def main():
    poll_rate = 0.1
    cap = cv2.VideoCapture(0)
    fd = face_detector.FaceDetector()
    if not cap.isOpened():
        raise IOError("Cannot open webcam")

    while True:
        _, frame = cap.read()
        frame = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        _, frame_png = cv2.imencode('.png', frame)
        frame_bytes = frame_png.tobytes()

        # check if there is a face
        prob = fd.detect_face_from_bytes(frame_bytes)
        if prob > 0.95:
            print(f"Detected a face: {prob}")
            # check if this is an authorized person
            with open('images/Joe-Benczarski.jpg', 'rb') as tgt:
                auth = fd.compare_face_from_bytes(frame_bytes, tgt.read(), 99.5)
                if auth:
                    print("User is authorized")
        else:
            print(f"Not a face: {prob}")

        #cv2.imshow('Input', frame)
        c = cv2.waitKey(1)
        if c == 27:
            break

        time.sleep(poll_rate)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
