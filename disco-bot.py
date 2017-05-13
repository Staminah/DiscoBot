import discord
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
player = None;
stop_demand = False
voice = None

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
            await client.send_message(message.channel, ':notes: Nouvelle entrée : '+ new_song.title + '. :clock10: ' + hms_to_string(seconds_to_hms(new_song.duration)))
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
            hms = hms_to_string(seconds_to_hms(song.duration))
            await client.send_message(message.channel, f"{count}. {song_title} - {hms}")
        if count == 0:
            await client.send_message(message.channel, ":exclamation: La playlist est vide")
    elif message.content.startswith('!play'):
        await play(message)
    elif message.content.startswith('!peek'):
        await peek(message.channel);
    elif message.content.startswith('!pause'):
        player.pause();   
        await client.send_message(message.channel, ":pause_button: Lecture mise en pause. (Reprendre la lecture avec !resume)")
    elif message.content.startswith('!resume'):
        player.resume(); 
        await client.send_message(message.channel, ":arrow_forward: Reprise de la lecture")
    elif message.content.startswith('!next'):
        player.stop(); #Stop the current song
        await client.send_message(message.channel, ":track_next: Passage au morceau suivant")
    elif message.content.startswith('!stop'):
        stop() #Stop the player completly
        await client.send_message(message.channel, ":stop_button: Lecture stoppée. (Reprendre la lecture avec !play)")
    elif message.content.startswith('!clear'):
        playlist.clear()
        await client.send_message(message.channel, ":grey_exclamation: La playlist a été vidée.")
    elif message.content.startswith('!dellast'):
        del_song = playlist.popleft()
        song_title = del_song.title
        await client.send_message(message.channel, ":grey_exclamation: " + song_title + " [Retiré de la playlist]" )   
# -----------------
#     METHODES
# -----------------
def stop():
    """Stop completly the music"""
    global stop_demand
    stop_demand = True
    playlist.append(current_song) #Put back on top of the playlist the song playing when stopped
    player.stop();

async def play(message):
    """Plays songs."""
    global current_song
    global player
    global stop_demand
    global voice

    server = message.server
    author = message.author
    voice_channel = author.voice_channel
    #Envoie du bot dans le channel de author
    tmp_voice = await _join_voice_channel(voice_channel)
    
    #If the bot is not already in the given voice channel
    if tmp_voice != False:
        voice = tmp_voice

    if current_song is None:
        if playlist:
            await client.send_message(message.channel, ':arrow_forward: Début de la lecture') 
            while playlist and not stop_demand:
                print("Lis un morceau")
                current_song = playlist.pop()

                player = await voice.create_ytdl_player(current_song.url, ytdl_options=YT_DL_OPTIONS)
                player.start()
				
                await display_song_playing_info(message.channel)
                
                while not player.is_done():
                    await asyncio.sleep(1) # attend tant que la musique en cours n'est pas finie 

            if not stop_demand:
                await client.send_message(message.channel, ':white_check_mark: La playlist est terminée')
            stop_demand = False
            current_song = None
        else:
            await client.send_message(message.channel, ':exclamation: La playlist est vide')
    else:
        await client.send_message(message.channel, ':exclamation: Musique déjà en cours')

async def peek(channel):
    """Display information of the next song to come"""
    peeked_song = playlist.peek()
    if peeked_song:
        song_title = peeked_song.title
        await client.send_message(channel, f":track_next: Prochain morceau : {song_title}")
    else:
        await client.send_message(channel, ":track_next: Prochain morceau : Y'a plus rien après wesh")

async def display_song_playing_info(channel):
    """Display info from the song playing currently and the next song to come"""
    song_title = current_song.title
    hms = hms_to_string(seconds_to_hms(current_song.duration))
    await client.send_message(channel, f":musical_note: Ecoute : {song_title} - {hms}")
    await peek(channel);
        
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
	
async def _join_voice_channel(channel):
    """The Bot join the given audio channel"""
    #Pour l'instant on admet un usage sur un seul voice channel à la fois
    
    for voice in client.voice_clients:      
        if voice.channel.id == channel.id:
            print("Already in that voice channel")
            return False
    
    voice = await client.join_voice_channel(channel)
    print("Connection to a voice channel")
    return voice

def seconds_to_hms(seconds):
    """Convert given seconds into hms"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return(h, m, s)
    
def hms_to_string(hms):
    """Convert hms into a string"""
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


client.run('token')
