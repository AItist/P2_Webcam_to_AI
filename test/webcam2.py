from multiprocessing import Process, Array, Value, Queue, Lock
import cv2
import numpy as np
import time

def capture_image(shared_array, size, lock, index):
    cap = cv2.VideoCapture(index)

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Write the image to shared memory
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_bytes = img_encoded.tobytes()

        with lock:
            shared_array[:len(img_bytes)] = np.frombuffer(img_bytes, dtype='uint8')
            size.value = len(img_bytes)

        time.sleep(1/30)

    # When everything done, release the capture
    cap.release()

def process_image(shared_array, size, lock, queue):
    while True:
        with lock:
            img_bytes = bytes(shared_array[:size.value])  # only read the number of bytes that were written

        if img_bytes:
            img_np = np.frombuffer(img_bytes, dtype='uint8')
            img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

            # Now img is a color OpenCV image
            # Do processing here...

            # Instead of showing the image here, we put it on the queue
            queue.put(img)

        time.sleep(0.1)

def display_image(queue1, queue2):
    while True:
        img1 = queue1.get()  # Get image from first queue
        img2 = queue2.get()  # Get image from second queue

        if img1 is not None:
            cv2.imshow('frame1', img1)
        if img2 is not None:
            cv2.imshow('frame2', img2)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Exit if Q is pressed
            break

if __name__ == '__main__':
    # Maximum size for a JPEG image in bytes
    max_size = 1024 * 1024 * 3

    lock1 = Lock()
    lock2 = Lock()
    shared_array1 = Array('B', max_size)
    shared_array2 = Array('B', max_size)
    size1 = Value('i', 0)
    size2 = Value('i', 0)
    queue1 = Queue()  # Queue for images from first camera
    queue2 = Queue()  # Queue for images from second camera

    p1 = Process(target=capture_image, args=(shared_array1, size1, lock1, 0))
    p2 = Process(target=process_image, args=(shared_array1, size1, lock1, queue1))
    p3 = Process(target=capture_image, args=(shared_array2, size2, lock2, 1))
    p4 = Process(target=process_image, args=(shared_array2, size2, lock2, queue2))

    p1.start()
    p2.start()
    p3.start()
    p4.start()

    # In the main process, we display the images
    display_image(queue1, queue2)

    p1.join()
    p2.join()
    p3.join()
    p4.join()
