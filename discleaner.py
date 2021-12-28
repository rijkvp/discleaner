import discord
from discord.ext import commands
import json
import datetime
import asyncio

client_secret = None
target_ids = None
is_bot = None

bot = commands.Bot(command_prefix="!")

with open("config.json", "r") as f:
    config_json = json.loads(f.read())
    client_secret = config_json["secret"]
    target_ids = [int(id) for id in config_json["target_ids"]]
    is_bot = config_json["is_bot"]

async def delete_messages(channel):
    time_delta = datetime.timedelta(days=30)
    before_date = datetime.datetime.now() - time_delta
    print("Deleting before {}".format(before_date.strftime("%Y-%m-%d %H:%M")))

    message_chain = []

    try:
        async for msg in channel.history(limit=float('inf'), before=before_date, oldest_first=True):
            if not msg.pinned:
                if msg.author.id in target_ids:
                    print("DIRECT   == <{}> {}: {}".format(msg.created_at.strftime("%Y-%m-%d %H:%M"), msg.author.name, msg.content))
                    message_chain.append(msg.id)
                elif target_ids in [m.id for m in msg.mentions]:
                    print("MENTION   == <{}> {}: {}".format(msg.created_at.strftime("%Y-%m-%d %H:%M"), msg.author.name, msg.content))
                    message_chain.append(msg.id)
                elif msg.reference != None and msg.reference.message_id in message_chain:
                    print("REFCHAIN  == <{}> {}: {}".format(msg.created_at.strftime("%Y-%m-%d %H:%M"), msg.author.name, msg.content))
                    message_chain.append(msg.id)
    except Exception as e: 
        print("Error: no perms probably")
        print(e)
        return
    
    print("\nDeleting {} messages from {}..".format(len(message_chain), channel.name))
    async for msg in channel.history(limit=float('inf'), before=before_date, oldest_first=True):
        if msg.id in message_chain:
            try:
                await msg.delete()
            except:
                print("Deletion failed.")

@bot.event
async def on_ready():
    print('Logged in as: {}'.format(bot.user.name))
    await bot.change_presence(status=discord.Status.invisible)
    for guild in bot.guilds:
        print('\n\nGUILD: {}'.format(guild.name))
        for tc in guild.text_channels:
            print('\nCHANNEL: {}'.format(tc.name))
            await delete_messages(tc)
    print("Done!")

bot.run(client_secret, bot=is_bot)
