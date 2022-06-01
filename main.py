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

discussion_index = 0

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
            votes INTEGER,
            is_discussed INTEGER
           );
            ''')
  print("Table created")
  
  conn.commit()

def execute_sql(sql, params):   
    conn = sql_connection()
    cursor = conn.cursor()
  
    if(params == None):
        cursor.execute(sql)
    else:
        cursor.execute(sql, params)
      
    conn.commit()
    return cursor

emojis=['😎', '🍍','🌈', '🥝','🍅', '🍆','🥑', '🥦','🥬','🥒', '🌶', '🫑','🌽','🥕','🫒', '🌝','🥔', '🍠', '🥐', '🥯', '🍞', '🥖', '🥨', '🧀', '🥚', '🍳', '🧈', '🥞', '🧇', '🥓', '🥩', '🍗', '🍖', '🦴', '🌭', '🍔', '🍟', '🍕', '🫓', '🥪', '🥙', '🧆']

def select_topics():
    sql = 'SELECT * FROM topics'
    cursor = execute_sql(sql, None)
    return cursor

def get_descending():
  sql = '''SELECT topic, author 
           FROM topics 
           ORDER BY votes DESC
           '''
  cursor = execute_sql(sql, None)
  topics_descending = cursor.fetchall()

  return topics_descending

def add_topic(topic, author):
    params = (topic, author, 0, 0)
    sql = 'INSERT INTO topics (topic, author, votes, is_discussed) VALUES (?, ?, ?, ?)'
    execute_sql(sql,params)
  
def delete_topic(topicID):
    sql = 'DELETE FROM topics WHERE topic_id = ?'
    execute_sql(sql, None)

async def list_topics(topic_channel):
  topics = select_topics().fetchall()
  if len(topics) > 0:
    res = ['\n'.join(f"{str(topic[0])} | {topic[2]} - {topic[1]}" for topic in topics)]
    formatted = '\n'.join(res)
    await topic_channel.send(formatted)
  else:
    await topic_channel.send("There are no topics!!!")

def clear_topics():
    sql_delete = 'DELETE FROM topics'
    sql_reset = 'DELETE FROM sqlite_sequence WHERE NAME=name'
    execute_sql(sql_delete, None)
    execute_sql(sql_reset, None)

def update_votes(votes, topicID):
  params = (votes, topicID)
  sql = 'UPDATE topics SET votes = ? WHERE topic_id = ?'
  execute_sql(sql, params)

async def suggestion_announcement(topic_channel):
  clear_topics()
  await topic_channel.send('@here Time to suggest some topics!!!')

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

async def declare_winner(topic_channel):
  topics = select_topics().fetchall()
  poll_message = await topic_channel.fetch_message(poll_msg.id)

  for topic in topics:
    topic_index = topics.index(topic)
    topic_id = topics.index(topic) + 1
    
    reaction = get(poll_message.reactions,   emoji=emojis[topic_index])
    num_reactions = reaction.count
    
    update_votes(num_reactions, topic_id)

  topics_descending = get_descending()
  winner = topics_descending[0]
  winning_topic = winner[0]
  winning_author = winner[1]

  global discussion_index
  discussion_index += 1
  
  await topic_channel.send(f'The winner is:\n\t"{winning_topic}"\nWhich was asked by:\n\t{winning_author}\n@here Discuss!!!')

async def current_topic(topic_channel):
  global discussion_index
  
  try:
    current = get_descending()[discussion_index -1]
    current_topic = current[0]
    current_author = current[1]
    
    await topic_channel.send(f'The current topic is:\n\t"{current_topic}" - {current_author}')
    
    discussion_index += 1
  except:
    await topic_channel.send('There are no more topics!')

async def next_topic(topic_channel):
  global discussion_index
  
  try:
    next = get_descending()[discussion_index]
    next_topic = next[0]
    next_author = next[1]
    
    await topic_channel.send(f'The next topic is:\n\t"{next_topic}"\nWhich was asked by:\n\t{next_author}\n@here Discuss!!!')
    
    discussion_index += 1
  except:
    await topic_channel.send('There are no more topics!')

async def display_help(topic_channel):
    command_list = ["$topic: add topic", "$list: list current topics", "$current: show current topic being discussed", "$help: list commands"]
  
    help_embed=discord.Embed(title='Help', description='Here are some helpful commands:', color=0xffffff)
    
    help_embed.add_field(name='Commands:', value = '\n'.join(command_list), inline=False)

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

    if msg.startswith('$winner'):
        topic_channel=client.get_channel(964331446934306826)
        await declare_winner(topic_channel)

    if msg.startswith('$next'):
        topic_channel=client.get_channel(964331446934306826)
        await next_topic(topic_channel)

    if msg.startswith('$current'):
        topic_channel=client.get_channel(964331446934306826)
        await current_topic(topic_channel)

    if msg.startswith('$help'):
        topic_channel=client.get_channel(964331446934306826)
        await display_help(topic_channel);


keep_alive()
client.run(my_secret)