import discord, random, asyncio, os, datetime , pytz , aiohttp , gc , subprocess
from discord.ext import commands , tasks
from pathlib import Path
from discord import app_commands
from cogs.essential.host import status,restart
from dotenv import load_dotenv


load_dotenv()
GIT_TOKEN = os.getenv("git_token")
CHANNEL_ID = int(os.getenv("RADIO_CHANNEL_ID"))

GITHUB_API_URL_BASE = os.getenv("git_repositorio")
PASTAS = ["musicas", "anuncios"]
HEADERS = {"Authorization": f"token {GIT_TOKEN}"}  # Substitua pelo seu token pessoal

MAX_TENTATIVAS = 50



class MusicBot(commands.Cog):
    def __init__(self , client: commands.Bot):
        self.client = client
        self.voice_channel_id = CHANNEL_ID  # ID do canal de voz.
        self.synced = False
        self.played_songs = set()
        self.music_folder = os.path.join("musicas_repo", "musicas")  # Nova pasta de músicas
        self.announcement_folder = os.path.join("musicas_repo", "anuncios")  # Pasta de anúncios
        self.current_announcement = False   #ANUNCIO ATUAL
        self.ffmpeg_options = {            'before_options': ' -nostdin',  'options': '-vn -f s16le -b:a 192k'         }
        self.status_msg = None  # Para guardar a mensagem de status


    
        # LIGANDO O BOT
    @commands.Cog.listener()
    async def on_ready(self):
        print("🎵 - Modúlo DJ carregado.")
        await asyncio.sleep(5)
        if not self.memory_check.is_running():
            self.memory_check.start()  # Inicia a verificação de memoria.
        await self.verificar_arquivos()
        
        



      # AGENDA A VERIFICAÇÃO PARA RODAR O ANUNCIO
    async def verificar_arquivos(self):
        print("🌐 - Iniciando verificação de arquivos.")
        await self.baixar_arquivos()



    # FUNÇÃO PARA BAIXAR OS ARQUIVOS DO REPOSITÓRIO
    async def baixar_arquivos(self, tentativa=1):
        if tentativa > MAX_TENTATIVAS:
            print("❌ - Limite de tentativas atingido. Abortando download.")
            await self.reproduzir()
            return

        async with aiohttp.ClientSession() as session:
            if GITHUB_API_URL_BASE is None or GIT_TOKEN is None:
                print("❌ - SEM DADOS DE REPOSITORIO, POR FAVOR VERIFIQUE O ARQUIVO .ENV")
                return
            for pasta_remota in PASTAS:
                pasta_local = os.path.join("musicas_repo", pasta_remota)
                if not os.path.exists(pasta_local):
                    os.makedirs(pasta_local)
                
                url = f"{GITHUB_API_URL_BASE}/{pasta_remota}"
                async with session.get(url, headers=HEADERS) as response:
                    if response.status == 200:
                        conteudo = await response.json()
                        for item in conteudo:
                            nome_arquivo = item["name"]
                            caminho_arquivo = os.path.join(pasta_local, nome_arquivo)

                            if os.path.exists(caminho_arquivo):
                                continue

                            download_url = item["download_url"]
                            async with session.get(download_url) as download_response:
                                if download_response.status == 200:
                                    with open(caminho_arquivo, "wb") as f:
                                        f.write(await download_response.read())
                                    print(f"✅ - Baixado: {nome_arquivo}")
                                    await asyncio.sleep(0.2)
                                else:
                                    print(f"❌ - Erro ao baixar {nome_arquivo}: {download_response.status}")
                                    print("🔁 - Reiniciando tentativa de download...")
                                    
                                    return await self.baixar_arquivos(tentativa + 1)
                                
                    else:
                        print(f"❌ - Erro ao acessar {url}: {response.status}")
                        print("🔁 - Reiniciando tentativa de download...")
                        return await self.baixar_arquivos(tentativa + 1)
            print("✅ - Biblioteca de musicas sincronizada com Github\n\n")
            await self.reproduzir()




        # FUNÇÂO DE REPRODUZIR MUSICA
    async def reproduzir(self):
        channel = self.client.get_channel(self.voice_channel_id)
        if channel:
            try:
                try:
                    async for msg in channel.history(limit=None):
                        await channel.purge(limit=100)
                        await asyncio.sleep(1)  # Evita ser bloqueado por flood
                except Exception as e:
                    print(f"❌ - Erro ao limpar mensagens do canal: {e}")

                if not self.check_music.is_running():
                    self.channel = channel
                    self.check_music.start()  # Verificação contínua.
                if not self.hourly_announcements.is_running():
                    self.hourly_announcements.start()  # Inicia sistema de anúncios
                
            except Exception as e:
                print(f"❌ - ({self.client.user}) Erro ao conectar ao canal de voz: {e}")
        else:
            print(f"❌ - ({self.client.user}) Canal de voz não encontrado.")




        # PROCURA UMA MUSICA ALEATORIA E SELECIONA
    def get_random_song(self):
        try:
            files = [f for f in os.listdir(self.music_folder) if f.endswith(".mp3")]
            remaining_songs = list(set(files) - self.played_songs)

            if not remaining_songs:
                self.played_songs.clear()
                remaining_songs = files

            song = random.choice(remaining_songs)
            self.played_songs.add(song)
            return song

        except Exception as e:
            print(f"❌ - Erro ao listar músicas: {e}")
            return None
    



        # PUXA UM ANUNCIO EM UM DETEMINADO HORARIO
    def get_hourly_announcement(self):
        current_hour = datetime.datetime.now().astimezone(pytz.timezone('America/Sao_Paulo')).hour
        filename = f"{current_hour}H.mp3"
        filepath = os.path.join(self.announcement_folder, filename)
        return filepath if os.path.exists(filepath) else False
    




        # TOCA MUSICA DE FATO
    async def play_music(self, vc):
        while vc.is_connected():
            if self.current_announcement:
                print(f"‼️ - Tocando Anúncio: {self.current_announcement}")
                path = self.current_announcement
                self.current_announcement = False
            else:
                song = self.get_random_song()
                if not song:
                    print(f"❌ - Nenhuma música encontrada na pasta.")
                    await asyncio.sleep(60)
                    continue
                path = os.path.join(self.music_folder, song)                
            
            # Verifica se o arquivo está ok com ffmpeg antes de tentar tocar
            if not await self.verify_and_cleanup_audio_file(path):
                continue
            # Separar para ter acesso ao FFmpegPCMAudio diretamente
            ffmpeg_source = discord.FFmpegPCMAudio(path, **self.ffmpeg_options)
            source = discord.PCMVolumeTransformer(ffmpeg_source, volume=0.5)
            done = asyncio.Event()
            # Define o status e começa a reproduzir a musica
            print(f"💿 - Tocando Agora: {song}")
            await self.update_status(song, vc)

            def after_playing(error):
                if error:
                    print(f"❌ - Erro ao reproduzir: {error}")
                done.set()
            vc.play(source, after=after_playing)
            await done.wait()

            # Liberação de memória manual após reprodução
            try:
                if hasattr(source, "cleanup"):
                    source.cleanup()
                if hasattr(ffmpeg_source, "cleanup"):
                    ffmpeg_source.cleanup()
                if hasattr(ffmpeg_source, 'proc'):
                    ffmpeg_source.proc.kill()
                del source
                del ffmpeg_source
            except Exception as e:
                print(f"🗑️ - Erro no cleanup: {e}")

            gc.collect()
            await asyncio.sleep(1)






    #Verifica se um arquivo de áudio é válido usando ffmpeg.
    async def verify_and_cleanup_audio_file(self, path):
        try:
            proc = await asyncio.create_subprocess_exec(
                'ffmpeg', '-v', 'error', '-i', path, '-f', 'null', '-',
                stdout=subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            exit_code = proc.returncode

            stderr_output = stderr.decode().strip()

            if exit_code != 0 or "Invalid data" in stderr_output or "Header missing" in stderr_output:
                print(f"🗑️ - Arquivo corrompido ou inválido. Deletando: {path}")
                print(f"⚠️ stderr: {stderr_output}")
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"⚠️ - Erro ao deletar arquivo: {e}")
                return False

            return True

        except Exception as e:
            print(f"⚠️ - Erro ao verificar arquivo com ffmpeg: {e}")
            return False






      

    #Verifica se a música ainda está tocando e se o bot está conectado.
    @tasks.loop(minutes=2)
    async def check_music(self):
        channel = self.channel
        backoff_delay = 1  # começa com 1 segundo

        for attempt in range(5):  # tenta reconectar no máximo 5 vezes por checagem
            vc = discord.utils.get(self.client.voice_clients, guild=channel.guild)

            if not vc or not vc.is_connected():
                try:
                    vc = await channel.connect()
                    await self.play_music(vc)
                    print(f"🔄️ - Reconectado ao canal de voz: {channel.name}")
                    break  # reconectado com sucesso, sai do loop
                except Exception as e:
                    print(f"❌ - Erro ao reconectar (tentativa {attempt + 1}): {e}")
                    if vc:
                        try:
                            await vc.disconnect()
                        except Exception:
                            pass
                    await asyncio.sleep(backoff_delay)
                    backoff_delay = min(backoff_delay * 2, 60)  # dobra até máximo de 60s
            else:
                break  # já está conectado

        # Tenta reiniciar a música se estiver conectado e parado
        vc = discord.utils.get(self.client.voice_clients, guild=channel.guild)
        if vc and vc.is_connected() and not vc.is_playing() and not vc.is_paused():
            print("🔄️ - Música parou. Reiniciando stream...")
            try:
                await self.play_music(vc)
            except Exception as e:
                print(f"❌ - Erro ao reiniciar o stream: {e}")
                try:
                    await vc.disconnect()
                except Exception:
                    await restart(self.client.user.name)
                    pass

        

        # AGENDA A VERIFICAÇÃO PARA RODAR O ANUNCIO
    @tasks.loop(minutes=5)
    async def hourly_announcements(self):
        now = datetime.datetime.now().astimezone(pytz.timezone('America/Sao_Paulo'))
        next_hour = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        seconds_until_next_hour = (next_hour - now).total_seconds()
        print(f"⏳ - Próximo anúncio em {int(seconds_until_next_hour)} segundos")
        await asyncio.sleep(seconds_until_next_hour)  # Espera até a próxima hora cheia
        # Só pega o anúncio no momento certo, sem repetir
        self.current_announcement = self.get_hourly_announcement()



    # LOOP DE ATUALIZAÇÃO DE STATUS
    async def update_status(self, song, vc):
        now = datetime.datetime.now().astimezone(pytz.timezone('America/Sao_Paulo'))
        song = Path(song).stem
        await self.client.change_presence(activity=discord.CustomActivity(name=f"Ouvindo {song}"))
        embed = discord.Embed(description=f"## 🎵 • Tocando agora\n\n**{song}**",color=0xFBC02D)  # amarelo estilo Braixen
        embed.set_footer(text=f"{self.client.user.name} • Braixen's House • {now.hour}:{now.minute}")
        embed.set_thumbnail(url=self.client.user.avatar.url)
        try:
            if self.status_msg:
                try:
                    await self.status_msg.edit(embed=embed)
                except discord.NotFound:
                    # Mensagem foi deletada, então envia uma nova
                    self.status_msg = await vc.channel.send(embed=embed)
            else:
                self.status_msg = await vc.channel.send(embed=embed)
        except Exception as e:
            print(f"❌ - Erro ao atualizar mensagem de status: {e}")



    # Monitorar Memoria no sistema DJ
    @tasks.loop(seconds=20)
    async def memory_check(self):
        try:
            res_status, host = await status(self.client.user.name)
            if host == "squarecloud":
                ram_str = res_status['response']['ram']
                limit_ram = 235
            if host == "discloud":
                ram_str = res_status['apps']['memory'].split('/')[0]
                limit_ram = 90
            
            ram_value = float(ram_str.replace("MB", "").strip())
            if ram_value >= limit_ram:
                print(f"🤖 - Uso de RAM alto! Reiniciando o app pela {host}...")
                await asyncio.sleep(10)
                await restart(self.client.user.name)
                
        except Exception as e :print(f"🤖 - falha ao checar memoria na hospedagem...\nError: {e}")




#-----------------COMANDOS AQUI-------------------------
#Inicia instancia e vincula com a classe




async def setup(client:commands.Bot) -> None:
  await client.add_cog(MusicBot(client))
