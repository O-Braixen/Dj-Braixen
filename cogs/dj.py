import discord, random, asyncio, os, datetime , pytz , aiohttp , gc , subprocess , tempfile
from discord.ext import commands , tasks
from pathlib import Path
from discord import app_commands
from cogs.essential.host import status,restart
from dotenv import load_dotenv


load_dotenv()
GIT_TOKEN = os.getenv("git_token")
DONOID = int(os.getenv("DONO_ID")) #acessa e define o id do dono
CHANNEL_ID = int(os.getenv("RADIO_CHANNEL_ID"))

GITHUB_API_URL_BASE = os.getenv("git_repositorio")
PASTAS = ["anuncios","musicas"]
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
        self._falhas_memoria = 0  # inicializa o contador


    
        # LIGANDO O BOT
    @commands.Cog.listener()
    async def on_ready(self):
        print("🎵 - Modúlo DJ carregado.")
        #await asyncio.sleep(5)
        if not self.memory_check.is_running():
            self.memory_check.start()  # Inicia a verificação de memoria.
        
        await self.reproduzir()
        await self.verificar_arquivos()
        
        



      # AGENDA A VERIFICAÇÃO PARA RODAR O ANUNCIO
    async def verificar_arquivos(self):
        print("🌐 - Iniciando verificação de arquivos.")
        await self.baixar_arquivos()



    
    # FUNÇÃO PARA BAIXAR OS ARQUIVOS DO REPOSITÓRIO
    async def baixar_arquivos(self, tentativa=1):
        if tentativa > MAX_TENTATIVAS:
            print("❌ - Limite de tentativas atingido. Abortando download.")
            #await self.reproduzir()
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
                                    await asyncio.sleep(5)
                                else:
                                    print(f"❌ - Erro ao baixar {nome_arquivo}: {download_response.status}")
                                    print("🔁 - Reiniciando tentativa de download...")
                                    
                                    return await self.baixar_arquivos(tentativa + 1)
                                
                    else:
                        print(f"❌ - Erro ao acessar {url}: {response.status}")
                        print("🔁 - Reiniciando tentativa de download...")
                        return await self.baixar_arquivos(tentativa + 1)
            print("✅ - Biblioteca de musicas sincronizada com Github\n\n")
            #await self.reproduzir()
    




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
    



        # PROCURA UM JINGLE ALEATORIA E SELECIONA
    def get_random_jingle(self):
        try:
            jingles = [
                f for f in os.listdir(self.announcement_folder)
                if f.endswith(".mp3") and f.startswith("jingle")
            ]
            return os.path.join(self.announcement_folder, random.choice(jingles)) if jingles else None
        except Exception as e:
            print(f"❌ - Erro ao listar jingles: {e}")
            return None







        # PUXA UM ANUNCIO EM UM DETEMINADO HORARIO
    def get_hourly_announcement(self):
        current_hour = datetime.datetime.now().astimezone(pytz.timezone('America/Sao_Paulo')).hour
        filename = f"{current_hour}H.mp3"
        filepath = os.path.join(self.announcement_folder, filename)
        return filepath if os.path.exists(filepath) else False
    


        # Pega duração da música
    async def get_duration(self, path):
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, _ = await proc.communicate()
        return float(out.decode().strip())





        # TOCA MUSICA DE FATO
    async def play_music(self, vc):
        while vc.is_connected():
            if self.current_announcement:
                song = self.current_announcement
                path = song
                self.current_announcement = False
                fade = False  # Não faz fade em anúncios
            else:
                song = self.get_random_song()
                if not song:
                    print(f"❌ - Nenhuma música encontrada na pasta.")
                    await asyncio.sleep(60)
                    continue
                path = os.path.join(self.music_folder, song)
                fade = True

            # Verifica arquivo
            if not await self.verify_and_cleanup_audio_file(path):
                continue

            source = None
            ffmpeg_source = None
            done = asyncio.Event()

            try:
                if fade:
                    duration = await self.get_duration(path)
                    fade_out_start = max(duration - 3, 0)

                    ffmpeg_source = discord.FFmpegPCMAudio(
                        path,
                        before_options="-nostdin",
                        options=f"-af 'afade=t=in:ss=0:d=3,afade=t=out:st={fade_out_start}:d=3' -vn -f s16le -b:a 192k"
                    )
                else:
                    ffmpeg_source = discord.FFmpegPCMAudio(path, **self.ffmpeg_options)

                source = discord.PCMVolumeTransformer(ffmpeg_source, volume=0.5)
                await self.update_status(song, vc)

                def after_playing(error):
                    if error:
                        print(f"❌ - Erro ao reproduzir: {error}")
                    done.set()

                vc.play(source, after=after_playing)
                await done.wait()

            finally:
                vc.stop()
                try:
                    if source and hasattr(source, "cleanup"):
                        source.cleanup()
                    if ffmpeg_source and hasattr(ffmpeg_source, "cleanup"):
                        ffmpeg_source.cleanup()
                    if ffmpeg_source and hasattr(ffmpeg_source, "proc") and ffmpeg_source.proc:
                        ffmpeg_source.proc.kill()
                        ffmpeg_source.proc.wait()
                except Exception as e:
                    print(f"🗑️ - Erro no cleanup: {e}")
                del source
                del ffmpeg_source
                gc.collect()

            # Chance de tocar jingle
            if random.random() < 0.2:
                jingle = self.get_random_jingle()
                if jingle and await self.verify_and_cleanup_audio_file(jingle):
                    jingle_source = None
                    jingle_ffmpeg = None
                    done = asyncio.Event()
                    try:
                        print(f"🔊 - Tocando jingle: {os.path.basename(jingle)}")
                        jingle_ffmpeg = discord.FFmpegPCMAudio(jingle, **self.ffmpeg_options)
                        jingle_source = discord.PCMVolumeTransformer(jingle_ffmpeg, volume=0.5)

                        def after_jingle(error):
                            if error:
                                print(f"❌ - Erro ao tocar jingle: {error}")
                            done.set()

                        vc.stop()
                        vc.play(jingle_source, after=after_jingle)
                        await done.wait()

                    except Exception as e:
                        print(f"❌ - Erro ao tocar jingle: {e}")
                    finally:
                        vc.stop()
                        try:
                            if jingle_source and hasattr(jingle_source, "cleanup"):
                                jingle_source.cleanup()
                            if jingle_ffmpeg and hasattr(jingle_ffmpeg, "cleanup"):
                                jingle_ffmpeg.cleanup()
                            if jingle_ffmpeg and hasattr(jingle_ffmpeg, "proc") and jingle_ffmpeg.proc:
                                jingle_ffmpeg.proc.kill()
                                jingle_ffmpeg.proc.wait()
                        except Exception as e:
                            print(f"🗑️ - Erro no cleanup do jingle: {e}")
                        del jingle_source
                        del jingle_ffmpeg
                        gc.collect()









               






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
        print(f"💿 - Tocando Agora: {song}")
        await self.client.change_presence(activity=discord.CustomActivity(name=f"Ouvindo {song}"))
        embed = discord.Embed(description=f"## 🎵 • Tocando agora\n\n**{song}**",color=0xFBC02D)  # amarelo estilo Braixen
        embed.set_footer(text=f"{self.client.user.name} • Braixen's House • {now.hour:02d}:{now.minute:02d}")
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
    @tasks.loop(seconds=60)
    async def memory_check(self):
        try:
            res_status, host = await status(self.client.user.name)

            if host == "squarecloud":
                ram_str = res_status['response']['ram']
                limit_ram = 210
            elif host == "discloud":
                ram_str = res_status['apps']['memory'].split('/')[0]
                limit_ram = 90
            else:
                return  # host desconhecido, ignora

            ram_value = float(ram_str.replace("MB", "").strip())
            self._falhas_memoria = 0  # resetar contador se for bem-sucedido

            if ram_value >= limit_ram:
                print(f"🤖 - Uso de RAM alto! Reiniciando o app pela {host}...")
                await restart(self.client.user.name)

        except Exception as e:
            self._falhas_memoria += 1
            print(f"🤖 - falha ao checar memoria na hospedagem ({self._falhas_memoria}/300)...\nError: {e}")
            if self._falhas_memoria >= 300:
                print("🚨 - Muitas falhas consecutivas ao checar memória. Reiniciando preventivamente...")
                await asyncio.sleep(10)
                await restart(self.client.user.name)




#-----------------COMANDOS AQUI-------------------------
#Inicia instancia e vincula com a classe
    dj=app_commands.Group(name="musica",description="Comandos de gestão do sistema DJ Braixen.",allowed_installs=app_commands.AppInstallationType(guild=True,user=False),allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=False, private_channel=False))


    @dj.command(name="verificar", description="🤖⠂Verifica todos os arquivos de música e remove os corrompidos.")
    async def verificar_musicas_slash(self, interaction: discord.Interaction):
        if interaction.user.id != DONOID:
            await interaction.response.send_message("Este comando é somente para o Dono do bot usar ~kyuu.", ephemeral=True)
            return

        await interaction.response.send_message("🔍 - Iniciando verificação de arquivos de áudio ~kyuu...")
        status_msg = await interaction.original_response()

        total = 0
        removidos = 0
        verificados = 0
        arquivos_removidos = []

        for pasta in [self.music_folder, self.announcement_folder]:
            for nome_arquivo in os.listdir(pasta):
                if not nome_arquivo.endswith(".mp3"):
                    continue

                caminho = os.path.join(pasta, nome_arquivo)
                total += 1
                valido = await self.verify_and_cleanup_audio_file(caminho)
                verificados += 1
                if not valido:
                    removidos += 1
                    arquivos_removidos.append(nome_arquivo)

                if verificados % 20 == 0:
                    await status_msg.edit(content=f"🔍 - Verificando arquivos... {verificados} analisados até agora ~kyuuu...")

        if removidos > 0:
            lista_formatada = "\n".join(f"- {nome}" for nome in arquivos_removidos)
            conteudo_final = (
                f"✅ - Verificação concluída.\n"
                f"{total} arquivos analisados, {removidos} removidos.\n\n"
                f"🗑️ - Arquivos removidos:\n{lista_formatada}"
            )
        else:
            conteudo_final = f"✅ - Verificação concluída. {total} arquivos analisados, nenhum removido ~kyuu."

        await status_msg.edit(content=conteudo_final)





    @dj.command(name="tocadas", description="📻⠂Mostra a lista completa de músicas já tocadas pelo bot.")
    async def musicas_tocadas_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not self.played_songs:
            await interaction.followup.send("Nenhuma música foi tocada ainda ~kyuu.", ephemeral=True)
            return

        lista = "\n".join(f"- {song}" for song in sorted(self.played_songs))

        # Se passar do limite de 2000 caracteres, envia como arquivo txt
        if len(lista) > 1900:
            import io
            file = discord.File(fp=io.BytesIO(lista.encode()), filename="musicas_tocadas.txt")
            await interaction.followup.send("✅ - Lista completa de músicas já tocadas:", file=file, ephemeral=True)
        else:
            await interaction.followup.send(f"✅ - Músicas já tocadas:\n{lista}", ephemeral=True)






async def setup(client:commands.Bot) -> None:
  await client.add_cog(MusicBot(client))
