"""
A Discord Bot integration for fridrich
Notice: you must replace VOTINGS_CHANNEL_ID with
the correct ID for your channel on your Server

Author: Nilusink
"""
from fridrich.cryption_tools import Low
from fridrich.backend import Connection
from fridrich.classes import Daytime
from fridrich import Error

from contextlib import suppress, contextmanager
from discord.ext import commands, tasks
from traceback import print_exc
from typing import Any, Dict
from time import sleep
import binascii
import discord

TOKEN = Low.decrypt('|Nb`sE&w(FH~=vKF#t3GH2^mNGypdMH~=;PH~=;PFaS6J |Nb}tE&wn9 |Nb`sE&wtBH~=sJF#s?CIRH2SH~={SG5|OLFaR|GF#tFK |Nb!mFaRz9FaR_FIRH2SHvlyNHUKgJF#s_DG5|0DH~={S |Nb`sE&w(FH~=vKF#t3GH2^mNGypdMH~=;PH~=;PFaS6J |Nb@rE&w?IG5|OLG5|0DGXOFGGXO9EG5|LKH2^gLFaS9K |Nb`sE&wtBH~=sJF#s?CIRH2SH~={SG5|OLFaR|GF#tFK |Nc1uE&w?IGypjOH~=>QGypRIHvlmJFaS0HHUKgJ |Nb`sE&w(FH~=vKF#t3GH2^mNGypdMH~=;PH~=;PFaS6J |Nb}tE&wn9 |Nb`sE&w$EGypjOH~=#MGypUJGXOOJG5|LKFaS3IH2? |Nb!mFaRz9FaR_FIRH2SHvlyNHUKgJF#s_DG5|0DH~={S |Nb`sE&w$EGypjOH~=#MGypUJGXOOJG5|LKFaS3IH2? |Nb@rE&w?IG5|OLG5|0DGXOFGGXO9EG5|LKH2^gLFaS9K |Nb`sE&wn9 |Nc1uE&w?IGypjOH~=>QGypRIHvlmJFaS0HHUKgJ |Nb`sE&w$EGypjOH~=#MGypUJGXOOJG5|LKFaS3IH2? |Nb}tE&wn9 |Nb`sE&wn9 |Nb=qE&wwCH~=*OF#t9IGypgNFaS3IF#t0FGypXKFaR_F |Nb`sE&w$EGypjOH~=#MGypUJGXOOJG5|LKFaS3IH2? |Nb@rE&w?IG5|OLG5|0DGXOFGGXO9EG5|LKH2^gLFaS9K |Nc1uE&wqAF#s?CGypRIGXOOJHvl;RF#t3GGypRI |Nb!mFaRz9FaS9KIRG^PFaR_FIRG;NH~=#MHUKgJFaS3IHvj |Nb=qE&wn9IRH5TFaR+CIRG^PF#t0FH2^sPG5|LKH~=&NH2? |Nb}tE&wwCFaS0HHUKgJGXOXMHUKgJIRG&LH~=sJHvlyN |Nb}tE&w<HH~=^RF#tILGypUJF#tCJGXOCFH2^gLH~={S |Nb`sE&wtBF#s_DF#s?CG5|FIH2^RGIRG*MHvl;RHvl*Q |Nb@rE&w+GH~=yLGXOFGIRH5TH~=#MF#s|EH2^XIHUKyP |Nb@rE&wn9H~=yLHvl#OG5|FIGXO9EG5|RMH~=yLF#tIL |Nc1uE&w?IGypjOH~=>QGypRIHvlmJFaS0HHUKgJ |Nb=qE&wn9IRH5TFaR+CIRG^PF#t0FH2^sPG5|LKH~=&NH2? |Nb}tE&wqAG5|CHFaR?EH~=&NFaR_FHUKjKH2^sPHUI |Nb@rE&w<HH2^gLHUKpMGypaLFaR(BGypIFF#s?CGypUJ |Nb@rE&w+GH~=yLGXOFGIRH5TH~=#MF#s|EH2^XIHUKyP |Nb`sE&wqAGypLGGypOHH~=&NG5|OLH2^dKG5|OLH2? |Nb`sE&wzDF#t9IF#tILH~=&NH~=>QFaS9KH2^jMHUKjK |Nc1uE&wn9 |Nc1uE&w(FIRG^PGXOOJIRG~RF#t3GH~=#MG5|IJH2^sP |Nc1uE&w<HIRH5TGypjOGypjOGXORKHUKdIF#t9IHUKpM |Nb@rE&w?IG5|OLG5|0DGXOFGGXO9EG5|LKH2^gLFaS9K |Nb`sE&wtBF#s_DF#s?CG5|FIH2^RGIRG*MHvl;RHvl*Q |Nb=qE&wtBIRG&LH2^RGG5|IJG5|6FF#s|EIRG&LH~=vK |Nc1uE&wzDH~=;PH~=#MG5|RMH~=sJH2^RGH2^UHGXOXM |Nb`sE&wzDF#t9IF#tILH~=&NH~=>QFaS9KH2^jMHUKjK |Nc1uE&w(FIRG^PGXOOJIRG~RF#t3GH~=#MG5|IJH2^sP |Nb`sE&w?IGXOULG5|FIGXOaNGXOIHF#tILGXOULHvlpK |Nb=qE&w<HGXO9EIRG^PF#tFKIRG>OH~=&NH2^aJFaR+C |Nb`sE&wzDH~=#MGXOCFGypdMHvlsLH2^dKHvl*QH~=#M |Nb=qE&w$EHUKvOHvl#OGypRIHUKgJH~=#MFaR(BG5|3EH2? |Nb`sE&wn9HvlmJFaS0HHvl*QF#s_DH~=;PH2^dKHvlyNH2? |Nb`sE&w(FH~=vKF#t3GH2^mNGypdMH~=;PH~=;PFaS6J |Nc1uE&w<HGypgNH~=*OHvl*QFaR+CHvl;RHUKdIFaR_F |Nb@rE&wn9 |Nb=qE&w?IF#t9IFaS3IIRG~RH~=#MFaS9KIRG{QF#t9I |Nc1uE&w$EIRG&LHUKsNGXO9EGypaLHUKgJH2^dKGXOXM |Nc1uE&wwCG5|LKGXOULIRG#KH2^aJFaS6JH~=^RF#t9I |Nb}tE&wtBGypaLG5|3EF#s|EH2^UHG5|9GH2^aJG5|3E |Nb=qE&wtBIRG&LH2^RGG5|IJG5|6FF#s|EIRG&LH~=vK ')

VOTINGS_CHANNEL_ID = 922820312968605806
VOTINGS_CHANNEL: Any = None

bot = commands.Bot(command_prefix='!')
stats_c = Connection(host="127.0.0.1")

command_warning_interval = Daytime(minute=10)  # interval of 10 minutes
last_command_warning = Daytime.now() - command_warning_interval

LOGGED_IN_USERS: Dict[str, Connection] = {}
USER_TIMEOUT = Daytime(minute=2)


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
    check if the channel is dm
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


# general commands
@bot.command(name='status', help="get the state of the current voting")
async def status(ctx, flag: str = "now") -> None:
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
                    p_format = "    - " + "\n    - ".join([f"{guy}: {res[voting]['results'][guy]}" for guy in res[voting]["results"] if res[voting]["results"][guy] > 0])
                    out += f"\n{voting}:\n{p_format}\n"

            await ctx.send(out+"\n")
            return

        await ctx.send("No votes yet!")


@bot.command(name='log', help="get the current log")
async def log(ctx) -> None:
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
                    p_format = "    - " + "\n    - ".join([f"{day}: {now_log[voting][day]}" for day in list(now_log[voting].keys())[:-11:-1]])
                    out += f"\n{voting}:\n{p_format}\n"

            await ctx.send(out+"\n")
            return

        await ctx.send("No log yet!")


@bot.command(name="streak", help="get the current streaks")
async def streak(ctx) -> None:
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


@bot.command(name="time", help="get the current server time")
async def g_time(ctx) -> None:
    """
    get an overview of the server and the votings
    """
    with print_traceback():
        if not await check_if_channel(ctx):
            return

        n_time = stats_c.get_server_time()
        out = f"♦ SERVER TIME ♦\n    - now: {n_time['now']}\n    - voting in: {n_time['until_voting']}"
        await ctx.send(out)


# user specific commands
@bot.command(name="login", help="login to your account (dm only)")
async def login(ctx, username: str = ..., password: str = ...) -> None:
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
                await ctx.send("You haven't logged in since the last server reboot, please provide username and password")
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


@bot.command(name="logout", help="logout (if logged in)")
async def logout(ctx) -> None:
    """
    logout
    """
    with print_traceback():
        if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
            return

        LOGGED_IN_USERS[ctx.author].end(revive=True)
        await ctx.send("Logged out")


@bot.command(name="vote", help="send a vote to the fridrich server (only when logged in)")
async def send_vote(ctx, vote: str, voting: str = "GayKing") -> None:
    """
    send a vote to the server
    """
    with print_traceback():
        if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
            return

        LOGGED_IN_USERS[ctx.author].send_vote(vote, voting=voting, flag="vote")
        await ctx.send("Vote registered")


@bot.command(name="unvote", help="reset your vote (only when logged in)")
async def unvote(ctx, voting: str = "GayKing") -> None:
    with print_traceback():
        if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
            return

        LOGGED_IN_USERS[ctx.author].send_vote(voting=voting, flag="unvote")
        await ctx.send("Deleted vote")


@bot.command(name="users", help="get all currently logged in users (only when logged in)")
async def users(ctx) -> None:
    with print_traceback():
        if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
            return

        all_users = LOGGED_IN_USERS[ctx.author].get_online_users()
        out = "Logged in users:\n:white_medium_small_square: " + "\n:white_medium_small_square: ".join(all_users)

        await ctx.send(out)


@bot.command(name="weather", help="request all data from all weather stations")
async def weather(ctx) -> None:
    with print_traceback():
        if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
            return

        u_c = LOGGED_IN_USERS[ctx.author]

        now_d = u_c.get_temps_now()

        out = "♦ WEATHER ♦"
        for station in now_d:
            out += f"\n:white_medium_small_square: {station} ({now_d[station]['time']}):\n    - " + "\n    - ".join([datapoint + ": " + str(now_d[station][datapoint]) for datapoint in ["temp", "hum", "press"]])
            out += "\n"

        await ctx.send(out)


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

        if message.channel == VOTINGS_CHANNEL and not message.content.startswith("!") and not message.author == bot.user:
            with suppress(discord.errors.Forbidden):
                await message.delete()

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error) -> None:
    """
    run if there was an error running an command
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
        # data for each loop
        left = stats_c.get_server_time()["until_voting"]

        # 00:00 switch
        if left < Daytime(second=2):
            sleep(2)
            res = stats_c.get_log()
            mes = f"♦ Voting results ♦"
            for voting in res:
                dat = res[voting][list(res[voting])[-1]]
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

            # start loops
            # check_login_time.start()  # kinda messes everything up
            looper.start()

            # run bot
            bot.run(TOKEN)

    finally:
        for element in LOGGED_IN_USERS:
            LOGGED_IN_USERS[element].end()
        print(f"Bot stopped at {str(Daytime.now())}\n")
