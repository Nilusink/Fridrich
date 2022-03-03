"""
An analyzer for the fridrich weather-station network.

Author:
Nilusink
"""
from fridrich.backend import Connection
import matplotlib.pyplot as plt
from typing import Dict, List
import pandas as pd
import numpy as np


# Bot login
USERNAME: str = "StatsBot"
PASSWORD: str = "IGetDaStats"

# settings
# data points to collect, when in tuple they are grouped, data_description for first point
DATA_POINT: str | tuple = "Temperature"

# default variables
DATA_DESCRIPTION: Dict[str, str] = {    # label for the plot, mustn't be changed
    "Temperature": "Temperature in °C",
    "hum": "Humidity in %",
    "press": "Pressure in hPa",
    "Temperature Index": "Felt temperature in °C"
}
MISSING_VALUE = np.inf
NUM_LABELS: int = 9

# used to set the amount of values (all_values[DATES::]). here: last 288 values
DATES: int = -288


def main() -> None:
    """
    main program
    """
    # data_point = DATA_POINT
    # values = 288
    with Connection(host="server.fridrich.xyz") as c:
        c.auth(USERNAME, PASSWORD)

        stations: List[Dict[str, str]] = c.get_weather_stations()

        temp_graphs: Dict[str, Dict[str, float | type(MISSING_VALUE)]] = {}
        for station in stations:
            temp_graphs[station["station_name"]]: dict = {}

            # append all log-times to the list
            print(f"getting {station['station_name']}")
            station_log = c.get_temps_log(station["station_name"])
            for date in list(station_log)[DATES::]:
                # remove second from date
                short_date = ":".join(date.split(":")[:-1])

                # append data for date
                if type(DATA_POINT) == tuple:
                    for point in DATA_POINT:
                        if point in station_log[date]:
                            temp_graphs[station["station_name"]][short_date] = station_log[date][point]
                            break
                    else:
                        temp_graphs[station["station_name"]][short_date] = MISSING_VALUE

                    continue

                if DATA_POINT in station_log[date]:
                    temp_graphs[station["station_name"]][short_date] = station_log[date][DATA_POINT]

                else:
                    temp_graphs[station["station_name"]][short_date] = MISSING_VALUE

        # combine all dates from every weather station
        all_dates: set = {date for station in temp_graphs for date in temp_graphs[station]}

        # if one of the stations doesn't have a measurement for all dates, set to infinite
        for station in temp_graphs:
            if len(temp_graphs[station]) < len(all_dates):
                for date in all_dates:
                    if date not in temp_graphs[station]:
                        temp_graphs[station][date] = MISSING_VALUE

    # configure data for graphing
    all_dates: list = sorted(list(all_dates))

    new_data = {}
    for station in temp_graphs:
        new_data[station] = []
        cnt = 0
        for date in all_dates:
            now = temp_graphs[station][date]
            new_data[station].append(now)
            cnt += now if now != MISSING_VALUE else 0

        # remove all stations that don't actually have data for this period
        if cnt == 0:
            new_data.pop(station)

    all_values = [value for station in new_data for value in new_data[station] if value != MISSING_VALUE]

    data = {"Dates": all_dates}

    data.update({
        station: new_data[station] for station in new_data
    })

    data = pd.DataFrame(data)

    # make graph
    data.plot()

    # configure graph
    plt.xlabel("Date")
    plt.ylabel(DATA_DESCRIPTION[DATA_POINT])

    # x and y ticks
    plt.xticks(range(0, len(all_dates), len(all_dates)//NUM_LABELS),
               [all_dates[i] for i in range(0, len(all_dates), len(all_dates)//NUM_LABELS)])

    # calculate the step for the y-axis
    lower_limit = int(min(all_values)-1)
    upper_limit = int(max(all_values)+1)
    potential_steps = (.1, .2, .5, 1, 2, 5, 10)
    max_values = 40
    step: float = .1
    for step in potential_steps:
        if (upper_limit-lower_limit) / step < max_values:
            break

    plt.yticks(np.arange(lower_limit, upper_limit, step))
    plt.legend(title="Weather Station")
    plt.grid()

    # show graph
    plt.show()

    print(f"last measurement: {all_dates[-1]}")


if __name__ == '__main__':
    main()
