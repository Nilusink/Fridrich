from typing import Dict, List, Tuple, Iterable
import matplotlib.pyplot as plt
from fridrich import backend
from fridrich import *
import tkinter as tk
import numpy as np
import json


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
    all_persons = all_persons = set([person.lower().replace(" ", "") for element in values.values() for persons in element for person in persons.split("|")])

    out = {}
    for month in values:
        values_now = [element.lower().replace(" ", "") for element in values[month]]
        if month not in out:
            out[month] = {}

        for person in all_persons:
            out[month][person] = values_now.count(person)

    return out


def per_month(values: Dict[str, List[str] | Tuple[str]]):
    0


def plot_3d(values: list) -> None:
    # Plotting
    # Data for three-dimensional scattered points
    ax = plt.axes(projection='3d')
    zdata = np.array(list(av_streak_per_person(values).values()))
    xdata = np.array(list(av_votes_per_person(values).values()))
    ydata = np.array(list(av_shares_per_person(values).values()))

    ax.scatter3D(xdata, ydata, zdata, c=zdata, cmap="Accent", depthshade=False, alpha=1)

    ax.set_xlabel("votes per person")
    ax.set_ylabel("shares per person")
    ax.set_zlabel("streak per person")

    print("\n".join([xdata.__str__(), ydata.__str__(), zdata.__str__()]))

    plt.show()


def plot_2d(x: Iterable, y: Iterable | dict, x_label: str | None = ..., y_label: str | None = ..., x_ticks: int | None = ..., y_ticks: int | None = ...) -> None:
    if type(y) == dict:
        all_persons = set(
            [person.lower().replace(" ", "") for element in y.values() for persons in element for person in
             persons.split("|")])

        for person in all_persons:
            plt.plot(x, [y[month][person] for month in y], label=person)

        plt.legend()

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
    # c = backend.Connection(host="192.168.10.15")
    # c.auth("Hurensohn3", "13102502")

    # log = c.get_log()
    # c.end()
    log = {'00.00.0000': 'jesus', '30.05.2021': 'Lukas', '31.05.2021': 'Melvin|Lukas|Niclas', '01.06.2021': 'Niclas', '02.06.2021': 'Melvin', '07.06.2021': 'Niclas', '08.06.2021': 'Niclas', '09.06.2021': 'Melvin', '10.06.2021': 'Melvin|Pedo|Socken Typ', '11.06.2021': 'Melvin', '12.06.2021': 'Menschheit', '14.06.2021': 'Melvin', '15.06.2021': 'Tisch|Melvin|Golden Gay Bridge', '16.06.2021': 'Josef|Melvin|Golden Gay Bridge', '17.06.2021': 'Grif|Melvin', '18.06.2021': 'Grif', '21.06.2021': 'busfahrer', '22.06.2021': 'Busfahrer', '23.06.2021': 'Busfahrer', '24.06.2021': 'Melvin|Busfahrer', '25.06.2021': 'Busfahrer', '26.06.2021': 'Busfahrer|Lukas', '28.06.2021': 'Busfahrer', '29.06.2021': 'busfahrer|Melvin', '30.06.2021': 'Busfahrer', '01.07.2021': 'Busfahrer|Jesus|SockenTyp', '02.07.2021': 'Busfahrer|Melvin', '03.07.2021': 'Melvin|Busfahrer', '05.07.2021': 'Melvin|Busfahrer', '06.07.2021': 'Busfahrer', '07.07.2021': 'Busfahrer|Lukas', '08.07.2021': 'Lukas', '09.07.2021': 'Melvin', '14.09.2021': 'Niclas|Melvin', '15.09.2021': 'Melvin', '16.09.2021': 'Lukas|Busfahrer', '17.09.2021': 'Juden', '21.09.2021': 'Juden', '22.09.2021': 'Niclas|Juden', '23.09.2021': 'Melvin|Juden', '24.09.2021': 'Juden', '27.09.2021': 'Juden', '28.09.2021': 'Juden', '29.09.2021': 'Juden|Melvin', '30.09.2021': 'Juden|Melvin', '01.10.2021': 'Juden|Lukas|Melvin', '04.10.2021': 'Juden', '05.10.2021': 'Juden|Melvin', '06.10.2021': 'Juden', '07.10.2021': 'Juden|Melvin', '08.10.2021': 'Juden|Melvin', '11.10.2021': 'Juden|Lukas', '12.10.2021': 'Juden', '13.10.2021': 'Juden', '14.10.2021': 'Juden|Melvin', '15.10.2021': 'Juden', '18.10.2021': 'Juden', '19.10.2021': 'Juden', '20.10.2021': 'Juden', '21.10.2021': 'Juden|Lukas', '22.10.2021': 'Juden', '03.11.2021': 'Juden', '05.11.2021': 'Juden', '08.11.2021': 'Juden', '10.11.2021': 'Juden|Melvin', '11.11.2021': 'Juden|Melvin', '16.11.2021': 'Juden', '17.11.2021': 'Juden', '18.11.2021': 'Juden'}

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
