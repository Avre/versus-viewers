import json

from twitchio.rewards import CustomRewardRedemption

active_queues = {}

class PlayerQueue():
    def __init__(self, streamer_name, queue_name='default'):
        self.streamer_name = streamer_name
        self.queue_open = False
        self.roster_file = str(f'{streamer_name}_{queue_name.replace(" ", "-")}_roster.json')
        self.queue_file = str(f'{streamer_name}_{queue_name.replace(" ", "-")}_queue.json')
        self.queue_name = queue_name
        self.current_roster = {}
        self.current_queue = []
        self.current_player = ''
        self.muted = True
    
    def speak(self, string):
        if self.muted:
            return ''
        else:
            return string

    def load_roster(self):
        try:
            with open(self.roster_file,'r') as roster_file:
                self.current_roster = json.load(roster_file)
        except FileNotFoundError:
            print('No roster file exists.')

    
    def save_roster(self):
        with open(self.roster_file,'w') as roster_file:
            json.dump(self.current_roster, roster_file, indent = 4 )


    def load_queue(self):
        try:
            with open(self.queue_file,'r') as queue_file:
                self.current_queue = json.load(queue_file)
        except FileNotFoundError:
            print('No roster file exists.')

    
    def save_queue(self):
        with open(self.queue_file,'w') as queue_file:
            json.dump(self.current_queue, queue_file, indent = 4 )


    def roster_add(self, player_name):
        self.current_roster[player_name] = {}
        self.current_roster[player_name]['name'] = player_name
        self.current_roster[player_name]['eligible'] = True


    def open_queue(self, queue_name):
        self.queue_open = True
        self.queue_name = queue_name
        self.queue_file = str(f'{self.streamer_name}_{queue_name.replace(" ", "-")}_queue.json')
        self.roster_file = str(f'{self.streamer_name}_{queue_name.replace(" ", "-")}_roster.json')
        self.load_queue()
        self.load_roster()


    def join_queue(self, player_name):
        if player_name not in self.current_roster:
            self.roster_add(player_name)
        self.current_queue.append(player_name)


    def leave_queue(self, player_name):
        self.current_queue.remove(player_name)


    def next_player(self):
        self.current_player = self.current_queue.pop(0)
        self.current_roster[self.current_player]['eligible'] = False
        self.save_queue()

    
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
        self.roster_file = str(f'{self.streamer_name}_{queue_name.replace(" ", "-")}_roster.json')
        self.queue_file = str(f'{self.streamer_name}_{queue_name.replace(" ", "-")}_queue.json')
        self.load_roster()
        self.load_queue()
        self.queue_open = False
