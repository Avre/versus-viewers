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
    channel_name = ['sajam']

try:
    set_prefix = sys.argv[2]
except IndexError:
    set_prefix = '!'

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
        super().__init__(token='21rrsrnu01fvuyaaumtvcy6n3q0108', prefix=set_prefix, initial_channels=channel_name)

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
        # Just here to make sure the bot isn't busted
        await ctx.send(active_channels[ctx.channel.name].speak(f'Hello {ctx.author.name}.'))
        print(f'Hello {ctx.author.name}')

    @commands.command()
    async def botmutetoggle(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            await ctx.send(active_channels[ctx.channel.name].speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}.')
            return

        active_channels[ctx.channel.name].muted = not active_channels[ctx.channel.name].muted
        await ctx.send(active_channels[ctx.channel.name].speak(f'Bot is no longer muted.'))
        print(f'Bot is no longer muted.')


    @commands.command()
    async def open(self, ctx: commands.Context, *, full_message='default'):
        # Check mod status, check for an existing PlayerQueue object and create if necessary
        # Execute method to open queue and send notification to chat.
        if not ctx.author.is_mod:
            await ctx.send(active_channels[ctx.channel.name].speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}.')
            return

        if active_channels[ctx.channel.name].queue_open:
            await ctx.send(active_channels[ctx.channel.name].speak(f'The {full_message} queue is already open.'))
            print(f'The {full_message} queue is already open.')
            return

        active_channels[ctx.channel.name].close_queue()
        active_channels[ctx.channel.name].open_queue(full_message)
        await ctx.send(active_channels[ctx.channel.name].speak(f'The {full_message} queue is now open!'))
        print(f'The {full_message} queue is now open!')

    @commands.command()
    async def close(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            await ctx.send(active_channels[ctx.channel.name].speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}.')
            return
        active_channels[ctx.channel.name].close_queue()
        await ctx.send(active_channels[ctx.channel.name].speak(f'The queue is now closed!'))
        print(f'The queue is now closed!')


    @commands.command()
    async def join(self, ctx: commands.Context):
        if not active_channels[ctx.channel.name].queue_open:
            await ctx.send(active_channels[ctx.channel.name].speak(f'The queue is closed.'))
            print(f'The queue is closed.')
            return

        if ctx.author.name in active_channels[ctx.channel.name].current_queue:
            await ctx.send(active_channels[ctx.channel.name].speak(f'You are already in the queue, {ctx.author.name}'))
            print(f'You are already in the queue, {ctx.author.name}')
            return

        try:
            if not active_channels[ctx.channel.name].current_roster[ctx.author.name]['eligible']:
                await ctx.send(active_channels[ctx.channel.name].speak(f'You have already played, {ctx.author.name}'))
                print(f'You have already played, {ctx.author.name}')
                return
        except KeyError:
            print(f'{ctx.author.name} was not found in roster.')

        active_channels[ctx.channel.name].join_queue(ctx.author.name)
        await ctx.send(active_channels[ctx.channel.name].speak(f'You are added to the queue, {ctx.author.name}'))
        print(f'You are added to the queue, {ctx.author.name}')


    @commands.command()
    async def leave(self, ctx: commands.Context):
        active_channels[ctx.channel.name].leave_queue(ctx.author.name)
        await ctx.send(active_channels[ctx.channel.name].speak(f'You are removed from the queue, {ctx.author.name}'))
        print(f'You are removed from the queue, {ctx.author.name}')

    @commands.command()
    async def position(self, ctx: commands.Context):
        await ctx.send(active_channels[ctx.channel.name].speak(f'{ctx.author.name}, you are number {active_channels[ctx.channel.name].current_queue.index(ctx.author.name) + 1} in queue.'))
        print(f'{ctx.author.name}, you are number {active_channels[ctx.channel.name].current_queue.index(ctx.author.name) + 1} in queue.')

    @commands.command()
    async def length(self, ctx: commands.Context):
        await ctx.send(active_channels[ctx.channel.name].speak(f'The queue has {len(active_channels[ctx.channel.name].current_queue)} players in it.'))
        print(f'The queue has {len(active_channels[ctx.channel.name].current_queue)} players in it.')

    @commands.command()
    async def next(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            await ctx.send(active_channels[ctx.channel.name].speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}')
            return
        active_channels[ctx.channel.name].next_player()
        sheet_instance.clear()
        sheet_instance.append_rows([[active_channels[ctx.channel.name].current_player]])
        sheet_instance.append_rows(doc_list(active_channels[ctx.channel.name].current_queue))

    @commands.command()
    async def list(self, ctx: commands.Context):
        await ctx.send(active_channels[ctx.channel.name].speak(f'{ctx.channel.name} is currently fighting {active_channels[ctx.channel.name].current_player}!  Next 5 up are: {", ".join(active_channels[ctx.channel.name].current_queue[:5])} '))
        print(f'{ctx.channel.name} is currently fighting {active_channels[ctx.channel.name].current_player}!  Next 5 up are: {", ".join(active_channels[ctx.channel.name].current_queue[:5])} ')

    @commands.command()
    async def clear(self, ctx: commands.Context):
        if not ctx.author.is_mod:
            await ctx.send(active_channels[ctx.channel.name].speak(f'You are not a moderator, {ctx.author.name}'))
            print(f'You are not a moderator, {ctx.author.name}')
            return        
        active_channels[ctx.channel.name].clear_queue()
        await ctx.send(active_channels[ctx.channel.name].speak(f'The {active_channels[ctx.channel.name].queue_name} queue has been cleared.'))
        print(f'The {active_channels[ctx.channel.name].queue_name} queue has been cleared.')
        sheet_instance.clear()

    @commands.command()
    async def reset(self, ctx: commands.Context,):
        active_channels[ctx.channel.name].reset()
        await ctx.send(active_channels[ctx.channel.name].speak(f'The queue {active_channels[ctx.channel.name].queue_name} has been reset.'))
        print(f'The queue {active_channels[ctx.channel.name].queue_name} has been reset.')

    @commands.command()
    async def qselect(self, ctx: commands.Context, *, full_message):
        active_channels[ctx.channel.name].change_queue(full_message)
        await ctx.send(active_channels[ctx.channel.name].speak(f'Queue {active_channels[ctx.channel.name].queue_name} has been selected.'))


    

###### TO DO
#refactor google sheets to use self sheet instance per channel instance and make it less shit




bot = Bot()
bot.run()
