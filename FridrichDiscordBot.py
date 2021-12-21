"""
A Discord Bot integration for fridrich
Notice: you must replace VOTINGS_CHANNEL_ID with
the correct ID for your channel on your Server

Author: Nilusink
"""
from fridrich.backend import Connection
from fridrich.classes import Daytime
from traceback import format_exc

from discord.ext import commands
from typing import Any

TOKEN = "OTIyODIwOTMyMDEwMTE1MDgz.YcHB9w.n8X_Cxe7dAH7xnB1tRYrErZQ5CM"

VOTINGS_CHANNEL_ID = 922820312968605806
VOTINGS_CHANNEL: Any = None

bot = commands.Bot(command_prefix='!')
stats_c = Connection(host="127.0.0.1")

command_warning_interval = Daytime(minute=10)  # interval of 10 minutes
last_command_warning = Daytime.now() - command_warning_interval


async def check_if_channel(ctx) -> bool:
    """
    check if the correct channel is selected
    """
    global VOTINGS_CHANNEL, last_command_warning
    await bot.wait_until_ready()

    if VOTINGS_CHANNEL is None:
        VOTINGS_CHANNEL = bot.get_channel(VOTINGS_CHANNEL_ID)

    if ctx.channel != VOTINGS_CHANNEL:
        await ctx.message.delete()
        if Daytime.now() - last_command_warning > command_warning_interval:
            last_command_warning = Daytime.now()
            await ctx.send("You can only use commands in the \"Votings\" Channel")
        return False
    return True


@bot.command(name='status', help="get the state of the current voting")
async def status(ctx, flag: str = "now") -> None:
    if not await check_if_channel(ctx):
        return

    if flag not in ("now", "last"):
        await VOTINGS_CHANNEL.send(f"Second argument \"flag\" must be \"last\" or \"now\"")
        return

    try:
        res = stats_c.get_results(flag=flag)
    except:
        await ctx.send(format_exc())
        return

    if res:
        out = "♦ VOTING STATUS ♦"
        for voting in res:
            p_format = "    - " + "\n    - ".join([f"{guy}: {res[voting]['results'][guy]}" for guy in res[voting]["results"] if res[voting]["results"][guy] > 0])
            out += f"\n{voting}:\n{p_format}\n"

        await VOTINGS_CHANNEL.send(out+"\n")
        return

    await VOTINGS_CHANNEL.send("No votes yet!")


@bot.command(name='log', help="get the current log")
async def log(ctx) -> None:
    if not await check_if_channel(ctx):
        return

    now_log = stats_c.get_log()
    if now_log:
        out = "♦ LOG ♦"
        for voting in now_log:
            if now_log[voting]:
                p_format = "    - " + "\n    - ".join([f"{day}: {now_log[voting][day]}" for day in list(now_log[voting].keys())[:-11:-1]])
                out += f"\n{voting}:\n{p_format}\n"

        await VOTINGS_CHANNEL.send(out+"\n")
        return

    await VOTINGS_CHANNEL.send("No log yet!")


@bot.command(name="streak", help="get the current streaks")
async def streak(ctx) -> None:
    if not await check_if_channel(ctx):
        return

    now_log = stats_c.get_log()
    if now_log:
        out = "♦ Streaks ♦"
        for voting in now_log:
            if now_log[voting]:
                tmp = stats_c.calculate_streak(now_log[voting])
                out += f"\n{voting}:\n    - {tmp[0]}, {tmp[1]}\n"

        await VOTINGS_CHANNEL.send(out)
        return

    await VOTINGS_CHANNEL.send("No log yet!")

if __name__ == '__main__':
    with stats_c as c:
        while not c:
            try:
                c.auth("StatsBot", "IGetDaStats")
            except ConnectionError:
                continue
        print("Bot started")
        bot.run(TOKEN)
