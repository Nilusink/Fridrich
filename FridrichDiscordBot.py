"""
A Discord Bot integration for fridrich
Notice: you must replace VOTINGS_CHANNEL_ID with
the correct ID for your channel on your Server

Author: Nilusink
"""
from fridrich.cryption_tools import Low
from fridrich.backend import Connection
from fridrich.classes import Daytime
import discord

from discord.ext import commands, tasks
from contextlib import suppress
from typing import Any, Dict

TOKEN = Low.decrypt('|Nb`sE&w(FH~=vKF#t3GH2^mNGypdMH~=;PH~=;PFaS6J |Nb}tE&wn9 |Nb`sE&wtBH~=sJF#s?CIRH2SH~={SG5|OLFaR|GF#tFK |Nb!mFaRz9FaR_FIRH2SHvlyNHUKgJF#s_DG5|0DH~={S |Nb`sE&w(FH~=vKF#t3GH2^mNGypdMH~=;PH~=;PFaS6J |Nb@rE&w?IG5|OLG5|0DGXOFGGXO9EG5|LKH2^gLFaS9K |Nb`sE&wtBH~=sJF#s?CIRH2SH~={SG5|OLFaR|GF#tFK |Nc1uE&w?IGypjOH~=>QGypRIHvlmJFaS0HHUKgJ |Nb`sE&w(FH~=vKF#t3GH2^mNGypdMH~=;PH~=;PFaS6J |Nb}tE&wn9 |Nb`sE&w$EGypjOH~=#MGypUJGXOOJG5|LKFaS3IH2? |Nb!mFaRz9FaR_FIRH2SHvlyNHUKgJF#s_DG5|0DH~={S |Nb`sE&w$EGypjOH~=#MGypUJGXOOJG5|LKFaS3IH2? |Nb@rE&w?IG5|OLG5|0DGXOFGGXO9EG5|LKH2^gLFaS9K |Nb`sE&wn9 |Nc1uE&w?IGypjOH~=>QGypRIHvlmJFaS0HHUKgJ |Nb`sE&w$EGypjOH~=#MGypUJGXOOJG5|LKFaS3IH2? |Nb}tE&wn9 |Nb`sE&wn9 |Nb=qE&wwCH~=*OF#t9IGypgNFaS3IF#t0FGypXKFaR_F |Nb`sE&w$EGypjOH~=#MGypUJGXOOJG5|LKFaS3IH2? |Nb@rE&w?IG5|OLG5|0DGXOFGGXO9EG5|LKH2^gLFaS9K |Nc1uE&wqAF#s?CGypRIGXOOJHvl;RF#t3GGypRI |Nb!mFaRz9FaS9KIRG^PFaR_FIRG;NH~=#MHUKgJFaS3IHvj |Nb=qE&wn9IRH5TFaR+CIRG^PF#t0FH2^sPG5|LKH~=&NH2? |Nb}tE&wwCFaS0HHUKgJGXOXMHUKgJIRG&LH~=sJHvlyN |Nb}tE&w<HH~=^RF#tILGypUJF#tCJGXOCFH2^gLH~={S |Nb`sE&wtBF#s_DF#s?CG5|FIH2^RGIRG*MHvl;RHvl*Q |Nb@rE&w+GH~=yLGXOFGIRH5TH~=#MF#s|EH2^XIHUKyP |Nb@rE&wn9H~=yLHvl#OG5|FIGXO9EG5|RMH~=yLF#tIL |Nc1uE&w?IGypjOH~=>QGypRIHvlmJFaS0HHUKgJ |Nb=qE&wn9IRH5TFaR+CIRG^PF#t0FH2^sPG5|LKH~=&NH2? |Nb}tE&wqAG5|CHFaR?EH~=&NFaR_FHUKjKH2^sPHUI |Nb@rE&w<HH2^gLHUKpMGypaLFaR(BGypIFF#s?CGypUJ |Nb@rE&w+GH~=yLGXOFGIRH5TH~=#MF#s|EH2^XIHUKyP |Nb`sE&wqAGypLGGypOHH~=&NG5|OLH2^dKG5|OLH2? |Nb`sE&wzDF#t9IF#tILH~=&NH~=>QFaS9KH2^jMHUKjK |Nc1uE&wn9 |Nc1uE&w(FIRG^PGXOOJIRG~RF#t3GH~=#MG5|IJH2^sP |Nc1uE&w<HIRH5TGypjOGypjOGXORKHUKdIF#t9IHUKpM |Nb@rE&w?IG5|OLG5|0DGXOFGGXO9EG5|LKH2^gLFaS9K |Nb`sE&wtBF#s_DF#s?CG5|FIH2^RGIRG*MHvl;RHvl*Q |Nb=qE&wtBIRG&LH2^RGG5|IJG5|6FF#s|EIRG&LH~=vK |Nc1uE&wzDH~=;PH~=#MG5|RMH~=sJH2^RGH2^UHGXOXM |Nb`sE&wzDF#t9IF#tILH~=&NH~=>QFaS9KH2^jMHUKjK |Nc1uE&w(FIRG^PGXOOJIRG~RF#t3GH~=#MG5|IJH2^sP |Nb`sE&w?IGXOULG5|FIGXOaNGXOIHF#tILGXOULHvlpK |Nb=qE&w<HGXO9EIRG^PF#tFKIRG>OH~=&NH2^aJFaR+C |Nb`sE&wzDH~=#MGXOCFGypdMHvlsLH2^dKHvl*QH~=#M |Nb=qE&w$EHUKvOHvl#OGypRIHUKgJH~=#MFaR(BG5|3EH2? |Nb`sE&wn9HvlmJFaS0HHvl*QF#s_DH~=;PH2^dKHvlyNH2? |Nb`sE&w(FH~=vKF#t3GH2^mNGypdMH~=;PH~=;PFaS6J |Nc1uE&w<HGypgNH~=*OHvl*QFaR+CHvl;RHUKdIFaR_F |Nb@rE&wn9 |Nb=qE&w?IF#t9IFaS3IIRG~RH~=#MFaS9KIRG{QF#t9I |Nc1uE&w$EIRG&LHUKsNGXO9EGypaLHUKgJH2^dKGXOXM |Nc1uE&wwCG5|LKGXOULIRG#KH2^aJFaS6JH~=^RF#t9I |Nb}tE&wtBGypaLG5|3EF#s|EH2^UHG5|9GH2^aJG5|3E |Nb=qE&wtBIRG&LH2^RGG5|IJG5|6FF#s|EIRG&LH~=vK ')

VOTINGS_CHANNEL_ID = 922820312968605806
VOTINGS_CHANNEL: Any = None

bot = commands.Bot(command_prefix='!')
stats_c = Connection(host="127.0.0.1")

command_warning_interval = Daytime(minute=10)  # interval of 10 minutes
last_command_warning = Daytime.now() - command_warning_interval

LOGGED_IN_USERS: Dict[str, Connection] = {}
USER_TIMEOUT = Daytime(minute=2)


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
        await ctx.send("you can only login via private dm to me")
        return False
    return True


async def check_if_logged_in(ctx) -> bool:
    """
    check if the user is logged in
    """
    if ctx.author not in LOGGED_IN_USERS:
        await ctx.send("Not logged in")
        return False

    if not not LOGGED_IN_USERS[ctx.author]:
        print(f"re-authing {ctx.author}")
        if not LOGGED_IN_USERS[ctx.author].re_auth():
            return False
    return True


# general commands
@bot.command(name='status', help="get the state of the current voting")
async def status(ctx, flag: str = "now") -> None:
    """
    basically get_results
    """
    if not await check_if_channel(ctx):
        return

    if flag not in ("now", "last"):
        await ctx.send(f"Second argument \"flag\" must be \"last\" or \"now\"")
        return

    res = stats_c.get_results(flag=flag)

    if res:
        out = "♦ VOTING STATUS ♦"
        for voting in res:
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
    if not await check_if_channel(ctx):
        return

    n_time = stats_c.get_server_time()
    out = f"♦ SERVER TIME ♦\n    - now: {n_time['now']}\n    - voting in: {n_time['until_voting']}"
    await ctx.send(out)


# user specific commands
@bot.command(name="login", help="login to your account (dm only)")
async def login(ctx, username: str, password: str) -> None:
    """
    login
    """
    if not await check_if_dm(ctx):
        return

    with suppress(discord.errors.Forbidden):
        await ctx.message.delete()

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
    if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
        return

    LOGGED_IN_USERS[ctx.author].end()
    del LOGGED_IN_USERS[ctx.author]
    await ctx.send("Logged out")


@bot.command(name="vote", help="send a vote to the fridrich server (only when logged in)")
async def send_vote(ctx, vote: str, voting: str = "GayKing") -> None:
    """
    send a vote to the server
    """
    if not all([await check_if_dm(ctx), await check_if_logged_in(ctx)]):
        return

    LOGGED_IN_USERS[ctx.author].send_vote(vote, voting=voting, flag="vote")
    await ctx.send("Vote registered")


@bot.event
async def on_command_error(ctx, error) -> None:
    """
    run if there was an error running an command
    """
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

    elif isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(f"Invalid command \"{ctx.message.content.split(' '[0])}\" (not found)")


@bot.event
async def on_member_join(member):
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
    for user in LOGGED_IN_USERS:
        if LOGGED_IN_USERS[user] and LOGGED_IN_USERS[user].login_time > USER_TIMEOUT:
            print(f"user timed out: {user}")
            LOGGED_IN_USERS[user].end(revive=True)


if __name__ == '__main__':
    try:
        with stats_c as c:
            while not c:
                try:
                    c.auth("StatsBot", "IGetDaStats")

                except ConnectionError:
                    continue
            print("Bot started")
            check_login_time.start()
            bot.run(TOKEN)

    finally:
        for element in LOGGED_IN_USERS:
            LOGGED_IN_USERS[element].end()

# TODO: send message if 00:00 (voting has been done)
