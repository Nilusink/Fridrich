"""
Program that creates Graphs and processes data for each gayking to analyze their behavior

Author: Nilusink
"""
from typing import Dict, List, Tuple, Iterable
import matplotlib.pyplot as plt
from fridrich import backend
from fridrich import *
import seaborn as sns
import tkinter as tk
import pandas as pd
import numpy as np


class Window:
    def __init__(self, connection: backend.Connection) -> None:
        """
        :param connection: logged in Connection instance
        """
        if not connection:
            raise AuthError("Instance of class not logged in!")

        self._c = connection

        self.__root = tk.Tk()
        self.__root.title("GayHistory Analyser")


def av_votes_per_person(values: list | tuple) -> dict:
    """
    :param values: the kings to parse (ordered by date)
    :returns: % how often the person was voted in general
    """
    entries = len(values)
    all_split = [person.lower().replace(" ", "") for element in values for person in element.split("|")]
    out = {}
    for person in set(all_split):
        out[person] = (all_split.count(person) / entries)*100

    return out


def av_streak_per_person(values: list | tuple) -> dict:
    """
    :param values: the kings to parse (ordered by date)
    :returns: average streak per person
    """
    values = [element.lower().replace(" ", "") for element in values]
    all_persons = set([person for element in values for person in element.split("|")])

    streaks = {person: [] for person in all_persons}
    ignore = {person: 0 for person in all_persons}

    def following(lst: list, item: str):
        """
        how many steaks the item has (from beginning of list)
        """
        out = 0
        for element in lst:
            if item in element:
                out += 1
                continue
            break
        return out

    for i in range(len(values)):
        for person in values[i].split("|"):
            if ignore[person] <= i:
                streak = following(values[i::], person)
                ignore[person] = i+streak
                streaks[person].append(streak)
    output = {person: sum(streaks[person]) / len(streaks[person]) for person in streaks}
    return output


def av_shares_per_person(values: list | tuple) -> dict:
    """
    :param values: the kings to parse (ordered by date)
    :returns: how many other persons the person is usually voted with
    """
    values = [element.lower().replace(" ", "") for element in values]
    all_persons = set([person for element in values for person in element.split("|")])

    out = {person: [] for person in all_persons}
    for element in values:
        persons = element.lower().replace(" ", "").split("|")
        for person in persons:
            out[person].append(len(persons))

    return {person: sum(out[person]) / len(out[person]) for person in out}


def votes_per_month(values: Dict[str, List[str] | Tuple[str]]) -> Dict[str, Dict[str, int]]:
    """
    :param values: a dictionary formatted like: {month: list of votes}
    :returns: dictionary every person for every month
    """
    all_persons = set([person.lower().replace(" ", "") for element in values.values() for persons in element for person in persons.split("|")])

    out = {}
    for month in values:
        values_now = [element.lower().replace(" ", "") for element in values[month]]
        if month not in out:
            out[month] = {}

        for person in all_persons:
            out[month][person] = values_now.count(person)

    return out


def plot_3d(values: list) -> None:
    # Plotting
    # Data for three-dimensional scattered points
    ax = plt.axes(projection='3d')
    z_data = np.array(list(av_streak_per_person(values).values()))
    x_data = np.array(list(av_votes_per_person(values).values()))
    y_data = np.array(list(av_shares_per_person(values).values()))

    ax.scatter3D(x_data, y_data, z_data, c=z_data, cmap="Accent", depthshade=False, alpha=1)

    ax.set_xlabel("votes per person")
    ax.set_ylabel("shares per person")
    ax.set_zlabel("streak per person")

    print("\n".join([x_data.__str__(), y_data.__str__(), z_data.__str__()]))

    plt.show()


def plot_2d(x: list, y: Iterable | dict, x_label: str | None = ..., y_label: str | None = ..., x_ticks: int | None = ..., y_ticks: int | None = ...) -> None:
    if type(y) == dict:
        all_persons = set(
            [person.lower().replace(" ", "") for element in y.values() for persons in element for person in
             persons.split("|")])

        df = {person: [y[month][person] for month in y] for person in all_persons}

        df.update({"Dates": [i for i in range(len(x))]})
        df = pd.DataFrame(df)

        g = sns.lmplot('Dates', 'value', data=pd.melt(df, ['Dates']), hue='variable', ci=None, order=5, truncate=True)
        g.set_xticklabels([""]+x+[""])
        g.set(ylabel="Votes per month")

    else:
        plt.plot(x, y)

    if x_label is not ...:
        plt.xlabel(x_label)
    if y_label is not ...:
        plt.ylabel(y_label)

    if x_ticks is not ...:
        plt.xticks(x_ticks)
    if y_ticks is not ...:
        plt.yticks(y_ticks)

    plt.show()


def main() -> None:
    """
    main Function
    """
    with backend.Connection(host="server.fridrich.xyz") as c:
        c.auth("StatsBot", "IGetDaStats")

        log = c.get_log()["GayKing"]

    months = {}
    for element, kings in log.items():
        date = ".".join(element.split(".")[1::])
        if date not in months:
            months[date] = []
        months[date].append(kings)

    per_month = votes_per_month(months)

    plot_2d(list(months), per_month)
    # plot_3d(list(log.values()))


if __name__ == "__main__":
    main()
