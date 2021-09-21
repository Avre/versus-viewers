#! python3.9
from twitchio.ext import commands #type: ignore
import json
import os
import sys
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials



if os.path.exists('roster.json'):
    with open('roster.json','r') as roster_file:
        player_roster = json.load(roster_file)
else:
    player_roster = {}

if os.path.exists('queue.json'):
    with open('queue.json','r') as queue_file:
        current_queue = json.load(queue_file)
else:
    current_queue = []

queue_is_open = False
current_player = ''

        
def is_eligible(chat_nick, input_roster = player_roster):
    return input_roster[chat_nick]['eligible']

def doc_list(list):
    return [[el] for el in list]

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)        
client = gspread.authorize(creds)

sheet = client.open('queue test')
sheet_instance = sheet.get_worksheet(0)

try:
    channel_name = sys.argv[1]
except IndexError:
    channel_name = 'avaren'

try:
    set_prefix = sys.argv[2]
except IndexError:
    set_prefix = '?'


print(f'joining {channel_name}')

class Bot(commands.Bot):

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        super().__init__(token='21rrsrnu01fvuyaaumtvcy6n3q0108', prefix=set_prefix, initial_channels=[channel_name])

    async def event_ready(self):
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return

        if message.content.startswith(set_prefix):
            print(f'{message.author.name}: {message.content}')

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    # @commands.command()
    # async def hello(self, ctx: commands.Context):
    #     # Send a hello back!
    #     await ctx.send(f'Hello {ctx.author.name}!')     

    @commands.command()
    async def join(self, ctx: commands.Context):
        if not queue_is_open:
            print('The queue is closed.')
            return
        if ctx.author.name in current_queue:
            print(f'You are already in the queue, {ctx.author.name}.')
            return
        if ctx.author.name in player_roster and is_eligible(ctx.author.name):
            current_queue.append(ctx.author.name)
        else:
            player_roster[ctx.author.name] = {'name': ctx.author.name, 'eligible': True}
            current_queue.append(ctx.author.name)
            with open('roster.json','w') as roster_file:
                json.dump(player_roster, roster_file, indent = 4)
        print(f'You are added to the queue, {ctx.author.name}!')

    @commands.command()
    async def leave(self, ctx: commands.Context):
        current_queue.remove(ctx.author.name)
        print(f'You are removed from the queue, {ctx.author.name}!')

    @commands.command()
    async def position(self, ctx: commands.Context):
        print(f'{ctx.author.name}, you are number {current_queue.index(ctx.author.name) + 1} in queue.')

    @commands.command()
    async def length(self, ctx: commands.Context):
        print(f'The queue has {len(current_queue)} players in it.')

    @commands.command()
    async def next(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            print(f'You are not a moderator, {ctx.author.name}.')
            return
        global current_player, sheet, sheet_instance
        current_player = current_queue.pop()
        print(f'{current_player} is now playing!')
        with open('queue.json','w') as queue_file:
            json.dump(current_queue, queue_file, indent = 4)
        sheet_instance.clear()
        sheet_instance.append_rows([[current_player]])
        sheet_instance.append_rows(doc_list(current_queue))


    @commands.command()
    async def list(self, ctx: commands.Context):
        print(f'PLAYER is currently fighting {current_player}!  Next 5 up are: {", ".join(current_queue[:5])} ')

    @commands.command()
    async def clear(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            print(f'You are not a moderator, {ctx.author.name}.')
            return        
        global current_queue, sheet, sheet_instance
        current_queue = []
        print(f'The queue has been cleared.')
        sheet_instance.clear()

    @commands.command()
    async def open(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            print(f'You are not a moderator, {ctx.author.name}.')
            return
        global queue_is_open
        queue_is_open = True
        print('The queue is now open!')

    @commands.command()
    async def close(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            print(f'You are not a moderator, {ctx.author.name}.')
            return
        global queue_is_open, current_queue, player_roster
        queue_is_open = False
        with open('queue.json','w') as queue_file:
            json.dump(current_queue, queue_file, indent = 4)
        with open('roster.json','w') as roster_file:
            json.dump(player_roster, roster_file, indent = 4)
        print('The queue is now closed!')






bot = Bot()
bot.run()
