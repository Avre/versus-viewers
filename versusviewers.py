import json
import os

class PlayerQueue():
    def __init__(self, streamer_name, queue_name='default'):
        self.streamer_name = streamer_name
        self.queue_open = False
        self.streamer_subdir = str(f'.{os.sep}queues{os.sep}{streamer_name}{os.sep}')
        self.roster_file = str(f'{self.streamer_subdir}{streamer_name}_{queue_name.replace(" ", "-")}_roster.json'.lower())
        self.queue_file = str(f'{self.streamer_subdir}{streamer_name}_{queue_name.replace(" ", "-")}_queue.json'.lower())
        self.queue_name = queue_name
        self.current_roster = {}
        self.current_queue = []
        self.current_player = ''
        self.muted = True

    def length_bark(self, handler):
        #What to say when
        return f'The {handler.queue_name} queue has {len(handler.current_queue)} players in it.'

    def mod_bark(self, author):
        #What to say when a non-mod tries to do mod shit
        return f'You are not a moderator, {author}'
    
    def speak(self, string):
        if self.muted:
            return ''
        else:
            return string

    def create(self, queue_name = 'default'):
        new_roster_file = str(f'{self.streamer_subdir}{self.streamer_name}_{queue_name.replace(" ", "-")}_roster.json'.lower())
        new_queue_file = str(f'{self.streamer_subdir}{self.streamer_name}_{queue_name.replace(" ", "-")}_queue.json'.lower())
        with open(new_roster_file,'w') as roster_file:
            json.dump(dict(), roster_file, indent = 4)
        with open(new_queue_file,'w') as queue_file:
            json.dump(list(), queue_file, indent = 4)

    def load(self, queue_name = 'default'):
        self.roster_file = str(f'{self.streamer_subdir}{self.streamer_name}_{queue_name.replace(" ", "-")}_roster.json'.lower())
        self.queue_file = str(f'{self.streamer_subdir}{self.streamer_name}_{queue_name.replace(" ", "-")}_queue.json'.lower())
        self.load_roster()
        self.load_queue()
        self.queue_name = queue_name

    def save(self):
        self.save_queue()
        self.save_roster()

    def load_roster(self):
        self.current_roster = {}
        try:
            with open(self.roster_file,'r') as roster_file:
                self.current_roster = json.load(roster_file)
        except FileNotFoundError:
            print('error: no roster file exists.')

    
    def save_roster(self):
        with open(self.roster_file,'w') as roster_file:
            json.dump(self.current_roster, roster_file, indent = 4 )


    def load_queue(self):
        self.current_queue = []
        try:
            with open(self.queue_file,'r') as queue_file:
                self.current_queue = json.load(queue_file)
        except FileNotFoundError:
            print('error: no queue file exists')

    
    def save_queue(self):
        with open(self.queue_file,'w') as queue_file:
            json.dump(self.current_queue, queue_file, indent = 4 )


    def roster_add(self, player_name):
        self.current_roster[player_name] = {}
        self.current_roster[player_name]['name'] = player_name
        self.current_roster[player_name]['eligible'] = True


    def open_queue(self, queue_name = 'default'):
        self.queue_open = True
        self.queue_name = queue_name
        self.queue_file = str(f'{self.streamer_subdir}{self.streamer_name}_{queue_name.replace(" ", "-")}_queue.json'.lower())
        self.roster_file = str(f'{self.streamer_subdir}{self.streamer_name}_{queue_name.replace(" ", "-")}_roster.json'.lower())
        self.load_queue()
        self.load_roster()


    def join_queue(self, player_name):
        if player_name not in self.current_roster:
            self.roster_add(player_name)
        self.current_queue.append(player_name)


    def leave_queue(self, player_name):
        self.current_queue.remove(player_name)


    def next_player(self):
        try:
            self.current_player = self.current_queue.pop(0)
            self.current_roster[self.current_player]['eligible'] = False
            self.save_queue()
        except IndexError:
            print('error: queue list is empty')
            return


    
    def clear_queue(self):
        self.current_queue = []
        self.save_queue()

    def close_queue(self):
        self.save_queue()
        self.save_roster()
        self.queue_open = False

    def reset(self):
        for playername in self.current_roster:
            self.current_roster[playername]['eligible'] = True
        self.save_roster()

    def change_queue(self, queue_name):
        self.save_roster()
        self.save_queue()
        self.queue_name = queue_name
        self.roster_file = str(f'{self.streamer_subdir}{self.streamer_name}_{queue_name.replace(" ", "-")}_roster.json'.lower())
        self.queue_file = str(f'{self.streamer_subdir}{self.streamer_name}_{queue_name.replace(" ", "-")}_queue.json'.lower())
        self.load_roster()
        self.load_queue()
