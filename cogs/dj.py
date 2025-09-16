import discord, random, asyncio, os, datetime , pytz , aiohttp , gc , subprocess , json 
from discord.ext import commands , tasks
from pathlib import Path
from discord import app_commands
from cogs.essential.host import status,restart
from dotenv import load_dotenv
from functools import partial



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
        self.music_folder = os.path.join("musicas_repo", "musicas")  # Nova pasta de músicas
        self.announcement_folder = os.path.join("musicas_repo", "anuncios")  # Pasta de anúncios
        self.current_announcement = False   #ANUNCIO ATUAL
        self.ffmpeg_options = {            'before_options': ' -nostdin',  'options': '-vn -f s16le -b:a 192k'         }
        self.status_msg = None  # Para guardar a mensagem de status
        self._falhas_memoria = 0  # inicializa o contador
        self.played_songs_file = "played_songs.json"
        self.played_songs = []
        self.pedidos = []  # lista de pedidos


        # Carregar do arquivo se existir
        if os.path.exists(self.played_songs_file):
            try:
                with open(self.played_songs_file, "r", encoding="utf-8") as f:
                    self.played_songs = json.load(f)
            except Exception as e:
                print(f"⚠️ - Erro ao carregar played_songs.json: {e}")
        else:
            # Cria o arquivo vazio
            with open(self.played_songs_file, "w", encoding="utf-8") as f:
                json.dump([], f)


    
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



        #SALVAR O JSON COM AS MUSICAS JÀ TOCADAS
    def save_played_songs(self):
        try:
            with open(self.played_songs_file, "w", encoding="utf-8") as f:
                json.dump(self.played_songs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ - Erro ao salvar played_songs.json: {e}")



        # PROCURA UMA MUSICA ALEATORIA E SELECIONA
    def get_random_song(self):
        try:
            files = [f for f in os.listdir(self.music_folder) if f.endswith(".mp3")]
            remaining_songs = [f for f in files if f not in self.played_songs]


            if not remaining_songs:
                self.played_songs.clear()
                remaining_songs = files

            song = random.choice(remaining_songs)
            self.played_songs.append(song)
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




        # PROCURA UMA INTRO DE PEDIDO ALEATÓRIA
    def get_random_pedido_intro(self):
        try:
            intros = [
                f for f in os.listdir(self.announcement_folder)
                if f.endswith(".mp3") and f.startswith("pedidos")
            ]
            return os.path.join(self.announcement_folder, random.choice(intros)) if intros else None
        except Exception as e:
            print(f"❌ - Erro ao listar intros de pedido: {e}")
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
        async def _tocar(vc, path, fade=True):
            """Toca um arquivo de áudio (com ou sem fade) e aguarda terminar"""
            if not await self.verify_and_cleanup_audio_file(path):
                return

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
                if fade :
                    await self.update_status(path, vc)

                def after_playing(error):
                    if error:
                        print(f"❌ - Erro ao reproduzir: {error}")
                    done.set()

                vc.play(source, after=after_playing)
                await done.wait()
                self.save_played_songs()  # Salva sempre que adiciona

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



        # ---------------- LOOP PRINCIPAL ----------------
        play_next_is_pedido = True  # controla alternância

        while vc.is_connected():
            skip_jingle_next = False

            # Se houver pedidos
            if self.pedidos:
                if play_next_is_pedido:
                    pedido_intro = self.get_random_pedido_intro()
                    if pedido_intro and await self.verify_and_cleanup_audio_file(pedido_intro):
                        await _tocar(vc, pedido_intro, fade=False)

                    path = self.pedidos.pop(0)
                    await _tocar(vc, path, fade=True)
                    skip_jingle_next = True
                    play_next_is_pedido = False  # próxima será música da DJ
                    continue
                else:
                    song = self.get_random_song()
                    if not song:
                        print("❌ - Nenhuma música encontrada na pasta.")
                        await asyncio.sleep(60)
                        continue
                    path = os.path.join(self.music_folder, song)
                    await _tocar(vc, path, fade=True)
                    play_next_is_pedido = True
                    # Chance de tocar jingle após música normal
                    if random.random() < 0.2:
                        jingle = self.get_random_jingle()
                        if jingle and await self.verify_and_cleanup_audio_file(jingle):
                            await _tocar(vc, jingle, fade=False)
                    continue

            # Se não houver pedidos, toca normalmente
            if self.current_announcement:
                path = self.current_announcement
                self.current_announcement = False
                await _tocar(vc, path, fade=False)
                skip_jingle_next = True
                continue

            song = self.get_random_song()
            if not song:
                print("❌ - Nenhuma música encontrada na pasta.")
                await asyncio.sleep(60)
                continue
            path = os.path.join(self.music_folder, song)
            await _tocar(vc, path, fade=True)

            if not skip_jingle_next and random.random() < 0.2:
                jingle = self.get_random_jingle()
                if jingle and await self.verify_and_cleanup_audio_file(jingle):
                    await _tocar(vc, jingle, fade=False)







               






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
    @tasks.loop(minutes=1)
    async def check_music(self):
        channel = getattr(self, "temp_channel", None) or self.client.get_channel(self.voice_channel_id)
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
        # Se estava em canal temporário e desconectou, reseta para o canal original
        if not (channel and channel.id == self.voice_channel_id):
            self.temp_channel = None

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

        view = discord.ui.View(timeout=None)
        consultarmusica = discord.ui.Button(label="Músicas Tocadas",style=discord.ButtonStyle.blurple,emoji="🎵")
        view.add_item(item=consultarmusica)
        consultarmusica.callback = partial( self.musicas_tocadas )

        try:
            if self.status_msg:
                try:
                    await self.status_msg.edit(embed=embed , view= view)
                except discord.NotFound:
                    # Mensagem foi deletada, então envia uma nova
                    self.status_msg = await vc.channel.send(embed=embed , view= view)
            else:
                self.status_msg = await vc.channel.send(embed=embed , view= view)
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



        #RETORNA AO USUARIO QUAIS MUSICAS JÀ FORAM TOCADAS
    @commands.Cog.listener()
    async def musicas_tocadas(self, interaction):
        await interaction.response.defer(ephemeral=True)

        if not self.played_songs:
            await interaction.followup.send("Nenhuma música foi tocada ainda ~kyuu.", ephemeral=True)
            return

        # Monta lista completa formatada com contador
        lista = [f"{i}. {song}" for i, song in enumerate(self.played_songs, start=1)]

        # Envia em blocos de até ~1800 caracteres
        bloco = ""
        for line in lista:
            if len(bloco) + len(line) + 1 < 1800:
                bloco += line + "\n"
            else:
                await interaction.followup.send(f"✅ - Músicas já tocadas:\n{bloco}", ephemeral=True)
                bloco = line + "\n"

        # Manda o último bloco restante
        if bloco.strip():
            await interaction.followup.send(f"✅ - Músicas já tocadas:\n{bloco}", ephemeral=True)






#-----------------COMANDOS AQUI-------------------------
#Inicia instancia e vincula com a classe
    dj=app_commands.Group(name="radio",description="Comandos de gestão do sistema DJ Braixen.",allowed_installs=app_commands.AppInstallationType(guild=True,user=False),allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=False, private_channel=False))


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
        await self.musicas_tocadas(interaction)







    @dj.command(name="mover", description="🔊⠂Move o bot para outro canal de voz temporariamente.")
    @app_commands.describe(canal="Canal de voz para onde mover o bot.")
    async def mover_canal_slash(self, interaction: discord.Interaction, canal: discord.VoiceChannel):
        if interaction.user.id != DONOID:
            await interaction.response.send_message("❌ - Apenas o dono do bot pode usar este comando ~kyuu.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        vc_atual = discord.utils.get(self.client.voice_clients, guild=interaction.guild)

        try:
            if vc_atual and vc_atual.is_connected():
                await vc_atual.disconnect(force=True)

            # Conecta no novo canal temporário
            novo_vc = await canal.connect()
            self.temp_channel = canal  # <-- registra canal temporário
            self.status_msg = None
            await self.play_music(novo_vc)

            await interaction.followup.send( f"✅ - Bot movido temporariamente para **{canal.name}**.", ephemeral=True )
        except Exception as e:
            await interaction.followup.send( f"❌ - Não consegui mover para o canal {canal.mention}.\nErro: {e}" )
            print(f"🚨 - Falha ao mover bot para novo canal de voz verifique o erro {e}")







    @dj.command(name="pedido", description="🎶⠂Peça uma música para a dj tocar logo após a atual.")
    @app_commands.describe(música="Escolha a música que será tocada em seguida.")
    async def tocar_slash(self, interaction: discord.Interaction, música: str):
        # Verifica se a DJ (bot) está no mesmo canal de voz
        vc = getattr(self, "vc", None)  # vc atual do bot
        if not vc or not vc.channel or vc.channel != interaction.user.voice.channel:
            await interaction.response.send_message( "❌ - Você precisa estar no mesmo canal de voz que eu para pedir uma música.", ephemeral=True , delete_after = 20)
            return
        path = os.path.join(self.music_folder, música)

        if not os.path.exists(path):
            await interaction.response.send_message("❌ - Música não encontrada.", ephemeral=True , delete_after = 20)
            return

        # define como a próxima música
        self.pedidos.append(path)  # adiciona na fila
        await interaction.response.send_message(f"✅ - **{música}** será tocada a seguir ~kyuu.", ephemeral=True , delete_after = 20)

    @tocar_slash.autocomplete('música')
    async def autocomplete_musicas(self, interaction: discord.Interaction, current: str):
        files = [f for f in os.listdir(self.music_folder) if f.endswith(".mp3")]
        return [ app_commands.Choice(name=f, value=f) for f in files if current.lower() in f.lower()][:25]  # Discord permite até 25 sugestões






async def setup(client:commands.Bot) -> None:
  await client.add_cog(MusicBot(client))
