import discord, random, asyncio, os, datetime , pytz , aiohttp , gc , subprocess , json 
from discord.ext import commands , tasks
from pathlib import Path
from discord import app_commands
from cogs.essential.host import status,restart , informação
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
        self.played_songs_file = os.path.join("musicas_repo", "played_songs.json")
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
        await asyncio.sleep(5)        
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
            return

        if GITHUB_API_URL_BASE is None or GIT_TOKEN is None:
            print("❌ - SEM DADOS DE REPOSITORIO, VERIFIQUE O .ENV")
            return

        async with aiohttp.ClientSession() as session:
            for pasta_remota in PASTAS:
                pasta_local = os.path.join("musicas_repo", pasta_remota)
                os.makedirs(pasta_local, exist_ok=True)

                url = f"{GITHUB_API_URL_BASE}/{pasta_remota}"
                async with session.get(url, headers=HEADERS) as response:
                    if response.status != 200:
                        print(f"❌ - Erro ao acessar {url}: {response.status}")
                        print("🔁 - Tentando novamente...")
                        return await self.baixar_arquivos(tentativa + 1)

                    conteudo = await response.json()

                    # Arquivos existentes no GitHub
                    arquivos_repo = {
                        item["name"]
                        for item in conteudo
                        if item["type"] == "file"
                    }

                    # Arquivos existentes localmente
                    arquivos_locais = set(os.listdir(pasta_local))

                    # 🧹 REMOVE arquivos locais que não existem mais no repo
                    for arquivo in arquivos_locais - arquivos_repo:
                        caminho = os.path.join(pasta_local, arquivo)
                        if os.path.isfile(caminho):
                            os.remove(caminho)
                            print(f"🗑️ - Removido (não existe no repo): {arquivo}")

                    # ⬇️ BAIXA arquivos novos
                    for item in conteudo:
                        if item["type"] != "file":
                            continue

                        nome_arquivo = item["name"]
                        caminho_arquivo = os.path.join(pasta_local, nome_arquivo)

                        if os.path.exists(caminho_arquivo):
                            continue

                        async with session.get(item["download_url"]) as download_response:
                            if download_response.status == 200:
                                with open(caminho_arquivo, "wb") as f:
                                    f.write(await download_response.read())
                                print(f"✅ - Baixado: {nome_arquivo}")
                                await asyncio.sleep(0.4)
                            else:
                                print(f"❌ - Erro ao baixar {nome_arquivo}")
                                return await self.baixar_arquivos(tentativa + 1)

        print("✅ - Biblioteca de músicas 100% sincronizada com o GitHub\n")

















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
                    await self.update_status(path, vc , duration)

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
    @tasks.loop(seconds=20)
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
    async def update_status(self, song, vc , duration):
        now = datetime.datetime.now().astimezone(pytz.timezone('America/Sao_Paulo'))
        song = Path(song).stem

                # formata duração
        if duration < 3600:  # menos de 1h → mm:ss
            minutos, segundos = divmod(int(duration), 60)
            tempo_total = f"{minutos:02d}:{segundos:02d}"
        else:  # 1h ou mais → hh:mm:ss
            horas, resto = divmod(int(duration), 3600)
            minutos, segundos = divmod(resto, 60)
            tempo_total = f"{horas}:{minutos:02d}:{segundos:02d}"
        
         # calcula timestamps
        end_timestamp = int(datetime.datetime.now().timestamp()) + int(duration)            # agora + duração da música


        print(f"💿 - Tocando Agora: {song} ({tempo_total})")
        await self.client.change_presence(activity=discord.CustomActivity(name=f"Ouvindo {song}"))
        embed = discord.Embed( description=f"## 🎶 • Tocando agora\n\nkyu~ sente essa vibe comigo 💛\n\n**{song}**\n\n⏱️ Duração total: `{tempo_total}`\n⏳ Termina: <t:{end_timestamp}:R>\n\nRelaxa… a Yoko tá no controle 😌🔥" , color=0xFBC02D)  # amarelo estilo Braixen
        embed.set_footer(text=f"{self.client.user.name} • {self.channel.guild.name} • {now.hour:02d}:{now.minute:02d}")
        embed.set_thumbnail(url=self.client.user.avatar.url)

        view = discord.ui.View(timeout=None)
        consultarmusica = discord.ui.Button(label="Tocadas",style=discord.ButtonStyle.gray,emoji="🎵")
        view.add_item(item=consultarmusica)
        consultarmusica.callback = partial( self.musicas_tocadas )

        totasmusica = discord.ui.Button(label="Todas",style=discord.ButtonStyle.gray,emoji="🎶")
        view.add_item(item=totasmusica)
        totasmusica.callback = partial( self.todas_musicas )

        pedirmusica = discord.ui.Button(label="Pedir Música",style=discord.ButtonStyle.gray,emoji="🦊")
        view.add_item(item=pedirmusica)
        pedirmusica.callback = partial( self.embed_pedir_musica )

        try:
            if self.status_msg:
                try:
                    ultima_msg = None
                    async for msg in vc.channel.history(limit=1):
                        ultima_msg = msg

                    precisa_nova = ( not self.status_msg or not ultima_msg or ultima_msg.id != self.status_msg.id or ultima_msg.author.id != self.client.user.id)

                    if precisa_nova:
                        self.status_msg = await vc.channel.send(embed=embed, view=view)
                    else:
                        await self.status_msg.edit(embed=embed, view=view)
                    #await self.status_msg.edit(embed=embed , view= view)
                except discord.NotFound:
                    # Mensagem foi deletada, então envia uma nova
                    self.status_msg = await vc.channel.send(embed=embed , view= view)
            else:
                self.status_msg = await vc.channel.send(embed=embed , view= view)
        except Exception as e:
            print(f"❌ - Erro ao atualizar mensagem de status: {e}")











        #RETORNA AO USUARIO UM EMBED EXPLICANDO COMO FUNCIONA OS PEDIDOS DE MUSICAS
    @commands.Cog.listener()
    async def embed_pedir_musica(self, interaction: discord.Interaction):
        embed = discord.Embed(
            description=( "## 🎵 • Pedido de Música\n\n"
                "Kyu~ quer escolher o próximo som da rádio? Então vem comigo que é facinho! 💛\n\n"
                "**Como funciona:**\n"
                "1️⃣ Use o comando `/radio pedido`\n"
                "2️⃣ Digite o nome da música que você quer ouvir\n"
                "3️⃣ Escolha uma opção da lista automática\n"
                "4️⃣ Prontinho! A música entra na minha fila ✨\n\n"
                "⚠️ **Atenção, kyu~**\n"
                "• Só dá pra pedir músicas que já existem no meu sistema\n"
                "• Nada de pedidos fora do catálogo, tá?\n"
                "• Os pedidos funcionam **somente** via slash command\n\n"
                "ℹ️ O autocomplete mostra apenas músicas disponíveis… assim eu não erro na escolha pra você 💿🔥"
            ),
            color=0xFBC02D
        )

        embed.set_footer(text="Pedidos apenas via slash command")
        embed.set_thumbnail(url=self.client.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)
















        #RETORNA AO USUARIO QUAIS MUSICAS JÀ FORAM TOCADAS
    @commands.Cog.listener()
    async def musicas_tocadas(self, interaction):
        await interaction.response.defer(ephemeral=True)

        if not self.played_songs:
            await interaction.followup.send("Ainda não rolou nenhuma música por aqui, kyu~ ✨ Que tal ser o primeiro a escolher o som?", ephemeral=True)
            return

        # Monta lista completa formatada com contador
        lista = [f"{i}. {song}" for i, song in enumerate(self.played_songs, start=1)]

        # Envia em blocos de até ~1800 caracteres
        bloco = ""
        for line in lista:
            if len(bloco) + len(line) + 1 < 1800:
                bloco += line + "\n"
            else:
                await interaction.followup.send( f"✅ Kyu~ ♫ Aqui estão as músicas que já rolaram nessa jornada sonora:\n{bloco}",    ephemeral=True)
                bloco = line + "\n"

        # Manda o último bloco restante
        if bloco.strip():
            await interaction.followup.send( f"✅ Kyu~ ♫ Aqui estão as músicas que já rolaram nessa jornada sonora:\n{bloco}",    ephemeral=True)









        # RETORNA AO USUARIO TODAS AS MUSICAS DISPONIVEIS
    @commands.Cog.listener()
    async def todas_musicas(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            musicas = [f for f in os.listdir(self.music_folder) if f.endswith(".mp3")]
        except Exception as e:
            await interaction.followup.send( f"❌ ┃ Kyu… opa! Algo deu errado enquanto eu tentava listar as músicas. Dá uma respirada aí que eu já tento de novo, tá? 💫\n\n**Detalhes:** {e}",ephemeral=True)
            return

        if not musicas:
            await interaction.followup.send( "🎧 Kyu~ por enquanto não tem nenhuma música disponível pra tocar… mas fica por aqui, já já pinta coisa boa!",ephemeral=True)
            return

        # Monta lista completa formatada com contador
        lista = [f"{i}. {song}" for i, song in enumerate(musicas, start=1)]

        # Envia em blocos de até ~1800 caracteres
        bloco = ""
        for line in lista:
            if len(bloco) + len(line) + 1 < 1800:
                bloco += line + "\n"
            else:
                await interaction.followup.send(f"✅ Kyu! Olha só o que tá disponível pra tocar agora na Braixen's House:\n{bloco}",ephemeral=True)
                bloco = line + "\n"

        # Manda o último bloco restante
        if bloco.strip():
            await interaction.followup.send(f"✅ Kyu! Olha só o que tá disponível pra tocar agora na Braixen's House:\n{bloco}",ephemeral=True)




























#-----------------COMANDOS AQUI-------------------------
#Inicia instancia e vincula com a classe
    dj=app_commands.Group(name="radio",description="Comandos de gestão do sistema DJ Braixen.",allowed_installs=app_commands.AppInstallationType(guild=True,user=False),allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=False, private_channel=False))










    @dj.command(name="verificar", description="🤖⠂Verifica todos os arquivos de música e remove os corrompidos.")
    async def verificar_musicas_slash(self, interaction: discord.Interaction):
        if interaction.user.id != DONOID:
            await interaction.response.send_message("Ei ei~ esse comando é exclusivo do dono do bot, viu? Kyu~ 💛",ephemeral=True)           
            return

        await interaction.response.send_message("🔍 | Yoko na área! Começando a verificação dos arquivos de áudio… kyu~ ✨")
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
                    await status_msg.edit(content=f"🔍 | Conferindo tudinho com atenção… {verificados} arquivos analisados até agora, kyuuu~ 👀")

        if removidos > 0:
            lista_formatada = "\n".join(f"- {nome}" for nome in arquivos_removidos)
            conteudo_final = (
                f"✅ | Prontinho~ verificação concluída, kyu! ✨\n"
                f"📊 {total} arquivos analisados, {removidos} removidos pra manter tudo organizado.\n\n"
                f"🗑️ | Esses aqui precisaram sair:\n{lista_formatada}"
            )
        else:
            conteudo_final = (
                    f"✅ | Tudo certo por aqui~! {total} arquivos analisados "
                    f"e nenhum precisou ser removido, kyu~ 💛"
                )
        await status_msg.edit(content=conteudo_final)












    @dj.command(name="tocadas", description="📻⠂Mostra a lista completa de músicas já tocadas pelo bot.")
    async def musicas_tocadas_slash(self, interaction: discord.Interaction):
        await self.musicas_tocadas(interaction)













    @dj.command(name="disponíveis", description="📻⠂Mostra a lista completa de músicas disponíveis no bot.")
    async def todas_musicas_slash(self, interaction: discord.Interaction):
        await self.todas_musicas(interaction)
















    @dj.command(name="mover", description="🔊⠂Move o bot para outro canal de voz temporariamente.")
    @app_commands.describe(canal="Canal de voz para onde mover o bot.")
    async def mover_canal_slash(self, interaction: discord.Interaction, canal: discord.VoiceChannel):
        #if interaction.user.id != DONOID:
        #    await interaction.response.send_message("Ei ei~ esse comando é exclusivo do dono do bot, viu? Kyu~ 💛",ephemeral=True)           
        #    return

        await interaction.response.defer(ephemeral=True)
        vc_atual = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        try:
            # INDICA UM NOVO CANAL TEMPORARIO
            self.temp_channel = canal  # <-- registra canal temporário
            self.status_msg = None
            if vc_atual and vc_atual.is_connected():
                await vc_atual.disconnect(force=True)
            await interaction.followup.send( f"🎧 Kyu~ prontinho! A alteração foi feita com sucesso 💖 Agora o canal temporário de reprodução é **{canal.name}**!" )

        except Exception as e:
            await interaction.followup.send( f"🎧 Kyu… deu um errinho aqui 😿 Não consegui me mover para o canal {canal.mention}. Tenta de novo em alguns instantes, tá?" )
            print(f"🚨 Falha ao mover o bot para o canal de voz: {e}")




















    @dj.command(name="pedido", description="🎶⠂Peça uma música para a dj tocar logo após a atual.")
    @app_commands.describe(música="Escolha a música que será tocada em seguida.")
    async def tocar_slash(self, interaction: discord.Interaction, música: str):
        # Verifica se a DJ (bot) está no mesmo canal de voz

        vc_atual = discord.utils.get(self.client.voice_clients, guild=interaction.guild)

        if not vc_atual or not vc_atual.channel or interaction.user.voice is None or vc_atual.channel != interaction.user.voice.channel:
            await interaction.response.send_message( "🎧 Ei, ei~ kyu! Você precisa estar no mesmo canal de voz que eu pra fazer um pedido, viu?", ephemeral=True , delete_after = 20)
            return
        path = os.path.join(self.music_folder, música)

        if not os.path.exists(path):
            await interaction.response.send_message( "🎧 Hmm~ kyu… procurei direitinho, mas essa música não tá no meu sistema. Que tal tentar outra pra gente curtir juntinhos?", ephemeral=True , delete_after = 20)
            return

        # define como a próxima música
        self.pedidos.append(path)  # adiciona na fila
        await interaction.response.send_message(f"🎶 Pedido aceito~ kyu! **{música}** já já entra no ar pra você aproveitar.", ephemeral=True , delete_after = 20)







    @tocar_slash.autocomplete('música')
    async def autocomplete_musicas(self, interaction: discord.Interaction, current: str):
        files = [f for f in os.listdir(self.music_folder) if f.endswith(".mp3")]
        return [ app_commands.Choice(name=f, value=f) for f in files if current.lower() in f.lower()][:25]  # Discord permite até 25 sugestões
















async def setup(client:commands.Bot) -> None:
  await client.add_cog(MusicBot(client))
