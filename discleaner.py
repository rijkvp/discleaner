import asyncio
import datetime
import discord
import json
import logging
import string


DATE_FMT = '%Y-%m-%d %H:%M'
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    datefmt=DATE_FMT, filename='discleaner.log', level=logging.INFO)

client_secret = None
target_ids = None
target_words = None
is_bot = None
target_only_self = None

with open('config.json', 'r') as f:
    config_json = json.loads(f.read())
    client_secret = config_json['secret']
    target_ids = [int(id) for id in config_json['target_ids']]
    target_words = config_json['target_words']
    is_bot = config_json['is_bot']
    target_only_self = config_json['target_only_self']


client = discord.Client()


def log_msg(msg, reason):
    logging.debug('[{}] <{}> {}: {}'.format(reason, msg.created_at.strftime(
        DATE_FMT), msg.author.name, msg.content))


async def delete_messages(channel, only_self):
    time_delta = datetime.timedelta(days=30)
    before_date = datetime.datetime.now() - time_delta

    message_chain = []

    try:
        async for msg in channel.history(limit=float('inf'), before=before_date, oldest_first=True):
            if not msg.pinned:
                if only_self:
                    if msg.author.id == client.user.id:
                        log_msg(msg, 'Self')
                        message_chain.append(msg.id)
                else:
                    search_str = ' ' + \
                        msg.content.translate(str.maketrans(
                            '', '', string.punctuation)).lower() + ' '
                    if msg.author.id in target_ids:
                        log_msg(msg, 'Targets')
                        message_chain.append(msg.id)
                    elif target_ids in [m.id for m in msg.mentions]:
                        log_msg(msg, 'Mention')
                        message_chain.append(msg.id)
                    elif msg.reference != None and msg.reference.message_id in message_chain:
                        log_msg(msg, 'Reference')
                        message_chain.append(msg.id)
                    elif any(word in search_str for word in target_words):
                        log_msg(msg, 'Word')
                        message_chain.append(msg.id)
    except Exception as e:
        logging.debug(
            'Error while reading history: no perms probably\n{}'.format(e))
        return 0

    logging.debug('\nDeleting {} messages.'.format(
        len(message_chain)))
    count = 0
    async for msg in channel.history(limit=float('inf'), before=before_date, oldest_first=True):
        if msg.id in message_chain:
            count += 1
            try:
                await msg.delete()
            except Exception as e:
                logging.debug('Error: deletion failed.\n{}'.format(e))
    return count


@client.event
async def on_ready():
    logging.info(
        'Logged in as: {}, starting operation..'.format(client.user.name))

    await client.change_presence(status=discord.Status.invisible)

    total_count = 0

    if not is_bot:
        logging.debug('Reading private channel history. Count is: {}'.format(
            len(client.private_channels)))
        for pc in client.private_channels:
            channel_name = None
            if pc.type is discord.ChannelType.private:
                logging.debug(
                    'Reading DM channel: {}'.format(pc.recipient.name))
                channel_name = pc.recipient.name
            elif pc.type is discord.ChannelType.group:
                logging.debug('Reading DM group channel: {}'.format(pc.name))
                channel_name = pc.name

            count = await delete_messages(pc, True)
            logging.info('Deleted {} messages from {}.'.format(
                count, channel_name))
            total_count += count

    for guild in client.guilds:
        logging.debug('Reaing guild: {}'.format(guild.name))
        for tc in guild.text_channels:
            logging.debug('Reading channel: {}'.format(tc.name))
            await delete_messages(tc, target_only_self)
    logging.info('Done! Deleted {} messages in total.'.format(total_count))
    await client.close()

client.run(client_secret, bot=is_bot)
