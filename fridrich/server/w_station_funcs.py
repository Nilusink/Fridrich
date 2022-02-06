"""
for weather-stations to commit data to the pool

Author:
Nilusink
"""
from fridrich.server.server_funcs import send_success
from fridrich.server.classes import User
from fridrich.server import Const
from traceback import format_exc
import json


def register(message: dict, user: User, *_args) -> None:
    """
    register a new weather-station
    """
    tmp: list
    try:
        tmp = json.load(open(Const.WeatherDir+"all.json", "r"))

    except (json.JSONDecodeError, FileNotFoundError):
        tmp = []

    for element in tmp:
        if message["station_name"] == element["station_name"]:
            mes = {
                    'Error': 'RegistryError',
                    "info": "weather-station is already registered"
                }
            user.send(mes, message_type="Error")
            return

    tmp.append({
        "station_name": message["station_name"],
        "location": message["location"]
    })

    with open(Const.WeatherDir+"all.json", "w") as out_file:
        json.dump(tmp, out_file, indent=4)

    with open(Const.WeatherDir+message["station_name"]+".json", "w") as out_file:
        out_file.write("{}")

    send_success(user)


def commit_data(message: dict, user: User, *_args) -> None:
    """
    commit data for already registered stations
    """
    now_data: dict
    station_data: dict
    try:
        if not check_if_registered(message, user, *_args):
            mes = {
                    'Error': 'RegistryError',
                    "info": "weather-station is not registered yet"
                }
            user.send(mes, message_type="Error")
            return

        try:
            now_data = json.load(open(Const.WeatherDir+"now.json", "r"))

        except (json.JSONDecodeError, FileNotFoundError):
            now_data = {}

        station_name = message["station_name"]
        commit_time = message["time"]
        message.pop("type")
        message.pop("station_name")

        now_data[station_name] = message.copy()  # copy so we don't get strange dependencies

        with open(Const.WeatherDir+"now.json", "w") as out_file:
            json.dump(now_data, out_file, indent=4)

        try:
            station_data = json.load(open(Const.WeatherDir+station_name+".json", "r"))

        except (json.JSONEncoder, FileNotFoundError):
            station_data = {}

        message.pop("time")
        station_data[commit_time] = message.copy()

        with open(Const.WeatherDir + station_name+".json", "w") as out_file:
            json.dump(station_data, out_file, indent=4)

        send_success(user)

    except KeyError:
        print(format_exc())
        user.send({
            "Error": "KeyError",
            "info": "Not all keys are given",
            "full": format_exc()
        })


def check_if_registered(message: dict, _user: User, *_args) -> bool:
    """
    check if a weather-station is already registered
    """
    try:
        return message["station_name"] in [station["station_name"] for station in json.load(open(Const.WeatherDir+"all.json", "r"))]

    except FileNotFoundError:
        return False


def get_now(_message: dict, user: User, *_args) -> None:
    """
    send a dict of all weather-stations with their current measurement
    """
    now_data: dict
    try:
        now_data = json.load(open(Const.WeatherDir+"now.json", "r"))

    except (json.JSONDecodeError, FileNotFoundError):
        now_data = {}

    user.send(now_data)


def get_log(message: dict, user: User, *_args) -> None:
    """
    send the log of a specific weather station
    """
    try:
        station_log = json.load(open(Const.WeatherDir+message["station_name"]+".json", "r"))

    except FileNotFoundError:
        user.send({
            "Error": "KeyError",
            "info": f"Weather station with name ({message['station_name']}) not registered!"
        })
        return

    user.send(station_log)


def get_stations(_message: dict, user: User, *_args) -> None:
    """
    send a dict of all currently registered weather station names and locations
    """
    try:
        stations = json.load(open(Const.WeatherDir+"all.json", "r"))

    except FileNotFoundError:
        user.send({})
        return

    user.send(stations)
