from Adafruit_IO import MQTTClient
import sys
import time

#list of IO_feed
AIO_FEED_ID = ["button1","ai_noti"]
#username_AIO
AIO_USERNAME = "sonlam7220"
#key_AIO
AIO_KEY = "aio_xGlf92dguJZ0lJMMMlcjWWkWO4T1"

def connected(client):
    print("Connected successful ...")
    #subcribe IO-feeds in adafruit from python gateway
    for i in AIO_FEED_ID:
        client.subscribe(i)

def subscribe(client , userdata , mid , granted_qos):
    #notification of finish subcriber feeds to client
    print("Subscribe successful ...")

def disconnected(client):
    print("Disconnected...")
    sys.exit (1)

def message(client , feed_id , payload):
    #notification of receiving data from feeds to client
    print("Receiving data: " + payload + " from feed id: " + feed_id)