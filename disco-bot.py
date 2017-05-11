import discord
import asyncio
import collections
import re
import youtube_dl

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
        self.url = kwargs.pop('url', None)
        self.webpage_url = kwargs.pop('webpage_url', "")
        self.duration = kwargs.pop('duration', 60)

class Deque(collections.deque):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def peek(self):
            ret = self.pop()
            self.append(ret)
            return copy.deepcopy(ret)

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
            playlist.append(new_song)
            await client.send_message(message.channel, 'Nouvelle entrée : '+new_song.title)
        else:
            await client.send_message(message.channel, 'Ceci n\'est pas un lien valide...')
    elif message.content.startswith('!playlist'):
        count = 0
        for song in playlist:
            song_title = song.title
            song_duration  =song.duration
            count += 1
            await client.send_message(message.channel, f"{count}. {song_title} - {song_duration} secondes")

# -----------------
#     METHODES
# -----------------
def get_song_info(url):
    """Returns Song object with details from url video"""
    yt = youtube_dl.YoutubeDL(YT_DL_OPTIONS)
    video = yt.extract_info(url, download=False, process=False)
    return Song(**video)

def is_valid_yt_url(url):
    """Verify if url is a valid YouTube link"""
    yt_link = re.compile(r'^(https?\:\/\/)?(www\.|m\.)?(youtube\.com|youtu\.?be)\/.+$') # C'est pas nous qui l'avons fait...
    if yt_link.match(url):
        return True
    return False

client.run('MzEyMTQ3MjIyOTExMzg1NjAw.C_W1RQ.P200q2IQJvwy7XHUolMbjzL1h3o')
