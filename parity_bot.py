#! python3.9
from twitchio.ext import commands #type: ignore
import json
import sys
import os
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from versusviewers import PlayerQueue

##################################################################################
#GOOGLE SHEETS CONNECTION
##################################################################################

def doc_list(list):
    return [[el] for el in list]

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

sheet = client.open('versusviewers.com')
sheet_instance = sheet.get_worksheet(0)

##################################################################################
#ARGUMENT INGESTION, VARIABLE INITIALIZATION AND JOIN
##################################################################################

try:
    set_prefix = sys.argv[1]
except IndexError:
    set_prefix = '?'

channel_names = []

if sys.argv[2:]:
    for arg in sys.argv[2:]:
        channel_names.append(arg)
else:
    channel_names = ['avaren']


print(f'Joining twitch channels {", ".join(channel_names)} with {set_prefix} set as command prefix.')

#Initialize default queue for each channel
for channel in channel_names:
    os.makedirs(str(f'.{os.sep}queues{os.sep}{channel}'), exist_ok= True)

active_channels = {}

for channel in channel_names:
    active_channels[channel.lower()] = PlayerQueue(channel)

with open('token.txt') as fp:
    auth_token = fp.read()

##################################################################################
#BOT INITIALIZATION
##################################################################################

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=auth_token, prefix=set_prefix, initial_channels=channel_names)

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    async def event_message(self, message):

        if message.echo:
            return
        if message.content.startswith(set_prefix):
            print(f'{message.author.name}: {message.content}')
        await self.handle_commands(message)

    @commands.command()
    async def hello(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        # Just here to make sure the bot isn't busted
        await ctx.send(handler.speak(f'Hello {ctx.author.name}.'))
        print(f'Hello {ctx.author.name}')

    @commands.command()
    async def botmutetoggle(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        # Moderator check, then toggles the PlayerQueue.muted attribute between True and False
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}.')
            return
        handler.muted = not handler.muted
        await ctx.send(handler.speak(f'Bot is no longer muted.'))
        print(f'Bot is no longer muted.')


    @commands.command()
    async def open(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        # Mod check, check for an existing PlayerQueue object and create if necessary
        # Execute method to open queue and send notification to chat.
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}.')
            return

        if handler.queue_open:
            await ctx.send(handler.speak(f'The {handler.queue_name} queue is already open.'))
            print(f'The {handler.queue_name} queue is already open.')
            return

        handler.close_queue()
        handler.open_queue(handler.queue_name)
        await ctx.send(handler.speak(f'The {handler.queue_name} queue is now open!'))
        print(f'The {handler.queue_name} queue is now open!')

    @commands.command()
    async def close(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}.')
            return
        handler.close_queue()
        await ctx.send(handler.speak(f'The {handler.queue_name} queue is now closed!'))
        print(f'The {handler.queue_name} queue is now closed!')


    @commands.command()
    async def join(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        if not handler.queue_open:
            await ctx.send(handler.speak(f'The {handler.queue_name} queue is closed.'))
            print(f'The {handler.queue_name} queue is closed.')
            return

        if ctx.author.name in handler.current_queue:
            await ctx.send(handler.speak(f'You are already in the {handler.queue_name} queue, {ctx.author.name}'))
            print(f'You are already in the {handler.queue_name} queue, {ctx.author.name}')
            return

        try:
            if not handler.current_roster[ctx.author.name]['eligible']:
                await ctx.send(handler.speak(f'You have already played, {ctx.author.name}'))
                print(f'You have already played, {ctx.author.name}')
                return
        except KeyError:
            print(f'{ctx.author.name} was not found in roster.')

        handler.join_queue(ctx.author.name)
        await ctx.send(handler.speak(f'You are added to the {handler.queue_name} queue in position {handler.current_queue.index(ctx.author.name) + 1}, {ctx.author.name}'))
        print(f'You are added to the {handler.queue_name} queue in position {handler.current_queue.index(ctx.author.name) + 1}, {ctx.author.name}')


    @commands.command()
    async def leave(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        handler.leave_queue(ctx.author.name)
        await ctx.send(handler.speak(f'You are removed from the {handler.queue_name} queue, {ctx.author.name}'))
        print(f'You are removed from the {handler.queue_name} queue, {ctx.author.name}')

    @commands.command()
    async def position(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        await ctx.send(handler.speak(f'{ctx.author.name}, you are number {handler.current_queue.index(ctx.author.name) + 1} in the {handler.queue_name} queue.'))
        print(f'{ctx.author.name}, you are number {handler.current_queue.index(ctx.author.name) + 1} in the {handler.queue_name} queue.')

    @commands.command()
    async def length(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        await ctx.send(handler.speak(f'The {handler.queue_name} queue has {len(handler.current_queue)} players in it.'))
        print(f'The the {handler.queue_name} queue has {len(handler.current_queue)} players in it.')

    @commands.command()
    async def next(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}')
            return
        handler.next_player()
        await ctx.send(handler.speak(f'It\'s your turn, {handler.current_player}.  Next in line is {handler.current_queue[0]}'))
        sheet_instance.clear()
        sheet_instance.append_rows([[handler.current_player]])
        sheet_instance.append_rows(doc_list(handler.current_queue))

    @commands.command()
    async def list(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        await ctx.send(handler.speak(f'{ctx.channel.name} is currently fighting {handler.current_player}!  Next 5 up are: {", ".join(handler.current_queue[:5])} '))
        print(f'{ctx.channel.name} is currently fighting {handler.current_player}!  Next 5 up are: {", ".join(handler.current_queue[:5])} ')

    @commands.command()
    async def clear(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}')
            return
        handler.clear_queue()
        await ctx.send(handler.speak(f'The {handler.queue_name} queue has been cleared.'))
        print(f'The {handler.queue_name} queue has been cleared.')
        sheet_instance.clear()

    @commands.command()
    async def reset(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}')
            return
        handler.reset()
        await ctx.send(handler.speak(f'The queue {handler.queue_name} has been reset.'))
        print(f'The queue {handler.queue_name} has been reset.')

    @commands.command()
    async def select(self, ctx: commands.Context, *, full_message = 'default'):
        handler = active_channels[ctx.channel.name]
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}')
            return
        handler.change_queue(full_message)
        await ctx.send(handler.speak(f'The queue {handler.queue_name} has been selected.'))
        print(f'The queue {handler.queue_name} has been selected.')


    @commands.command()
    async def save(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}')
            return
        handler.save()
        await ctx.send(handler.speak(f'The queue {handler.queue_name} has been saved.'))
        print(f'The queue {handler.queue_name} has been saved.')

    @commands.command()
    async def queue(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        await ctx.send(handler.speak(f'Current queue: {handler.queue_name} -- Status: {"open" if handler.queue_open else "closed"}.  Use command !join to join an open queue.'))

    @commands.command()
    async def queuedoc(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        await ctx.send(handler.speak(f'The current queue can be accessed at www.{handler.streamer_name}.versusviewers.com'))
        print(f'The current queue can be accessed at www.{handler.streamer_name}.versusviewers.com')

    @commands.command()
    async def troy(self, ctx: commands.Context):
        await ctx.send('OhMyDog')
        print('OhMyDog')




bot = Bot()
bot.run()
