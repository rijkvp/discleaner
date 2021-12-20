import discord
from discord.ext import commands
import json
import datetime
import asyncio

client_secret = None

bot = commands.Bot(command_prefix="!")

with open("config.json", "r") as f:
    config_json = json.loads(f.read())
    client_secret = config_json["secret"]

async def delete_messages(channel, before_date):
    async for msg in channel.history(before=before_date, oldest_first=True):
        if not msg.pinned:
            print("<{}> {}".format(msg.created_at.strftime("%Y-%m-%d %H:%M"), msg.content))
            try:
                await msg.delete()
            except:
                pass
        else: 
            print("Keeping pinned " + msg.content)

# Only allow two or three months to prevent deleting recent messages
def get_time(time_name):
    if time_name == "3m":
        return ("three months", datetime.timedelta(days=90))
    elif time_name == "2m":
        return ("two months", datetime.timedelta(days=60))
    else:
        return (None, None)

@bot.command(name="clean-server")
async def clean_server(ctx, time_name):
    try:
        await ctx.message.delete()
    except:
        pass

    time_name, time_delta = get_time(time_name)

    if time_name == None or time_delta == None:
        await ctx.send("Invalid time argument!", delete_after=10)
        return

    await ctx.send("Cleaning messages older than {}..".format(time_name), delete_after=10)

    before_date = datetime.datetime.now() - time_delta

    for channel in ctx.guild.text_channels:
        print("Clean channeling {}".format(channel.name))
        await delete_messages(channel, before_date)
    
    await ctx.send("Old messages have been deleted.", delete_after=10)

@bot.command(name="clean-channel")
async def clean_channel(ctx, time_name):
    try:
        await ctx.message.delete()
    except:
        pass

    time_name, time_delta = get_time(time_name)

    if time_name == None or time_delta == None:
        await ctx.send("Invalid time argument!", delete_after=10)
        return

    await ctx.send("Cleaning messages older than {}..".format(time_name), delete_after=10)

    before_date = datetime.datetime.now() - time_delta
    await delete_messages(ctx.message.channel, before_date)
    
    await ctx.send("Old messages have been deleted.", delete_after=10)

@bot.event
async def on_ready():
    print('Logged in as: {0.user}'.format(bot))

bot.run(client_secret)
