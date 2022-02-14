"""
An analyzer for the fridrich weather-station network.

Author:
Nilusink
"""
from fridrich.backend import Connection
import matplotlib.pyplot as plt
from typing import Dict, List
import seaborn as sns
import pandas as pd


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


def main() -> None:
    """
    main program
    """
    # data_point = DATA_POINT
    # values = 288
    with Connection(host="server.fridrich.xyz") as c:
        c.auth(USERNAME, PASSWORD)
        stations = c.get_weather_stations()

        temp_graphs: Dict[str, Dict[str, float | None]] = {}
        for station in stations:
            temp_graphs[station["station_name"]]: dict = {}

            # append all log-times to the list
            station_log = c.get_temps_log(station["station_name"])
            for date in station_log:
                # remove second from date
                short_date = ":".join(date.split(":")[:-1])

                # append data for date
                if type(DATA_POINT) == tuple:
                    for point in DATA_POINT:
                        if point in station_log[date]:
                            temp_graphs[station["station_name"]][short_date] = station_log[date][point]
                            break
                    else:
                        temp_graphs[station["station_name"]][short_date] = None

                    continue

                if DATA_POINT in station_log[date]:
                    temp_graphs[station["station_name"]][short_date] = station_log[date][DATA_POINT]

                else:
                    temp_graphs[station["station_name"]][short_date] = None
    #
    #     # combine all dates from every weather station
    #     all_dates: set = {date for station in temp_graphs for date in temp_graphs[station]}
    #
    #     # if one of the stations doesn't have a measurement for all dates, set None
    #     for station in temp_graphs:
    #         if len(temp_graphs[station]) < len(all_dates):
    #             for date in all_dates:
    #                 if date not in temp_graphs[station]:
    #                     temp_graphs[station][date] = None
    #
    #     # configure data for graphing
    #     all_dates: list = list(all_dates)
    #
    #     data = {"dates": all_dates[-values::]}
    #     data.update({
    #         station: list(temp_graphs[station].values())[-values::] for station in temp_graphs
    #     })
    #     data = pd.DataFrame(data)
    #
    #     # make graph
    #     g = sns.lineplot(x="dates", y="value", hue="variable", data=pd.melt(data, ["dates"]), ci=None)
    #
    #     # configure graph
    #     g.set(ylabel=DATA_DESCRIPTION[data_point[0] if type(data_point) == tuple else data_point], xlabel="Date")
    #
    #     plt.xticks([all_dates[i] for i in range(0, len(all_dates), len(all_dates) // 8)])
    #     plt.legend(title="Weather Station")
    #
    #     # save graph
    #     plt.show()
        # plt.savefig(outfile)
        stations: List[Dict[str, str]] = c.get_weather_stations()

        temp_graphs: Dict[str, Dict[str, float | None]] = {}
        for station in stations:
            temp_graphs[station["station_name"]]: dict = {}

            # append all log-times to the list
            station_log = c.get_temps_log(station["station_name"])
            for date in station_log:
                # remove second from date
                short_date = ":".join(date.split(":")[:-1])

                # append data for date
                if type(DATA_POINT) == tuple:
                    for point in DATA_POINT:
                        if point in station_log[date]:
                            temp_graphs[station["station_name"]][short_date] = station_log[date][point]
                            break
                    else:
                        temp_graphs[station["station_name"]][short_date] = None

                    continue

                if DATA_POINT in station_log[date]:
                    temp_graphs[station["station_name"]][short_date] = station_log[date][DATA_POINT]

                else:
                    temp_graphs[station["station_name"]][short_date] = None

        # combine all dates from every weather station
        all_dates: set = {date for station in temp_graphs for date in temp_graphs[station]}

        # if one of the stations doesn't have a measurement for all dates, set None
        for station in temp_graphs:
            if len(temp_graphs[station]) < len(all_dates):
                for date in all_dates:
                    if date not in temp_graphs[station]:
                        temp_graphs[station][date] = None

    # configure data for graphing
    all_dates: list = sorted(list(all_dates))[-100::]

    new_data = {}
    for station in temp_graphs:
        new_data[station] = []
        cnt = 0
        for date in all_dates:
            now = temp_graphs[station][date]
            new_data[station].append(now)
            cnt += now if now is not None else 0

        # remove all stations that don't actually have data for this period
        if cnt == 0:
            new_data.pop(station)

    data = {"dates": all_dates}
    data.update({
        station: new_data[station] for station in new_data
    })
    data = pd.DataFrame(data)

    # make graph
    plt.figure(figsize=(16, 8))
    g = sns.lineplot(x="dates", y="value", hue="variable", data=pd.melt(data, ["dates"]), ci=None)

    # configure graph
    g.set(ylabel=DATA_DESCRIPTION[DATA_POINT[0] if type(DATA_POINT) == tuple else DATA_POINT], xlabel="Date")

    plt.xticks([all_dates[i] for i in range(0, len(all_dates), len(all_dates)//8)])
    plt.legend(title="Weather Station")

    # show graph
    plt.show()
    # plt.savefig('books_read.png')


if __name__ == '__main__':
    main()
