import discord
import asyncio
import collections
import re
import youtube_dl
import copy

# -----------------
#    CONSTANTES
# -----------------
YT_DL_OPTIONS = {
    'source_address': '0.0.0.0',
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': "mp3",
    'outtmpl': '%(id)s',
    'noplaylist': True,
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
playlist = Deque()
current_song = None
client = discord.Client()

# -----------------
#    DISCORD.PY
# -----------------
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.content.startswith('!add song'):
        url = message.content.split()[2]
        if is_valid_yt_url(url):
            new_song = get_song_info(url)
            playlist.appendleft(new_song)
            hms = seconds_to_hms(new_song.duration)
            await client.send_message(message.channel, ':notes: Nouvelle entrée : '+ new_song.title + '. Durée : ' + str(hms[0]) + ':' + str(hms[1]) + ':' + str(hms[2]))
        else:
            await client.send_message(message.channel, ':exclamation: Ceci n\'est pas un lien valide...')
    elif message.content.startswith('!playlist'):
        count = 0
        reversed_playlist = playlist.copy()
        reversed_playlist.reverse()
        for song in reversed_playlist:
            song_title = song.title
            song_duration = song.duration
            song_url = song.url
            count += 1
            await client.send_message(message.channel, f"{count}. {song_title} - {song_duration} secondes")
        if count == 0:
            await client.send_message(message.channel, ":exclamation: La playlist est vide")
    elif message.content.startswith('!play'):
        await play(message)
    elif message.content.startswith('!peek'):
        await peek(message);

# -----------------
#     METHODES
# -----------------
async def play(message):
    """Plays songs."""
    global current_song
    if current_song is None:
        if playlist:
            while playlist:
                current_song = playlist.pop()
                song_title = current_song.title
                song_url = current_song.url
                song_duration = current_song.duration

                # TODO: Lancer la musique
                await client.send_message(message.channel, f":musical_note: Ecoute : {song_title}")
                await peek(message);
                await asyncio.sleep(song_duration) # en secondes
            current_song = None
            await client.send_message(message.channel, ':white_check_mark: La playlist est terminée')
        else:
            await client.send_message(message.channel, ':exclamation: La playlist est vide')
    else:
        await client.send_message(message.channel, ':exclamation: Musique déjà en cours')

async def peek(message):
    peeked_song = playlist.peek()
    if peeked_song:
        song_title = peeked_song.title
        await client.send_message(message.channel, f":track_next: Prochain morceau : {song_title}")
    else:
        await client.send_message(message.channel, ":track_next: Prochain morceau : Y'a plus rien après wesh")

def get_song_info(url):
    """Returns Song object with details from url video."""
    yt = youtube_dl.YoutubeDL(YT_DL_OPTIONS)
    video = yt.extract_info(url, download=False, process=False)
    return Song(**video)

def is_valid_yt_url(url):
    """Verify if url is a valid YouTube link."""
    yt_link = re.compile(r'^(https?\:\/\/)?(www\.|m\.)?(youtube\.com|youtu\.?be)\/.+$') # C'est pas nous qui l'avons fait...
    if yt_link.match(url):
        return True
    return False

def seconds_to_hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return(h, m, s)

client.run('MzEyMTQ3MjIyOTExMzg1NjAw.C_W1RQ.P200q2IQJvwy7XHUolMbjzL1h3o')
