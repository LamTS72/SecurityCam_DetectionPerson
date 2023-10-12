import threading
import time
import sys

from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit
import cv2
import webbrowser
import socket
import signal
from run_AI_yolo import *
from webcam import *
from Adafruit_IO import MQTTClient
from tensorflow.compat.v1 import InteractiveSession
from tensorflow.compat.v1 import ConfigProto

camera0 = Webcam(0)
camera1 = Webcam(1)
########################
run_yolo = Detect_Yolo()
app = Flask(__name__)
socketio = SocketIO(app)
########################
check_signal0 = None
num_person0 = 0
camera0_on = 1
state0 = 1
########################
check_signal1 = None
num_person1 = 0
camera1_on = 1
state1 = 1
########################
# load configuration for object detector
model_filename = 'model_data/mars-small128.pb'
config = ConfigProto()
#config.gpu_options.allow_growth = Fasle
session = InteractiveSession(config=config)
saved_model_loaded = tf.saved_model.load(run_yolo._weights, tags=[tag_constants.SERVING])
infer = saved_model_loaded.signatures['serving_default']
# Get the IP address of the machine running the app
hostname = socket.gethostname()

ip_address = socket.gethostbyname(hostname)

# # Define a global lock for thread-safe access to the model
# lock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def generate_frames(cam):
    global check_signal0, num_person0, session, config

    # Definition of the parameters
    max_cosine_distance = 0.4
    nn_budget = None
    nms_max_overlap = 1.0

    # initialize deep sort
    encoder = gdet.create_box_encoder(model_filename, batch_size=1)
    # calculate cosine distance metric
    metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
    # initialize tracker
    tracker = Tracker(metric)

    # STRIDES, ANCHORS, NUM_CLASS, XYSCALE = utils.load_config(FLAGS)
    input_size = run_yolo._size
    video_path = run_yolo._video

    if cam == 0:
        frame_num0 = 0
        num_handle_frame0 = 0

        global camera0_on, state0
        # while video is running
        while True:
            # Đọc ảnh từ class Webcam
            if camera0_on == 1:
                if state0 == 0:
                    state0 = 1
                    camera0.vid = cv2.VideoCapture(0)  # Turn on camera

                frame = next(camera0.get_frame())
                display_frame = frame.copy()
                resized_frame = cv2.resize(frame, (860, 640))
                frame_num0 += 1
                num_handle_frame0 += 1
                frame, check_signal0, num_person0 = run_yolo.detect_run(frame, frame_num0, num_handle_frame0, input_size
                                                                        , infer, tracker, encoder, nms_max_overlap)

                # Trả về cho web bằng lệnh yeild
                yield b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg',resized_frame)[1].tobytes() + b'\r\n--frame\r\n'
            else:
                camera0.vid.release()  # Turn off camera
                pass

    elif cam == 1:
        frame_num1 = 0
        num_handle_frame1 = 0

        global camera1_on, state1
        # while video is running
        while True:
            # Đọc ảnh từ class Webcam
            if camera1_on == 1:
                if state1 == 0:
                    state1 = 1
                    camera1.vid = cv2.VideoCapture(1)  # Turn on camera
                frame = next(camera1.get_frame())
                display_frame = frame.copy()
                resized_frame = cv2.resize(frame, (860, 640))
                frame_num1 += 1
                num_handle_frame1 += 1
                frame, check_signal, num_person = run_yolo.detect_run(frame, frame_num1, num_handle_frame1, input_size,
                                                                      infer, tracker, encoder, nms_max_overlap)
                # Nhận diện qua model YOLO

                # Trả về cho web bằng lệnh yeild
                #yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'
                yield b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', resized_frame)[
                    1].tobytes() + b'\r\n--frame\r\n'
            else:
                camera1.vid.release()  # Turn off camera


@app.route('/mystream')
def video_feed():
    return Response(generate_frames(0), mimetype='multipart/x-mixed-replace; boundary=frame')
    # return Response(generate_frames(), mimetype='video/mp4')

@app.route('/mystream1')
def video_feed1():
    return Response(generate_frames(1), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

@app.route('/1')
def index1():
    """Video streaming home page."""
    return render_template('index1.html')

@socketio.on('stream')
def handle_stream():
    for frame in generate_frames(0):
        emit('image', {'data': frame})

# define the keyboard interrupt handler function
def keyboard_interrupt_handler(signal, frame, camera):
    camera.vid.release()
    cv2.destroyAllWindows()
    print("\nVideo streaming stopped.")
    exit(0)

# register the keyboard interrupt handler function
signal.signal(signal.SIGINT, keyboard_interrupt_handler)

def webServer():
    #list of IO_feed
    AIO_FEED_ID = ["switchcamera", "ainoti", "quantity"]
    # username_AIO
    AIO_USERNAME = "io-username"
    # key_AIO
    AIO_KEY = "io-key"

    def connected(client):
        print("Connected successful ...")
        # subcribe IO-feeds in adafruit from python gateway
        for i in AIO_FEED_ID:
            client.subscribe(i)

    def subscribe(client, userdata, mid, granted_qos):
        # notification of finish subcriber feeds to client
        print("Subscribe successful ...")

    def disconnected(client):
        print("Disconnected...")
        sys.exit(1)

    def message(client, feed_id, payload):
        global camera0_on, state0
        # notification of receiving data from feeds to client
        print("Receiving data: " + payload + " from feed id: " + feed_id)
        if feed_id == "switchcamera":
            if payload == '0':
                camera0_on = 0
                state0 = 0
                print("Camera turned off " + str(camera0_on))
            elif payload == '1':
                camera0_on = 1
                print("Camera turned on " + str(camera0_on))
###################################################
    client = MQTTClient(AIO_USERNAME, AIO_KEY)
    client.on_connect = connected
    client.on_disconnect = disconnected
    client.on_message = message
    client.on_subscribe = subscribe
    client.connect()
    client.loop_background()
##################################################
    def handle_ai():
        global check_signal0, num_person0
        counter = 10
        while True:
            counter -= 1
            if counter <= 0:
                counter = 10
                if check_signal0 is not None:
                    client.publish("ainoti", check_signal0)
                    client.publish("quantity", num_person0)
            time.sleep(0.5)

    t2 = threading.Thread(target=handle_ai, name='t2')
    t2.start()

    def handle_ai1():
        global check_signal1, num_person1
        counter = 10
        while True:
            counter -= 1
            if counter <= 0:
                counter = 10
                if check_signal1 is not None:
                    client.publish("ainoti1", check_signal1)
                    client.publish("quantity1", num_person1)
            time.sleep(0.5)

    t2 = threading.Thread(target=handle_ai1, name='t2')
    t2.start()

    socketio = SocketIO(app, transports=['polling', 'websocket'])
    webbrowser.open_new('http://' + ip_address + ':8880/mystream')
    webbrowser.open_new('http://' + ip_address + ':8880/mystream1')
    # Start the Flask-SocketIO app
    socketio.run(app, host='0.0.0.0', port=8880, allow_unsafe_werkzeug=True)


while True:
    webServer()
    pass