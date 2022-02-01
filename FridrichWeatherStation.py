"""
Run on a device that can get weather data, replace lines 35 to 37 with your code.

Author:
Nilusink
"""
from fridrich import AuthError, RegistryError
from fridrich.backend import Connection
from fridrich.classes import Daytime
from random import randint
import asyncio
import signal
import sys


# default login data for weather stations
USERNAME = "WStation"
PASSWORD = "ISetDaWeather"

# set the station name and location for THIS station
NAME = "WeatherStation1"
LOCATION = "Somewhere"

# settings for station
SEND_INTERVAL: int | float = 60*15   # wait time in seconds (in this case every 15 minutes)


# default variables
RUNNING: bool = True


async def send_weather() -> None:
    """
    login to the server, send weather data, logout
    """
    print(f"Running send_weather ({Daytime.now().to_string()})")
    with Connection(host="server.fridrich.xyz") as c:
        c.auth(USERNAME, PASSWORD)
        if not c:
            raise AuthError("Invalid credentials")

        # collect weather data, replace the random values with the way you want to get weather data
        temp = randint(0, 40)
        hum = randint(20, 90)
        press = randint(800, 1100)

        # commit data to the server
        try:
            c.commit_weather_data(station_name=NAME, temperature=temp, humidity=hum, pressure=press, wait=False)

        except RegistryError:
            print(f"Not registered, registering now")
            c.register_station(station_name=NAME, location=LOCATION, wait=True)
            c.commit_weather_data(station_name=NAME, temperature=temp, humidity=hum, pressure=press, wait=True)

            c.send()


async def main() -> None:
    """
    main Function
    """
    while RUNNING:
        try:
            last_run = asyncio.create_task(send_weather())
            await asyncio.sleep(SEND_INTERVAL)
            await last_run

        except KeyboardInterrupt:
            return end(0)


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
    asyncio.run(main())
    end()
