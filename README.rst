DiscoBot
========

A Simple Musical Bot for Discord. (Work in progress)

Getting Started
---------------

Requirements
~~~~~~~~~~~~

For Python
^^^^^^^^^^

::

    $ pip install -r requirements.txt

FFMPEG
^^^^^^

1. Download this folder : `ffmpeg v3.3.1 win64`_
2. Find **ffmpeg.exe** inside the downloaded folder (into bin folder).
3. Put the exe where you want and **add it to your PATH**.

Installing
~~~~~~~~~~

1. Do what is listed above.
2. Create a simple text file next to **disco-bot.py** (at the root of
   your installation folder) and **insert your bot token** in the first
   row.

Running
-------

Run disco-bot.py

::

    python disco-bot.py

How to use it ?
---------------

Once your bot is online on your server you can use a list of commands
that start with **!**. Some of them require you to be in a voice channel
in order to work (like !play).

-  **!helpbot** : Display help about the bot’s commands
-  **!addsong [YT URL]** : Add a song or songs from a playlist to the
   bot’s queue. Only argument is YouTube URL of your song/playlist.
-  **!playlist** : Display the current playlist of the bot.
-  **!play** : Start reading the songs in the playlist (you must be in a
   voice channel!)
-  **!peek** : Display information about the next song.
-  **!song** : Display information about the current song.
-  **!next** : Skip the current song and start reading the next one.
-  **!pause** : Pause the reading.
-  **!resume** : Resume the reading.
-  **!stop** : Stop completly the lecture.
-  **!clear** : Empty the playlist.
-  **!dellast** : Delete the last song added to the playlist.
-  **!volume [number]** : When called without arguments only display the
   current volume, when you specify a number (between 0 - 200) adjust
   the current volume.

Authors
-------

-  **Anthony Fleury** - `Staminah`_
-  **Christpohe Hirschi** - `ChrisHirs`_

Bibliography
------------

-  `discord.py`_
-  `Youtube-DL`_
-  `Discord API Reference`_
-  `FFMPEG files`_
-  `RedBot`_

.. _ffmpeg v3.3.1 win64: http://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-3.3.1-win64-static.zip
.. _Staminah: https://github.com/Staminah
.. _ChrisHirs: https://github.com/ChrisHirs
.. _discord.py: https://github.com/Rapptz/discord.py
.. _Youtube-DL: https://github.com/rg3/youtube-dl
.. _Discord API Reference: http://discordpy.readthedocs.io/en/latest/api.html
.. _FFMPEG files: https://ffmpeg.zeranoe.com/builds/
.. _RedBot: https://github.com/Twentysix26/Red-DiscordBot
