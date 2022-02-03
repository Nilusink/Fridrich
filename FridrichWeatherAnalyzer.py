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
DATA_POINT: str = "temp"    # must be temp | hum | press

# default variables
DATA_DESCRIPTION: Dict[str, str] = {    # label for the plot, mustn't be changed
    "temp": "Temperature in °C",
    "hum": "Humidity in %",
    "press": "Pressure in hPa"
}


def main() -> None:
    """
    main program
    """
    with Connection(host="server.fridrich.xyz") as c:
        c.auth(USERNAME, PASSWORD)
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
                temp_graphs[station["station_name"]][short_date] = station_log[date][DATA_POINT]

        # combine all dates from every weather station
        all_dates: set = {date for station in temp_graphs for date in temp_graphs[station]}

        # if one of the stations doesn't have a measurement for all dates, set None
        for station in temp_graphs:
            if len(temp_graphs[station]) < len(all_dates):
                for date in all_dates:
                    if date not in temp_graphs[station]:
                        temp_graphs[station][date] = None

    # configure data for graphing
    all_dates: list = list(all_dates)

    data = {"dates": all_dates}
    data.update({
        station: temp_graphs[station].values() for station in temp_graphs
    })
    data = pd.DataFrame(data)

    # make graph
    g = sns.lineplot(x="dates", y="value", hue="variable", data=pd.melt(data, ["dates"]), ci=None)

    # configure graph
    g.set(ylabel=DATA_DESCRIPTION[DATA_POINT], xlabel="Date")

    plt.xticks([all_dates[i] for i in range(0, len(all_dates), len(all_dates)//8)])
    plt.legend(title="Weather Station")

    # show graph
    plt.show()


if __name__ == '__main__':
    main()
