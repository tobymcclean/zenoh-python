import zenoh
import argparse
import time
import signal 

ap = argparse.ArgumentParser()
ap.add_argument("-z", "--zenohd", required=True,
                help="ip:port for the zenoh broker")

args = vars(ap.parse_args())

def listener(rid, data, length, info):
    print('Received {} bytes of data'.format(length))

if __name__ == '__main__':    
    z = zenoh.Zenoh(args['zenohd'], 'user'.encode(), 'password'.encode())
    r_name = '/demo/hello/python'
    
    print('Declaring Subscriber for {}', r_name)
    
    pub = z.declare_publisher(r_name, SubscriberMode.push(), listener)
    time.sleep(60)