"""
An analyzer for the fridrich weather-station network.

Author:
Nilusink
"""
from scipy.ndimage import gaussian_filter1d
from fridrich.backend import Connection
import matplotlib.pyplot as plt
from typing import Dict, List
from scipy import interpolate
import pandas as pd
import typing as tp
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
            for date in list(station_log):
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
    all_dates: list = sorted(list(all_dates))[DATES:]

    new_data = {}
    for station in temp_graphs:
        new_data[station]: dict = {}
        cnt = 0
        for date in all_dates:
            now = temp_graphs[station][date]
            new_data[station][date] = now
            cnt += now if now != MISSING_VALUE else 0

        # remove all stations that don't actually have data for this period
        if cnt == 0:
            new_data.pop(station)

    data = {"Dates": all_dates}

    # append the data of each individual station and smooth the curve using a gaussian filter
    data.update({
        station: gaussian_filter1d(list(new_data[station].values()), sigma=2) for station in new_data
    })

    all_values = [value for station in new_data for value in new_data[station].values() if value != MISSING_VALUE]

    ax = pd.DataFrame(data).plot(linestyle="dotted")

    data = {"dates": all_dates}

    # daily average
    days: tp.List[str] = list({date.split("-")[0] for date in all_dates})
    days.sort()

    # calculate the average value per day
    average_data: tp.Dict[str, list] = {}
    for station in new_data:
        # check if the key already exists in the dictionary
        if station not in average_data:
            average_data[station] = []

        # collect all values across a day
        for day in days:
            daily_values = []
            new_data[station]: tp.Dict[str, float]
            for date in all_dates:
                value = new_data[station][date]
                if day in date:
                    if value != MISSING_VALUE:
                        daily_values.append(value)
                        continue

            # calculate average
            if len(daily_values) == 0:
                average_data[station].append(np.inf)
                continue

            average_data[station].append(sum(daily_values) / len(daily_values))

    d_r = list(range(0, len(days) * 288, 288))
    n_r = list(range(len(all_dates)))
    for station in average_data:
        f = interpolate.interp1d(d_r, average_data[station])
        new_d = gaussian_filter1d(f(n_r), sigma=50)
        data.update({
            station + " daily average": new_d
        })

    # make graph
    pd.DataFrame(data).plot(ax=ax)

    # configure graph
    plt.xlabel("Date")
    plt.ylabel(DATA_DESCRIPTION[DATA_POINT])

    # x and y ticks
    v_n = len(all_dates) // NUM_LABELS
    v_n = v_n if v_n != 0 else len(all_dates)
    plt.xticks(range(0, len(all_dates), v_n),
               [all_dates[i] for i in range(0, len(all_dates), v_n)])

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
    plt.legend(title="Weather Stations")
    plt.grid()

    # show graph
    plt.show()

    print(f"last measurement: {days[-1]}")


if __name__ == '__main__':
    main()
