# Versus-Viewers
Twitch chat bot for managing viewer player queues.

Works in multiple channels at once with separate queue objects.


Parity bot is version to run alongside pejter's bot.
Versus bot (if present) is unrestricted development.
versusviewers is the class definition for the queue manager object.

heavily utilizes twitchio.  google sheet integration requires gspread.

## Quick Start

* Download everything.
* Install python if needed from https://www.python.org/downloads/
* Go to www.twitchtokengenerator.com and connect to your bot account.  save client key in a file in the directory with the script called token.txt
* run the bot in the command line using the following format: py scriptname.py [command prefix] [any number of channels separated by spaces]
* example launch command: `py parity_bot.py ! avaren letsdaze_` will join the bot to twitch channel avaren and letsdaze_ with the command prefix !




## Functionality

versus-viewers creates separate queue objects for each twitch channel it is joined to.  It saves both queue members and a roster file (anyone who has joined that queue) as human readable json files in directory ./queues/ with a file for each queue.

vv uses a config file to load the twitch chat user auth token for the account that is joining the chats (your bot account).  I recommend www.twitchtokengenerator.com for this.

vv updates a google sheet with the current active queue members every !next command.  currently not customizable.


# Commands

## Normal Chatter Commands

- **!join** joins the active queue.
- **!leave** leaves the active queue.
- **!position** reports user's position the active queue.
- **!length** reports the length of the queue.
- **!list** gives the top 5 names in queue.
- **!queue** reports the name and status of the active queue.
- **!queuedoc** provides the link to the google doc queue readout.
- **!troy** woof


## Moderator Commands

- **!select** (queuename) selects a queue as the active queue.
    - Creates the queue then selects it if it doesn't currently exist.
- **!open** opens the active queue for players to join.
- **!close** closes the active queue.
- **!clear** clears the active queue.
- **!reset** resets all players eligibility for the active queue.
- **!next** advances the queue and announces who is now playing, and who is on deck.
- **!botmutetoggle** toggles the bot between muted and unmuted.  While muted, the bot still processes commands as normal but does not chat to twitch.




# To Do:

Separate google sheet selection per instance.
Prettify and add more info to sheet. (learn more pandas?)
create documentation for creating google drive API service account and connecting to the sheet

Handle more errors when methods fail due to index/name/etc errors (trying !next on an empty queue, etc)

research and create requirements.txt

add config file functionality for easier customization of google doc, bot's messages

reposition code for more logical readability and COMMENT EVERYTHING
