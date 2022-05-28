import os
import sqlite3
from sqlite3 import Error
import discord
import random
from replit import db
from keep_alive import keep_alive
import asyncio
from discord.utils import get
from discord.ext import tasks, commands

my_secret = os.environ['TOKEN']

client = discord.Client()

topic_channel=client.get_channel(964331446934306826)

#Connect to database
def sql_connection():
  try:
    conn = sqlite3.connect('database.db')
    print("Connection is established: Database is created in memory")
    return conn
  except Error:
    print(Error)

#Create cursor and topic table 
def sql_table(conn):
  cursor = conn.cursor()

  cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics(
            topicID INTEGER PRIMARY KEY AUTOINCREMENT, 
            author TEXT NOT NULL, 
            topic TEXT NOT NULL,
            votes INTEGER
           );
            ''')
  print("Table created")
  conn.commit()

emojis=['😎', '🍍','🌈', '🥝','🍅', '🍆','🥑', '🥦','🥬','🥒', '🌶', '🫑','🌽','🥕','🫒', '🌝','🥔', '🍠', '🥐', '🥯', '🍞', '🥖', '🥨', '🧀', '🥚', '🍳', '🧈', '🥞', '🧇', '🥓', '🥩', '🍗', '🍖', '🦴', '🌭', '🍔', '🍟', '🍕', '🫓', '🥪', '🥙', '🧆']

#Select all topics
def select_topics():
    conn = sqlite3.connect('database.db')
    sql = 'SELECT * FROM topics'

    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
  
    return cursor

#Add topic to topic table in db
def add_topic(topic, author):
    conn = sqlite3.connect('database.db')
    params = (topic, author, 0)
    sql = 'INSERT INTO topics (topic, author, votes) VALUES (?, ?, ?)'
  
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()

#Delete topic from topic table in db
def delete_topic(topicID):
    conn = sqlite3.connect('database.db')
    sql = 'DELETE FROM topics WHERE topicID = ?'

    cursor = conn.cursor()
    cursor.execute(sql, topicID)
    conn.commit()

async def list_topics(topic_channel):
  topics = select_topics().fetchall()
  if len(topics) > 0:
    res = '\n'.join(str(topic) for topic in topics)
    await topic_channel.send(res)
  else:
    await topic_channel.send("There are no topics!!!")

#Clear topics in topic table in db
def clear_topics():
    conn = sqlite3.connect('database.db')
    sql_delete = 'DELETE FROM topics'
    sql_reset = 'DELETE FROM sqlite_sequence WHERE NAME=name'
  
    cursor = conn.cursor()
    cursor.execute(sql_delete)
    conn.commit()

    cursor.execute(sql_reset)
    conn.commit()

#Create announcement to start topic suggestion round
async def suggestion_announcement(topic_channel):
  clear_topics()
  await topic_channel.send('@here Time to suggest some topics!!!')

#Create poll
async def create_poll(topic_channel):
    topics = select_topics().fetchall()

    res = ['\n'.join(f"{emojis[topics.index(topic)]} - {str(topic[2])} - {topic[1]}" for topic in topics)]

    if len(topics) > 0:
        my_embed=discord.Embed(title='Topic of the day', description='Vote for your favourite topic', color=0xffffff)
    
        my_embed.add_field(name='Topics:', value = '\n'.join(res), inline=False)

        global poll_msg
        poll_msg=await topic_channel.send(embed=my_embed)
        
        for topic in topics:
            await poll_msg.add_reaction(emojis[topics.index(topic)])

        await topic_channel.send('@here Time to vote!!!')
    else:
        await topic_channel.send('There are no topics!!!')

#Display help message
async def display_help(topic_channel):
    command_list = ["$topic: add topic", "$list: list current topics", "$current: show current topic being discussed", "$help: list commands"]
  
    help_embed=discord.Embed(title='Help', description='Here are some helpful commands:', color=0xffffff)
    
    help_embed.add_field(name='Commands:', value = '\n'.join(command_list), inline=False)

    await topic_channel.send(embed=help_embed)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    conn = sql_connection()
    sql_table(conn)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content

    if msg.startswith('$topic '):
        topic = msg.split('$topic ',1)[1]
        author = str(message.author)
        add_topic(topic, author)

    if msg.startswith('$list'):
        topic_channel=client.get_channel(964331446934306826)
        await list_topics(topic_channel)
  
    if msg.startswith('$suggest'):
        topic_channel=client.get_channel(964331446934306826)
        await suggestion_announcement(topic_channel)

    if msg.startswith('$poll'):
        topic_channel=client.get_channel(964331446934306826)
        await create_poll(topic_channel)

    if msg.startswith('$help'):
        topic_channel=client.get_channel(964331446934306826)
        await display_help(topic_channel);


keep_alive()
client.run(my_secret)