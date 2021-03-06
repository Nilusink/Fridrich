"""
A Discord Bot integration for fridrich
Notice: you must replace VOTINGS_CHANNEL_ID with
the correct ID for your channel on your Server

Author: Nilusink
"""
from fridrich.backend import Connection
from fridrich.classes import Daytime
from fridrich.errors import Error

from contextlib import suppress, contextmanager
from scipy.ndimage import gaussian_filter1d
from discord.ext import commands, tasks
from traceback import print_exc
import matplotlib.pyplot as plt
from scipy import interpolate
import pandas as pd
import typing as tp
import numpy as np
import binascii
import discord
import asyncio
import json
import os

try:
    with open(os.getcwd()+"/config/discord_bot.json", "r") as inp:
        config = json.load(inp)
        # get discord bot info
        TOKEN: str = config["token"]
        VOTINGS_CHANNEL_ID: int = config["channel_id"]

        # get fridrich bot info
        USERNAME: str = config["fridrich_user"]
        PASSWORD: str = config["fridrich_pwd"]

except KeyError:
    raise KeyError("the discord_bot config file doesn't contain the correct values!")


VOTINGS_CHANNEL: tp.Any = None

bot = commands.Bot(command_prefix='!')
stats_c = Connection(host="127.0.0.1")

command_warning_interval = Daytime(minute=10)  # interval of 10 minutes
last_command_warning = Daytime.now() - command_warning_interval

LOGGED_IN_USERS: tp.Dict[str, Connection] = {}
USER_TIMEOUT = Daytime(minute=2)

DATA_DESCRIPTION: tp.Dict[str, str] = {    # label for the plot, mustn't be changed
    "Temperature": "Temperature in °C",
    "hum": "Humidity in %",
    "Humidity": "Humidity in %",
    "press": "Pressure in hPa",
    "Pressure": "Pressure in hPa",
    "Temperature Index": "Felt temperature in °C"
}


@contextmanager
def print_traceback():
    """
    discord won't always give you the error messages, so we catch them here
    """
    try:
        yield

    except Exception as e:
        print_exc()
        raise Error(e)


def get_all_weather_data(data_point: str, values_start: int) -> tuple[list, dict[str, dict]]:

    stations = c.get_weather_stations()

    temp_graphs: tp.Dict[str, tp.Dict[str, float | None]] = {}
    for station in stations:
        temp_graphs[station["station_name"]]: dict = {}

        # append all log-times to the list
        station_log = c.get_temps_log(station["station_name"])
        for date in station_log:
            # remove second from date
            short_date = ":".join(date.split(":")[:-1])

            # append data for date
            if type(data_point) == tuple:
                for point in data_point:
                    if point in station_log[date]:
                        temp_graphs[station["station_name"]][short_date] = station_log[date][point]
                        break
                else:
                    temp_graphs[station["station_name"]][short_date] = None

                continue

            if data_point in station_log[date]:
                temp_graphs[station["station_name"]][short_date] = station_log[date][data_point]

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
    all_dates: list = sorted(list(all_dates))[values_start:]

    new_data = {}
    for station in temp_graphs:
        new_data[station]: dict = {}
        cnt = 0
        for date in all_dates:
            now = temp_graphs[station][date]
            new_data[station][date] = now
            cnt += now if now is not None else 0

        # remove all stations that don't actually have data for this period
        if cnt == 0:
            new_data.pop(station)

    return all_dates, new_data


def make_graph(values: int, outfile: str, data_point) -> None:
    all_dates, new_data = get_all_weather_data(data_point, -values)

    data = {"dates": all_dates}

    data.update({
        station: gaussian_filter1d(new_data[station]) for station in new_data
    })

    all_points = [value for values in data.values() for value in values if type(value) in (int, float)]
    if len(all_points) == 0:
        raise ValueError("No points for selected range")

    plt.figure(figsize=(16, 8))
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
                    if value is not None:
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
    # g = sns.lineplot(x="dates", y="value", hue="variable", data=pd.melt(data, ["dates"]), ci=None)

    # configure graph
    p = data_point[0] if type(data_point) == tuple else data_point

    labels = 8
    # x and y ticks
    # calculate the step for the y-axis
    all_values = [value for station in new_data for value in new_data[station].values() if value is not None]
    lower_limit = int(min(all_values)-1)
    upper_limit = int(max(all_values)+1)

    v_n = len(all_dates) // labels
    v_n = v_n if v_n != 0 else len(all_dates)
    plt.xticks(range(0, len(all_dates), v_n),
               [all_dates[i] for i in range(0, len(all_dates), v_n)])

    potential_steps = (.1, .2, .5, 1, 2, 5, 10)
    max_values = 40
    step: float = .1
    for step in potential_steps:
        if (upper_limit-lower_limit) / step < max_values:
            break

    plt.yticks(np.arange(lower_limit, upper_limit, step))
    plt.legend(title="Weather Stations")
    plt.grid()

    plt.legend(title="Weather Station")
    plt.grid()

    # save graph
    plt.savefig(outfile)
    plt.clf()


async def check_if_channel(ctx) -> bool:
    """
    check if the correct channel is selected
    """
    global VOTINGS_CHANNEL, last_command_warning
    await bot.wait_until_ready()

    if VOTINGS_CHANNEL is None:
        VOTINGS_CHANNEL = bot.get_channel(VOTINGS_CHANNEL_ID)

    if ctx.channel != VOTINGS_CHANNEL:
        try:
            await ctx.message.delete()

        except discord.errors.Forbidden:  # when it is a dm
            if isinstance(ctx.channel, discord.channel.DMChannel):
                return True
            return False

        if Daytime.now() - last_command_warning > command_warning_interval:
            last_command_warning = Daytime.now()
            await ctx.send("You can only use commands in the \"Votings\" Channel")
        return False
    return True


async def check_if_dm(ctx) -> bool:
    """
    check if the channel is dm channel
    """
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        with suppress(discord.errors.Forbidden):
            await ctx.message.delete()
        await ctx.author.send("this function can only be used via private dm to me")
        return False
    return True


async def check_if_logged_in(ctx) -> bool:
    """
    check if the user is logged in
    """
    if ctx.author not in LOGGED_IN_USERS:
        await ctx.author.send("Not logged in")
        return False

    if not not LOGGED_IN_USERS[ctx.author]:
        if not LOGGED_IN_USERS[ctx.author].re_auth():
            ctx.author.send("Not logged in")
            return False
    return True


class General(commands.Cog):
    def __init__(self, bot_instance) -> None:
        self.bot = bot_instance

    @commands.command(name='status', help="get the state of the current voting")
    async def status(self, ctx, flag: str = "now") -> None:
        """
        basically get_results
        """
        with print_traceback():
            if not await check_if_channel(ctx):
                return

            if flag not in ("now", "last"):
                await ctx.send(f"Second argument \"flag\" must be \"last\" or \"now\"")
                return

            res = stats_c.get_results(flag=flag)

            if res:
                out = "♦ VOTING STATUS ♦"
                for voting in res:
                    if res[voting]["totalVotes"]:
                        p_format = "    - " + "\n    - ".join(
                            [f"{guy}: {res[voting]['results'][guy]}"
                             for guy in res[voting]["results"] if res[voting]["results"][guy] > 0])
                        out += f"\n{voting}:\n{p_format}\n"

                await ctx.send(out+"\n")
                return

            await ctx.send("No votes yet!")

    @commands.command(name='log', help="get the current log")
    async def log(self, ctx) -> None:
        """
        get the current log
        """
        with print_traceback():
            if not await check_if_channel(ctx):
                return

            now_log = stats_c.get_log()
            if now_log:
                out = "♦ LOG ♦"
                for voting in now_log:
                    if now_log[voting]:
                        p_format = "    - " + "\n    - ".join([f"{day}: {now_log[voting][day]}"
                                                               for day in list(now_log[voting].keys())[:-11:-1]])
                        out += f"\n{voting}:\n{p_format}\n"

                await ctx.send(out+"\n")
                return

            await ctx.send("No log yet!")

    @commands.command(name="streak", help="get the current streaks")
    async def streak(self, ctx) -> None:
        """
        get the current streaks
        """
        with print_traceback():
            if not await check_if_channel(ctx):
                return

            now_log = stats_c.get_log()
            if now_log:
                out = "♦ STREAKS ♦"
                for voting in now_log:
                    if now_log[voting]:
                        tmp = stats_c.calculate_streak(now_log[voting])
                        out += f"\n{voting}:\n    - {tmp[0]}, {tmp[1]}\n"

                await ctx.send(out)
                return

            await ctx.send("No log yet!")

    @commands.command(name="time", help="get the current server time")
    async def g_time(self, ctx) -> None:
        """
        get an overview of the server and the votings
        """
        with print_traceback():
            if not await check_if_channel(ctx):
                return

            n_time = stats_c.get_server_time()
            out = f"♦ SERVER TIME ♦\n    - now: {n_time['now']}\n    - voting in: {n_time['until_voting']}"
            await ctx.send(out)


class Voting(commands.Cog):
    def __init__(self, bot_instance) -> None:
        self.bot = bot_instance

    @commands.command(name="login", help="login to your account (dm only)")
    async def login(self, ctx, username: str = ..., password: str = ...) -> None:
        """
        login
        """
        with print_traceback():
            if not await check_if_dm(ctx):
                return

            with suppress(discord.errors.Forbidden):
                await ctx.message.delete()

            if username is ... or password is ...:
                if ctx.author not in LOGGED_IN_USERS:
                    await ctx.send("You haven't logged in since the last server reboot,"
                                   "please provide username and password")
                    return

                if LOGGED_IN_USERS[ctx.author].re_auth():
                    await ctx.send("Login successful")
                    return

                await ctx.send("Invalid credentials, session ended")
                LOGGED_IN_USERS[ctx.author].end()
                del LOGGED_IN_USERS[ctx.author]
                return

            tmp = Connection(host=stats_c.server_ip)
            if tmp.auth(username, password):
                LOGGED_IN_USERS[ctx.author] = tmp
                await ctx.send("Login successful")
                return

            tmp.end()
            await ctx.send("Login failed")

    @commands.command(name="logout", help="logout (if logged in)")
    async def logout(self, ctx) -> None:
        """
        logout
        """
        with print_traceback():
            if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
                return

            LOGGED_IN_USERS[ctx.author].end(revive=True)
            await ctx.send("Logged out")

    @commands.command(name="vote", help="send a vote to the fridrich server (only when logged in)")
    async def send_vote(self, ctx, vote: str, voting: str = "GayKing") -> None:
        """
        send a vote to the server
        """
        with print_traceback():
            if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
                return

            LOGGED_IN_USERS[ctx.author].send_vote(vote, voting=voting, flag="vote")
            await ctx.send("Vote registered")

    @commands.command(name="unvote", help="reset your vote (only when logged in)")
    async def unvote(self, ctx, voting: str = "GayKing") -> None:
        with print_traceback():
            if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
                return

            LOGGED_IN_USERS[ctx.author].send_vote(voting=voting, flag="unvote")
            await ctx.send("Deleted vote")

    @commands.command(name="users", help="get all currently logged in users (only when logged in)")
    async def users(self, ctx) -> None:
        with print_traceback():
            if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
                return

            all_users = LOGGED_IN_USERS[ctx.author].get_online_users()
            out = "Logged in users:\n:white_medium_small_square: " + "\n:white_medium_small_square: ".join(all_users)

            await ctx.send(out)


class WeatherStations(commands.Cog):
    def __init__(self, bot_instance) -> None:
        self.bot = bot_instance

    @commands.group(name="weather", help="handler for all weather data")
    async def weather(self, ctx) -> None:
        if ctx.message.content == "!weather":
            await self.now(ctx)

    @weather.command(name="now", help="request current data from all weather stations")
    async def now(self, ctx) -> None:
        with print_traceback():
            now_d = stats_c.get_temps_now()
            out = "♦ WEATHER ♦"
            for station in now_d:
                out += f"\n:white_medium_small_square: {station} ({now_d[station]['time']}):\n"
                now_d[station].pop("time")
                for value in now_d[station]:
                    out += f"    - {value}: {now_d[station][value]}\n"

            await ctx.send(out)

    @weather.command(name="graph", help="create a graph from the [values]s last measurements"
                                        "(default is 288 because every 5 minutes is a measurement * 288 = 1 day")
    async def graph(self, ctx, values: int = 288, data_point: str = "Temperature") -> None:
        with print_traceback():
            await ctx.send("creating graph...")

            try:
                make_graph(values, "tmp.png", data_point)

            except ValueError:
                await ctx.send("Cannot make graph: no data points for selected arguments")
                return

            await ctx.send(file=discord.File("tmp.png"))

            # wait for a little and then remove the file
            await asyncio.sleep(1)
            os.remove("tmp.png")

    @weather.command(name="daily", help="make a graph based on the daily average")
    async def daily(self, ctx, data_point: str = "Temperature"):
        ...


@bot.event
async def on_message(message):
    """
    if the message sent isn't a command or sent by the bot, delete it
    """
    with print_traceback():
        global VOTINGS_CHANNEL

        await bot.wait_until_ready()
        if VOTINGS_CHANNEL is None:
            VOTINGS_CHANNEL = bot.get_channel(VOTINGS_CHANNEL_ID)

        if message.channel == VOTINGS_CHANNEL and not message.content.startswith("!")\
                and not message.author == bot.user:
            with suppress(discord.errors.Forbidden):
                await message.delete()

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error) -> None:
    """
    run if there was an error running a command
    """
    with print_traceback():
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.send('You do not have the correct role for this command.')

        elif isinstance(error, commands.errors.CommandNotFound):
            await ctx.send(f"Invalid command \"{ctx.message.content.split(' ')[0]}\" (not found)")


@bot.event
async def on_member_join(member):
    with print_traceback():
        await member.create_dm()
        await member.dm_channel.send(
            f'Hello {member.name}, go fuck yourself!\nTo get an overview of all the commands, text me "!help" !'
        )


@tasks.loop(seconds=30)
async def check_login_time():
    """
    repeated every 30 seconds
    checks if a user has been logged in for longer than "USER_TIMEOUT"
    then logs them out
    """
    with print_traceback():
        for user in LOGGED_IN_USERS:
            if LOGGED_IN_USERS[user] and LOGGED_IN_USERS[user].login_time > USER_TIMEOUT:
                print(f"user timed out: {user}")
                LOGGED_IN_USERS[user].end(revive=True)


@tasks.loop(seconds=1)
async def looper() -> None:
    """
    function for checking all kinds of stuff in a loop
    """
    with suppress(binascii.Error):
        if not stats_c:
            try:
                stats_c.re_auth()
            except (Exception,):
                return

        # data for each loop
        left = stats_c.get_server_time()["until_voting"]

        # 00:00 switch
        if left < Daytime(second=2):
            await asyncio.sleep(2)
            # send both requests at one time
            log = stats_c.get_log(wait=True)
            res = stats_c.get_results(flag="last", wait=True)
            if not res:
                channel = bot.get_channel(VOTINGS_CHANNEL_ID)
                await channel.send("No votes for yesterday!")
                return

            stats_c.send()

            # get results
            log, res = log.result(), res.result()

            mes = f"♦ Voting results ♦"
            for voting in log:
                # only append the voting if there was a vote
                if res[voting]["totalvotes"] > 0:
                    dat = log[voting][list(log[voting])[-1]]
                    mes += f"\n{voting}: {dat}"

            channel = bot.get_channel(VOTINGS_CHANNEL_ID)
            await channel.send(mes)

if __name__ == '__main__':
    try:
        with stats_c as c:
            while not c:
                try:
                    c.auth("StatsBot", "IGetDaStats")

                except ConnectionError:
                    continue
            print(f"Bot started at {str(Daytime.now())}")

            bot.add_cog(General(bot))
            bot.add_cog(Voting(bot))
            bot.add_cog(WeatherStations(bot))

            looper.start()

            # run bot
            bot.run(TOKEN)

    finally:
        for element in LOGGED_IN_USERS:
            LOGGED_IN_USERS[element].end()
        print(f"Bot stopped at {str(Daytime.now())}\n")
