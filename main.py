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

#Connect to database
def sql_connection():
  try:
    conn = sqlite3.connect('database.db')
    print("Connection is established: Database is created in memory")
  except Error:
    print(Error)
  finally:
    conn.close()

#Create cursor and topic table 
def sql_table(conn):
  cursor = conn.cursor()

  cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics(
            topicID INTEGER PRIMARY KEY AUTOINCREMENT, 
            author TEXT NOT NULL, 
            topic TEXT NOT NULL
           );
            ''')
  conn.commit()

conn = sql_connection()
sql_table(conn)

emojis=['😎', '🍍','🌈', '🥝','🍅', '🍆','🥑', '🥦','🥬','🥒', '🌶', '🫑','🌽','🥕','🫒', '🌝','🥔', '🍠', '🥐', '🥯', '🍞', '🥖', '🥨', '🧀', '🥚', '🍳', '🧈', '🥞', '🧇', '🥓', '🥩', '🍗', '🍖', '🦴', '🌭', '🍔', '🍟', '🍕', '🫓', '🥪', '🥙', '🧆']

#Select all topics
def select_topics(conn):
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM topics''')
    conn.commit()

#Add topic to topic table in db
def add_topic(conn, topic, author):
    params = (topic, author)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO topics (topic, author) VALUES (?, ?)''', params)
    conn.commit()

#Delete topic from topic table in db
def delete_topic(conn,  topicID):
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM topics WHERE topicID = ?''', topicID)
    conn.commit()

#Clear topics in topic table in db
def clear_topics(conn):
    cursor = conn.cursor()
    cursor.execute('''DELETE * FROM topics''')
    conn.commit()

#Create announcement to start topic suggestion round
async def suggestion_announcement(conn, topic_channel):
  clear_topics(conn)
  await topic_channel.send('@here Time to suggest some topics!!!')

#Create poll
async def create_poll(conn, topic_channel):
  cursor = conn.cursor()
  topics = select_topics().fetchall()
