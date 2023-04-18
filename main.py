
import threading
import time
import random

from flask import Flask, Response
from flask_socketio import SocketIO, emit
import cv2
import webbrowser
import socket
import signal
from adafruit_server import *


app = Flask(__name__)
socketio = SocketIO(app)

# Get the IP address of the machine running the app
hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Open the default browser to the app's URL
camera = cv2.VideoCapture(0)

client = MQTTClient(AIO_USERNAME, AIO_KEY)
client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message
client.on_subscribe = subscribe
client.connect()
client.loop_background()

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            #client.publish("ai_noti", "detect person")
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/mystream')
def index():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    #return Response(generate_frames(), mimetype='video/mp4')

@socketio.on('stream')
def handle_stream():
    for frame in generate_frames():
        emit('image', {'data': frame})

# define the keyboard interrupt handler function
def keyboard_interrupt_handler(signal, frame):
    camera.release()
    cv2.destroyAllWindows()
    print("\nVideo streaming stopped.")
    exit(0)

# register the keyboard interrupt handler function
signal.signal(signal.SIGINT, keyboard_interrupt_handler)

#if __name__ == '__main__':
def webServer():
   socketio = SocketIO(app, transports=['polling', 'websocket'])
   webbrowser.open_new('http://' + ip_address + ':8880/mystream')
   # Start the Flask-SocketIO app
   socketio.run(app, host='0.0.0.0', port=8880, allow_unsafe_werkzeug=True)

def handle_ai():
    counter = 10
    while True:
        counter -= 1
        if counter <= 0 :
            counter = 10
            # temp = random.randint(10, 50)
            # client.publish("sensor1", temp)

        time.sleep(0.5)

while True:
    t1 = threading.Thread(target=webServer, name='t1')
    t2 = threading.Thread(target=handle_ai, name='t2')

    t1.start()
    t2.start()

    t1.join()
    t2.join()


