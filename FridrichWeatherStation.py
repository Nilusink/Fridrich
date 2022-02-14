"""
Requests weather data from an arduino (or a Fridrich Board)
and forwards it to the server

Author:
Nilusink
"""
from fridrich.errors import AuthError, RegistryError
from fridrich.backend import Connection
from fridrich.classes import Daytime
import binascii
import serial
import signal
import json
import time
import sys
import os


# load data from config file
try:
    with open(os.getcwd()+"/config/weather_station.json", "r") as inp:
        config = json.load(inp)
        # login data for weather station
        USERNAME: str = config["fridrich_user"]
        PASSWORD: str = config["fridrich_pwd"]

        # load the station name and location for THIS station
        NAME = config["station_name"]
        LOCATION = config["station_location"]

except KeyError:
    raise KeyError("the weather_station config file doesn't contain the correct values!")

# default variables and class instances
RUNNING: bool = True
STATION: serial.Serial = ...
for _ in range(5):
    try:
        STATION = serial.Serial(port="/dev/ttyUSB0", baudrate=9600, timeout=.1)    # you probably have to change the USB port for your arduino
        STATION.flush()
        break

    except (Exception,):
        continue

if STATION is ...:
    exit(-1)


def request_data() -> dict:
    """
    send a ping to the arduino and wait for the
    response, then parse from "name1:value1,name2:value2"
    to {"name1": value1, "name2": value2}
    """
    data = ""
    tries = 0
    while data == "":
        STATION.reset_input_buffer()
        tries += 1
        STATION.write(b"some data please")  # ask politely for some weather data
        STATION.flush()
        time.sleep(.5)
        try:
            data = STATION.readline().decode().rstrip("\n").rstrip("\r")

        except (Exception,):
            continue

        if tries > 10:
            raise ValueError("cannot read sensor")

    # parse data
    try:
        out: dict = {}
        for element in data.split(","):
            parts = element.split(":")
            out[parts[0]] = float(parts[1])

        return out
    
    except IndexError:
        return {}


def send_weather() -> None:
    """
    login to the server, send weather data, logout
    """
    print(f"Running send_weather ({Daytime.now().to_string()})")
    try:
        data = request_data()

    except ValueError:
        data = {}

    print(f"{data=}")
    for _ in range(10):
        try:
            with Connection(host="server.fridrich.xyz") as c:
                # try to send data backed up from the last time it couldn't be sent
                if os.path.exists("temp_weather.json"):
                    with open("temp_weather.json", "r") as in_file:
                        for line in in_file.readlines():
                            t, wd = line.rstrip("\n").split("|||")
                            c.commit_weather_data(station_name=NAME, weather_data=json.loads(wd), wait=True, set_time=t)

                # collect weather data, replace the random values with the way you want to get weather data

                # commit data to the server
                try:
                    c.auth(USERNAME, PASSWORD)
                    if not c:
                        raise AuthError("Invalid credentials")

                    c.commit_weather_data(station_name=NAME, weather_data=data, wait=True)  # if there was an error sending the message to the server, keep in buffer
                    c.send()

                except RegistryError:
                    print(f"Not registered, registering now")
                    c.register_station(station_name=NAME, location=LOCATION, wait=False)

                    c.commit_weather_data(station_name=NAME, weather_data=data, wait=True)
                    c.send()

                except ConnectionError:
                    time.sleep(5)
                    continue

                return

        except binascii.Error:
            # try to avoid incorrect padding error
            time.sleep(1)
            continue

    else:
        with open("temp_weather.json", "a") as out:
            now_time = time.strftime("%Y.%m.%d")+"-"+Daytime.now().to_string()
            out.write(f"{now_time}|||{json.dumps(data)}")
        time.sleep(60)


def main() -> None:
    """
    main Function
    """
    while RUNNING:
        try:
            if time.strftime("%M")[-1] in ("5", "0"):    # send every 5 minutes
                send_weather()
                time.sleep(60)

            # for performance
            time.sleep(.5)

        except KeyboardInterrupt:
            return end(0)

        except AuthError:
            continue


def end(*signals) -> None:
    """
    gets called if the session gets terminated or the program exits
    """
    global RUNNING
    print("shutting down...")
    RUNNING = False
    sys.exit(signals[0])


if __name__ == "__main__":
    # signal handling (termination)
    signal.signal(signal.SIGINT, end)
    signal.signal(signal.SIGTERM, end)

    # run program
    main()
    end()
