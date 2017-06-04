import discord
from discord.ext import commands
import asyncio
import collections
import re
import copy

try:
    import youtube_dl
except:
    youtube_dl = None

try:
    if not discord.opus.is_loaded():
        discord.opus.load_opus('libopus-0.dll')
except OSError:  # Incorrect bitness
    opus = False
except:  # Missing opus
    opus = None
else:
    opus = True

description = '''A bot to stream music.'''
bot = commands.Bot(command_prefix='!', description=description)


# -----------------
#    CONSTANTES
# -----------------
YT_DL_OPTIONS = {
    'source_address': '0.0.0.0',
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': "mp3",
    'outtmpl': '%(id)s',
    'noplaylist': False,
    'yesplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
    'outtmpl': "data/audio/cache/%(id)s",
    'default_search': 'auto'
}

# -----------------
#      CLASSES
# -----------------
class Song:
    def __init__(self, **kwargs):
        self.__dict__ = kwargs
        self.title = kwargs.pop('title', None)
        self.id = kwargs.pop('id', None)
        self.url = kwargs.pop('webpage_url', None)
        self.duration = kwargs.pop('duration', 60)

class Deque(collections.deque):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def peek(self):
        if self:
            song = self.pop()
            self.append(song)
            return copy.deepcopy(song)
        return False

# -----------------
#     GLOBALS
# -----------------
my_playlist = Deque()
current_song = None
client = discord.Client()
player = None;
stop_demand = False
voice = None
current_volume = 1.0;
paused = False;

# -----------------
#     ERRORS
# -----------------

error_unreadable_video = ":exclamation: Cette vidéo n'existe pas (plus) OU a été bloquée pour des raisons de droits d'auteur."
error_empty_playlist = ":exclamation: La playlist est vide."
error_not_playing = ":exclamation: Aucune musique en cours."

# -----------------
#    DISCORD.PY
# -----------------
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command(pass_context=True)
async def addsong(ctx, url : str):
    """Add the song specified by url into the playlist."""
    if is_valid_yt_url(url):
        info = await get_song_info(url)
        if info:
            if info['extractor_key'] == 'Youtube':
                await add_song_to_playlist(info, ctx.message.channel)
            elif info['extractor_key'] == 'YoutubePlaylist':
                await bot.say(':recycle: Chargement de la playlist...')
                print(info['entries'])
                for song in info['entries']:
                    url = f"https://www.youtube.com/watch?v={song['url']}"
                    print(url)
                    info = await get_song_info(url)
                    if info:
                        await add_song_to_playlist(info, ctx.message.channel)
                    else:
                        await bot.say(error_unreadable_video)
                await bot.say(':white_check_mark: Playlist chargée.')
        else:
            await bot.say(error_unreadable_video)
    else:
        await bot.say(':exclamation: Ceci n\'est pas un lien valide...')


@bot.command()
async def playlist():
    """Display the current content of the playlist."""
    count = 0
    for song in reversed(my_playlist):
        song_title = song.title
        song_duration = song.duration
        song_url = song.url
        count += 1
        hms = hms_to_string(seconds_to_hms(song.duration))
        await bot.say(f"{count}. {song_title} :clock10: {hms}")
    if count == 0:
        await bot.say(error_empty_playlist)


@bot.command(pass_context=True)
async def play(ctx):
    """Join the caller voice channel and start playing the songs in the playlist."""
    global current_song
    global player
    global stop_demand
    global voice

    server = ctx.message.server
    author = ctx.message.author
    voice_channel = author.voice_channel

    if current_song is None:
        if my_playlist:

            # Envoie du bot dans le channel de author
            tmp_voice = await _join_voice_channel(voice_channel)

            # If the bot is not already in the given voice channel
            if tmp_voice != False:
                voice = tmp_voice

            await bot.say(':arrow_forward: Début de la lecture.')

            while my_playlist and not stop_demand:
                print("Lis un morceau")
                current_song = my_playlist.pop()

                beforeArgs = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

                player = await voice.create_ytdl_player(current_song.url, ytdl_options=YT_DL_OPTIONS, before_options=beforeArgs)
                player.volume = current_volume
                player.start()
                
                await display_song_playing_info(ctx.message.channel)

                # TODO: Attente passive
                while not player.is_done():
                    await asyncio.sleep(1) # Attend tant que la musique en cours n'est pas finie

            if not stop_demand:
                await bot.say(':white_check_mark: La playlist est terminée.')
            stop_demand = False
            current_song = None
            set_paused(False)
        else:
            await bot.say(error_empty_playlist)
    else:
        await bot.say(':exclamation: Musique déjà en cours.')


@bot.command(pass_context=True)
async def peek(ctx):
    """Display info about the next song in the playlist."""
    if my_playlist:
        await display_next_song_info(ctx.message.channel);
    else:
        await bot.say(error_empty_playlist)


@bot.command(pass_context=True)
async def song(ctx):
    """Display info about the song currently playing."""
    if not current_song is None:
        await display_song_playing_info(ctx.message.channel)
    else:
        await bot.say(error_not_playing)


@bot.command()
async def pause():
    """Enable pause mode which pauses the lecture of the current song and the playlist."""
    if not current_song is None:
        if not paused:
            set_paused(True)
            player.pause();
            await bot.say(":pause_button: Lecture mise en pause. (Reprendre la lecture avec !resume)")
        else:
            await bot.say(":exclamation: Lecture déjà en pause.")
    else:
        await bot.say(error_not_playing)

@bot.command()
async def resume():
    """Disable pause mode which continues the reading of the current song and the playlist."""
    if not current_song is None:
        if paused:
            set_paused(False)
            player.resume();
            await bot.say(":arrow_forward: Reprise de la lecture.")
        else:
            await bot.say(":exclamation: La lecture est déjà en cours.")
    else:
        await bot.say(error_not_playing)

@bot.command()
async def next():
    """Stop the current song and play the next one in the playlist."""
    if not current_song is None:
        player.stop(); # Stop the current song
        await bot.say(":track_next: Passage au morceau suivant.")
    else:
        await bot.say(error_not_playing)


@bot.command()
async def stop():
    """Stop completly the reading of the current song and the playlist."""
    # Stop the player completly
    global stop_demand
    if not current_song is None:
        stop_demand = True
        my_playlist.append(current_song) # Put back on top of the playlist the song playing when stopped
        player.stop();
        await bot.say(":stop_button: Lecture stoppée. (Reprendre la lecture avec !play)")
    else:
        await bot.say(error_not_playing)


@bot.command()
async def clear():
    """Clear the playlist."""
    my_playlist.clear()
    await bot.say(":grey_exclamation: La playlist a été vidée.")


@bot.command()
async def dellast():
    """Remove the last song added to the playlist from it."""
    del_song = my_playlist.popleft()
    song_title = del_song.title
    await bot.say(f":grey_exclamation: {song_title} [Retiré de la playlist]" )


@bot.command(pass_context=True)
async def volume(ctx):
    """Change volume of the bot stream."""
    arg = ctx.message.content.split()
    if(len(arg) > 1):
        await set_volume(arg[1], ctx.message.channel)
    else:
        await display_volume(ctx.message.channel)
        
@bot.command()
async def helpbot():
    """Display help for the bot's commands""" 
    help = '-  **!help** : Display help about the bot’s commands\n'\
    '-  **!addsong [YT URL]** : Add a song or songs from a playlist to the'\
    'bot’s queue. Only argument is YouTube URL of your song/playlist.\n'\
    '-  **!playlist** : Display the current playlist of the bot.\n'\
    '-  **!play** : Start reading the songs in the playlist (you must be in a'\
    'voice channel!)\n'\
    '-  **!peek** : Display information about the next song.\n'\
    '-  **!song** : Display information about the current song.\n'\
    '-  **!next** : Skip the current song and start reading the next one.\n'\
    '-  **!pause** : Pause the reading.\n'\
    '-  **!resume** : Resume the reading.\n'\
    '-  **!stop** : Stop completly the lecture.\n'\
    '-  **!clear** : Empty the playlist.\n'\
    '-  **!dellast** : Delete the last song added to the playlist.\n'\
    '-  **!volume [number]** : When called without arguments only display the'\
    'current volume, when you specify a number (between 0 - 200) adjust'\
    'the current volume.\n'
    await bot.say(help)

# -----------------
#     METHODES
# -----------------
async def display_next_song_info(channel):
    """Display information of the next song to come."""
    peeked_song = my_playlist.peek()
    if peeked_song:
        song_title = peeked_song.title
        await bot.send_message(channel, f":track_next: Prochain morceau : {song_title}")
    else:
        await bot.send_message(channel, ":track_next: Prochain morceau : Y'a plus rien après wesh!")

async def display_song_playing_info(channel):
    """Display info from the song playing currently and the next one to come."""
    song_title = current_song.title
    hms = hms_to_string(seconds_to_hms(current_song.duration))
    await bot.send_message(channel, f":musical_note: Ecoute : {song_title} :clock10: {hms}")
    await display_next_song_info(channel);

async def get_song_info(url):
    """Return song object with details from url video."""
    yt = youtube_dl.YoutubeDL(YT_DL_OPTIONS)
    return yt.extract_info(url, download=False, process=False)

def is_valid_yt_url(url):
    """Verify if url is a valid YouTube link."""
    yt_link = re.compile(r'^(https?\:\/\/)?(www\.|m\.)?(youtube\.com|youtu\.?be)\/.+$') # C'est pas nous qui l'avons fait...
    return yt_link.match(url)

async def _join_voice_channel(channel):
    """The bot joins the given audio channel."""
    # Pour l'instant on admet un usage sur un seul voice channel à la fois

    for voice in bot.voice_clients:
        if voice.channel.id == channel.id:
            print("Already in that voice channel")
            return False

    voice = await bot.join_voice_channel(channel)
    print("Connection to a voice channel")
    return voice

async def display_volume(channel):
    """Display the current player volume."""
    await bot.send_message(channel, f":speaker: Volume à {current_volume * 100:.0f}%" )

async def set_volume(val, channel):
    """Set the new volume to val."""
    global current_volume
    try:
        val = int(val)
    except ValueError:
        print("That's not an int!")
    if 0 <= val <=200:
        current_volume = val/100.
        if player:
            player.volume = current_volume
        await display_volume(channel)
    else:
        await bot.send_message(channel, ":exclamation: Le volume doit être compris entre 0 et 200." )

async def add_song_to_playlist(info, channel):
    """Add a song into the playlist."""
    if check_duration(info['duration']):
        new_song = Song(**info)
        my_playlist.appendleft(new_song)
        title = new_song.title
        hms = hms_to_string(seconds_to_hms(new_song.duration))
        await bot.send_message(channel, f":notes: Nouvelle entrée : {title}. :clock10: {hms}")
    else:
        await bot.send_message(channel, ":exclamation: La durée d'un morceau ne doit pas excéder 10 minutes.")

def seconds_to_hms(seconds):
    """Convert given seconds into hms."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return(h, m, s)

def hms_to_string(hms):
    """Convert hms into a string."""
    h = ""
    m = ""
    s = ""
    if hms[0] != 0:
        h = str(hms[0]) + "h "
    if hms[1] != 0:
        m = str(hms[1]) + "mn "
    if hms[2] != 0:
        s = str(hms[2]) + "s"

    return h + m + s

def check_duration(duration):
    """Check the duration given in arg."""
    return duration <= 600 # 10 minutes


def get_token():
    """Get the bot token from text file."""
    file = open("token.txt", "r")
    return file.read()

def set_paused(bool):
    """Set the state of the pause."""
    global paused
    paused = bool

bot.run(get_token())
