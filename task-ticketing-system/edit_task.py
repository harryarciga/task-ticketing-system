import discord
import time
from discord.ext import commands

from googleapiclient.discovery import build
from google.oauth2 import service_account


from apikeys import *

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

