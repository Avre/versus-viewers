#! python3.9
from twitchio.ext import commands #type: ignore
import json
import sys
import os
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from versusviewersv2 import PlayerQueue

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
    channel_name = sys.argv[1]
except IndexError:
    channel_name = ['avaren']

try:
    set_prefix = sys.argv[2]
except IndexError:
    set_prefix = '?'

active_channels = {}

print(f'Joining twitch channel {channel_name} with {set_prefix} set as command prefix.')

#Initialize default queue for each channel
for channel in channel_name:
    active_channels[channel] = PlayerQueue(channel)


##################################################################################
#BOT INITIALIZATION
##################################################################################

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token='AUTH_TOKEN_HERE', prefix=set_prefix, initial_channels=channel_name)

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
    async def open(self, ctx: commands.Context, *, full_message='default'):
        handler = active_channels[ctx.channel.name]
        # Mod check, check for an existing PlayerQueue object and create if necessary
        # Execute method to open queue and send notification to chat.
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}.')
            return

        if handler.queue_open:
            await ctx.send(handler.speak(f'The {full_message} queue is already open.'))
            print(f'The {full_message} queue is already open.')
            return

        handler.close_queue()
        handler.open_queue(full_message)
        await ctx.send(handler.speak(f'The {full_message} queue is now open!'))
        print(f'The {full_message} queue is now open!')

    @commands.command()
    async def close(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}.')
            return
        handler.close_queue()
        await ctx.send(handler.speak(f'The {handler.current_queue} queue is now closed!'))
        print(f'The {handler.current_queue} queue is now closed!')


    @commands.command()
    async def join(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        if not handler.queue_open:
            await ctx.send(handler.speak(f'The {handler.current_queue} queue is closed.'))
            print(f'The {handler.current_queue} queue is closed.')
            return

        if ctx.author.name in handler.current_queue:
            await ctx.send(handler.speak(f'You are already in the {handler.current_queue} queue, {ctx.author.name}'))
            print(f'You are already in the {handler.current_queue} queue, {ctx.author.name}')
            return

        try:
            if not handler.current_roster[ctx.author.name]['eligible']:
                await ctx.send(handler.speak(f'You have already played, {ctx.author.name}'))
                print(f'You have already played, {ctx.author.name}')
                return
        except KeyError:
            print(f'{ctx.author.name} was not found in roster.')

        handler.join_queue(ctx.author.name)
        await ctx.send(handler.speak(f'You are added to the {handler.current_queue} queue in position {handler.current_queue.index(ctx.author.name) + 1}, {ctx.author.name}'))
        print(f'You are added to the {handler.current_queue} queue in position {handler.current_queue.index(ctx.author.name) + 1}, {ctx.author.name}')


    @commands.command()
    async def leave(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        handler.leave_queue(ctx.author.name)
        await ctx.send(handler.speak(f'You are removed from the {handler.current_queue} queue, {ctx.author.name}'))
        print(f'You are removed from the {handler.current_queue} queue, {ctx.author.name}')

    @commands.command()
    async def position(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        await ctx.send(handler.speak(f'{ctx.author.name}, you are number {handler.current_queue.index(ctx.author.name) + 1} in queue.'))
        print(f'{ctx.author.name}, you are number {handler.current_queue.index(ctx.author.name) + 1} in queue.')

    @commands.command()
    async def length(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        await ctx.send(handler.speak(f'The queue has {len(handler.current_queue)} players in it.'))
        print(f'The queue has {len(handler.current_queue)} players in it.')

    @commands.command()
    async def next(self, ctx: commands.Context):
        handler = active_channels[ctx.channel.name]
        if not ctx.author.is_mod:
            await ctx.send(handler.speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}')
            return
        handler.next_player()
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
    async def reset(self, ctx: commands.Context,):
        handler = active_channels[ctx.channel.name]
        handler.reset()
        await ctx.send(handler.speak(f'The queue {handler.queue_name} has been reset.'))
        print(f'The queue {handler.queue_name} has been reset.')



    

###### TO DO
#refactor google sheets to use self sheet instance per channel instance and make it less shit
#clone pejters open, close, create, load, unload, save behavior




bot = Bot()
bot.run()
