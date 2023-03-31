import discord
from discord.ext import commands

from youtube_dl import YoutubeDL



class music_cog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        
        self.is_playing = False
        self.is_paused = False
        
        self.music_queue = []
        self.YDL_OPTIONS = {'fomat': 'bestaudio','noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        
        self.vc = None
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item,download = False) ['entries'][0]
            except Exception:
                return False
        return {'source':info['formats'[0]['url']], 'title':info['title']}
    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']
            self.music_queue.pop(0)
            self.vc.play_music(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
    
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']
            
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()
                
                if self.vc == None:
                    await ctx.send("Could not connect to the Voice Channel")
                    return
                else:
                    await self.vc.move_to(self.music_queue[0][1])
                self.music_queue.pop(0)
                
                self.vc.play_music(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
    
    @commands.command(name="play", aliaes=["p", "playing"], help="Play the selected song from YouTube")
    async def play(self, ctx, **args):
        query = "".join(args)
        
        voice_channel = ctx.author.voice_channel
        if voice_channel is None:
            await ctx.send("Connecting to a Voice Channel")        
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format, try a different keyword")
            else:
                await ctx.send("Song added to the queue")
                self.music_queue.append([song, voice_channel])
                
                if self.is_playing == False:
                    await self.play_music(ctx) 
    @commands.command(name="paused", help="Pauses the current song being played")
    async def pause(self, ctx,**args):
        if self.is_playing:
            self.is_playing = False
            self.is_playing = True
            self.vc.pause()
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
    @commands.command(name="resume", aliases=["r"] ,help="Resumes the current song")
    async def resume(self, ctx,*args):                        
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
    @commands.command(name="skip", aliases=["s"] ,help="Skips the current played song")
    async def skip(self, ctx,*args):
        if self.vc != None and self.vc:
            self.vc.stop()
            await self.play_music(ctx)
    
    @commands.command(name="queue", aliases=["q"], help="Displays all the songs currently in the queue")
    async def queue(self, ctx):
        retval = ""
        
        for i in range(0, len(self.music_queue)):
            if i > 4: break
            retval += self.music_queue[i][0]['title'] + '/'
            
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in the queue.")
    
    @commands.command(name="clear", aliases=["c","bin"], help="Stops the current song and clears the queue")
    async def clear(self, ctx, *args):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self,music_queue = []
        await ctx.send("Music queue cleared") 
    
    @commands.command(name="leave", aliases=["disconnect","l","d"], help="Kick the bot from the voice channel")
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()        
            