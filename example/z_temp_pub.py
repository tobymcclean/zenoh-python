from zenoh import Zenoh
import random
import time
import sys

random.seed()


def read_temp():
    return random.randint(15, 30)


def run_sensor_loop(z, pub):
    # read and produce e temperature every half a second
    while True:
        t = read_temp()
        z.stream_data(pub, str(t).encode())
        time.sleep(0.1)


if __name__ == "__main__":
    locator = None
    if len(sys.argv) > 1:
        locator = sys.argv[1]

    z = Zenoh.open(locator)
    pub = z.declare_publisher('/myhome/kitcken/temp')
    run_sensor_loop(z, pub)
