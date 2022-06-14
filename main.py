import os
import sqlite3
from sqlite3 import Error
import discord
from keep_alive import keep_alive
from discord.utils import get
from discord.ext.commands import Bot

my_secret = os.environ['TOKEN']

client = Bot("!")

is_voting = False
is_current = False
discussion_index = 0
embed_color = 0x40ff9e
emoji_string = '🍏🍎🍐🍊🍋🍌🍉🍇🍓🫐🍈🍒🍑🥭🍍🥥🥝🍅🍆🥑🥦🥬🥒🌶🫑🌽🥕🫒🧄🧅🥔🍠🥐🥯🍞🥖🥨🧀🥚🍳🧈🥞🧇🥓🥩🍗🍖🦴🌭🍔🍟🍕🫓🥪🥙🧆🌮🌯🫔🥗'
emojis = [char for char in emoji_string]


def sql_connection():
    try:
        conn = sqlite3.connect('database.db')
        print("Connection is established: Database is created in memory")
        return conn
    except Error:
        print(Error)


def sql_table():
    conn = sql_connection()
    cursor = conn.cursor()

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics(
            topic_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            author TEXT NOT NULL, 
            topic TEXT NOT NULL,
            votes INTEGER
           );
            ''')
    print("Table created")

    conn.commit()


def execute_sql(sql, *params):
    conn = sql_connection()
    cursor = conn.cursor()

    NoneType = type(None)
    if not isinstance(params[0], (int, NoneType)) and not isinstance(params[0], (str, NoneType)):
        params = params[0]

    try:
        if None in params:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
    except Exception as e:
        print("ERROR : " + str(e))

    conn.commit()
    return cursor


def select_topics():
    sql = 'SELECT * FROM topics'
    cursor = execute_sql(sql, None)
    topics = cursor.fetchall()
    return topics


def select_topic(topic_id):
    sql = 'SELECT * FROM topics WHERE topic_id = ?'
    cursor = execute_sql(sql, topic_id)
    topic = cursor.fetchall()
    return topic


def count_user_topics(author):
    sql = 'SELECT * FROM topics WHERE author = ?'
    cursor = execute_sql(sql, author)
    topics = cursor.fetchall()
    return len(topics)


def get_descending():
    sql = '''SELECT topic, author 
           FROM topics 
           ORDER BY votes DESC
           '''
    cursor = execute_sql(sql, None)
    topics_descending = cursor.fetchall()

    return topics_descending


def clear_topics():
    sql_delete = 'DELETE FROM topics'
    sql_reset = 'DELETE FROM sqlite_sequence WHERE NAME=name'
    execute_sql(sql_delete, None)
    execute_sql(sql_reset, None)


def update_votes(votes, topicID):
    params = (votes, topicID)
    sql = 'UPDATE topics SET votes = ? WHERE topic_id = ?'
    execute_sql(sql, params)


def get_current_topic(discussion_index):
    current_topic = get_descending()[discussion_index]
    return current_topic


async def add_topic(topic, author, topic_channel):
    global is_voting
    if is_voting:
        await topic_channel.send('Voting is in progress!')
        return

    if count_user_topics(author) >= 5:
        await topic_channel.send('You may only suggest a maximum of 5 topics!')
        return

    try:
        params = (topic, author, 0)
        sql = 'INSERT INTO topics (topic, author, votes) VALUES (?, ?, ?)'
        execute_sql(sql, params)
    except:
        await topic_channel.send('Topic limit reached!')


async def delete_topic(topic_index, author, topic_channel):
    global is_voting
    if is_voting:
        await topic_channel.send('Voting is in progress!')
        return

    topics = select_topics()
    if len(topics) <= 0:
        await topic_channel.send("There are no topics!")
        return

    try:
        topic = topics[int(topic_index)]
        topic_id = topic[0]
        topic = select_topic(topic_id)[0]
        if (topic[1] == str(author)):
            sql_delete = 'DELETE FROM topics WHERE topic_id = ?'
            execute_sql(sql_delete, topic_id)
        else:
            await topic_channel.send('You are not the author of this topic')
    except:
        await topic_channel.send('Please enter a valid index')


async def list_topics(topic_channel):
    topics = select_topics()

    if len(topics) <= 0:
        await topic_channel.send("There are no topics!")
        return

    res = [
        '\n'.join(f"{topics.index(topic)} | {topic[2]} - {topic[1]}"
                  for topic in topics)
    ]

    my_embed = discord.Embed(
        title='Suggested topics',
        description='Here is a list of the suggested topics',
        color=embed_color)

    formatted = '\n'.join(res)

    my_embed.add_field(name='Topics:', value=formatted, inline=False)

    await topic_channel.send(embed=my_embed)


async def suggestion_announcement(topic_channel):
    clear_topics()

    global discussion_index
    discussion_index = 0

    global is_current
    is_current = False

    global is_voting
    is_voting = False

    await topic_channel.send(
        '<@&985985687218167828> Time to suggest some topics!')
    await topic_channel.edit(topic='', slowmode_delay=int(30))


async def create_poll(topic_channel):
    global is_voting
    global discussion_index
    discussion_index = 0

    topics = select_topics()

    if len(topics) <= 0:
        await topic_channel.send("There are no topics!")
        return

    res = [
        '\n'.join(
            f"{emojis[topics.index(topic)]} - {str(topic[2])} - {topic[1]}"
            for topic in topics)
    ]

    formatted = '\n'.join(res)

    my_embed = discord.Embed(title='Topic of the day',
                             description='Vote for your favourite topic',
                             color=embed_color)

    my_embed.add_field(name='Topics:', value=formatted, inline=False)

    global poll_msg
    poll_msg = await topic_channel.send(embed=my_embed)

    for topic in topics:
        topic_index = topics.index(topic)
        await poll_msg.add_reaction(emojis[topic_index])

    await topic_channel.send('<@&985985687218167828> Time to vote!')
    await topic_channel.set_permissions(topic_channel.guild.default_role, send_messages=False)
    is_voting = True


async def declare_winner(topic_channel):
    global is_current
    global is_voting

    topics = select_topics()

    if len(topics) <= 0:
        await topic_channel.send("There are no suggested topics!")
        return

    try:
        global poll_msg
        poll_message = await topic_channel.fetch_message(poll_msg.id)
    except:
        await topic_channel.send('No poll')

    for topic in topics:
        topic_index = topics.index(topic)
        topic_id = topic[0]

        reaction = get(poll_message.reactions, emoji=emojis[topic_index])
        num_reactions = reaction.count

        update_votes(num_reactions, topic_id)

    topics_descending = get_descending()
    winner = topics_descending[0]
    winning_topic = winner[0]
    winning_author = winner[1]

    my_embed = discord.Embed(color=embed_color)

    my_embed.add_field(
        name='Winner',
        value=f'\nTopic:\n    **{winning_topic}**\nAuthor:\n    **{winning_author}**',
        inline=False)

    await topic_channel.send(embed=my_embed)
    await topic_channel.send('<@&985985687218167828> Discuss!')
    await topic_channel.edit(topic=f'The current topic is: "{winning_topic}"', slowmode_delay=int(0))
    is_current = True
    is_voting = False


async def declare_current_topic(topic_channel):
    global discussion_index
    global is_current

    if not is_current:
        await topic_channel.send('There is no current topic!')
        return

    try:
        current_topic = get_current_topic(discussion_index)[0]
        current_author = get_current_topic(discussion_index)[1]

        my_embed = discord.Embed(color=embed_color)

        my_embed.add_field(
            name='Current topic',
            value=f'\nTopic:\n    **{current_topic}**\nAuthor:\n    **{current_author}**',
            inline=False)

        await topic_channel.send(embed=my_embed)
    except:
        await topic_channel.send('There is no current topic!')


async def next_topic(topic_channel):
    global discussion_index
    discussion_index += 1

    try:
        next_topic = get_current_topic(discussion_index)[0]
        next_author = get_current_topic(discussion_index)[1]

        my_embed = discord.Embed(color=embed_color)

        my_embed.add_field(
            name='Next topic',
            value=f'\nTopic:\n**{next_topic}**\nAuthor:\n**{next_author}**'.
            format(next_topic, next_author),
            inline=False)

        await topic_channel.send(embed=my_embed)

        await topic_channel.send('<@&985985687218167828> Discuss!')
    except:
        await topic_channel.send('There are no more topics!')


async def display_help(topic_channel):
    command_list = [
        "**$topic**: add topic", "**$list**: list current topics",
        "**$current**: show current topic being discussed",
        "**$help**: list commands"
    ]

    help_embed = discord.Embed(title='Help',
                               description='Here are some helpful commands:',
                               color=embed_color)

    help_embed.add_field(name='Commands:',
                         value='\n'.join(command_list),
                         inline=False)

    await topic_channel.send(embed=help_embed)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    sql_table()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content

    if msg.startswith('$topic '):
        topic_channel = message.channel
        topic = msg.split('$topic ', 1)[1]
        author = str(message.author)
        await add_topic(topic, author, topic_channel)

    if msg.startswith('$list'):
        topic_channel = message.channel
        await list_topics(topic_channel)

    if msg.startswith('$suggest'):
        topic_channel = message.channel
        if message.author.guild_permissions.administrator == True:
            await suggestion_announcement(topic_channel)
        else:
            print("not admin")

    if msg.startswith('$poll'):
        topic_channel = message.channel
        if message.author.guild_permissions.administrator == True:
            await create_poll(topic_channel)
        else:
            print("not admin")

    if msg.startswith('$winner'):
        topic_channel = message.channel
        if message.author.guild_permissions.administrator == True:
            await declare_winner(topic_channel)
        else:
            print("not admin")

    if msg.startswith('$next'):
        topic_channel = message.channel
        if message.author.guild_permissions.administrator == True:
            await next_topic(topic_channel)
        else:
            print("not admin")

    if msg.startswith('$current'):
        topic_channel = message.channel
        await declare_current_topic(topic_channel)

    if msg.startswith('$delete'):
        author = message.author
        topic_id = msg.split('$delete ', 1)[1]
        topic_channel = message.channel
        await delete_topic(topic_id, author, topic_channel)

    if msg.startswith('$help'):
        topic_channel = message.channel
        await display_help(topic_channel)


keep_alive()
client.run(my_secret)
