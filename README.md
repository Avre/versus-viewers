# versus-viewers
Twitch chat bot for managing viewer player queues
Works in multiple channels at once with separate queue objects.


Parity bot is version to run alongside pejter's bot.
Versus bot (if present) is unrestricted development.
versusviewers is the class definition for the queue manager object.

heavily utilizes twitchio.  google sheet integration requires gspread.


To Do:

Separate google sheet selection per instance.
Prettify and add more info to sheet. (learn more pandas)

Handle more errors when methods fail due to index/name/etc errors (trying !next on an empty queue, etc)

Make this actually real documentation
