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