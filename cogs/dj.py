import discord, random, asyncio, os, datetime , pytz , aiohttp , gc , subprocess , json, ctypes, logging
from discord.ext import commands , tasks
from pathlib import Path
from discord import app_commands
from cogs.essential.host import restart
from dotenv import load_dotenv
from functools import partial

logger = logging.getLogger('djbraixen')






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
        os.makedirs("musicas_repo", exist_ok=True)
        self.music_folder = os.path.join("musicas_repo", "musicas")  # Nova pasta de músicas
        self.announcement_folder = os.path.join("musicas_repo", "anuncios")  # Pasta de anúncios
        self.current_announcement = False   #ANUNCIO ATUAL
        self.ffmpeg_options = {
            'before_options': ' -nostdin',
            'options': '-vn'
        }
        self.status_msg = None  # Para guardar a mensagem de status
        self._falhas_memoria = 0  # inicializa o contador
        self.played_songs_file = os.path.join("musicas_repo", "played_songs.json")
        self.played_songs = []
        self.pedidos = []  # lista de pedidos

        # Controle de concorrência e cache inteligente de RAM
        self.play_task = None
        self.songs_cache = {}
        self.available_songs = []
        self.available_jingles = []
        self.available_intros = []
        self.available_announcements = []

        # Carregar do arquivo se existir
        if os.path.exists(self.played_songs_file):
            try:
                with open(self.played_songs_file, "r", encoding="utf-8") as f:
                    self.played_songs = json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ - Erro ao carregar played_songs.json: {e}")
        else:
            # Cria o arquivo vazio
            with open(self.played_songs_file, "w", encoding="utf-8") as f:
                json.dump([], f)

        self.consecutive_failed_connections = 0
        self.consecutive_idle_ticks = 0

        # Inicializa o cache de músicas em memória
        self.atualizar_cache_musicas()
        if not self.limpar_memoria_periodica.is_running():
            self.limpar_memoria_periodica.start()

    @tasks.loop(minutes=5)
    async def limpar_memoria_periodica(self):
        def obter_ram_atual():
            try:
                # Método nativo no Linux (Docker/SquareCloud)
                if os.path.exists("/proc/self/status"):
                    with open("/proc/self/status", "r") as f:
                        for line in f:
                            if line.startswith("VmRSS:"):
                                return int(line.split()[1]) / 1024
                # Fallback genérico para Windows local
                import psutil
                process = psutil.Process(os.getpid())
                return process.memory_info().rss / (1024 * 1024)
            except Exception:
                return 0.0

        try:
            ram_antes = obter_ram_atual()
            
            # Força o Linux glibc (Docker/SquareCloud) a liberar memória retida para o S.O.
            libc = ctypes.CDLL(None)
            libc.malloc_trim(0)
            
            ram_depois = obter_ram_atual()
            liberado = max(ram_antes - ram_depois, 0.0)
            
            if ram_antes > 0 and ram_depois > 0:
                # Prints de memória removidos para evitar spam no console
                pass
            else:
                pass
        except Exception:
            pass

    def atualizar_cache_musicas(self):
        try:
            if os.path.exists(self.music_folder):
                songs = []
                for root, _, files in os.walk(self.music_folder):
                    for f in files:
                        if f.endswith(".mp3"):
                            rel_path = os.path.relpath(os.path.join(root, f), self.music_folder)
                            songs.append(rel_path.replace("\\", "/"))
                self.available_songs = songs
            else:
                self.available_songs = []

            if os.path.exists(self.announcement_folder):
                jingles = []
                intros = []
                announcements = []
                for root, _, files in os.walk(self.announcement_folder):
                    for f in files:
                        if f.endswith(".mp3"):
                            full_path = os.path.join(root, f)
                            basename = os.path.basename(f)
                            if basename.startswith("jingle"):
                                jingles.append(full_path)
                            elif basename.startswith("pedidos"):
                                intros.append(full_path)
                            elif basename[:-4].replace("H", "").isdigit():
                                announcements.append(full_path)
                self.available_jingles = jingles
                self.available_intros = intros
                self.available_announcements = announcements
            else:
                self.available_jingles = []
                self.available_intros = []
                self.available_announcements = []

            # Limpa chaves obsoletas do cache de metadados para economizar RAM
            todos_arquivos = set(self.available_songs)
            for jingle_path in self.available_jingles:
                todos_arquivos.add(os.path.basename(jingle_path))
            for intro_path in self.available_intros:
                todos_arquivos.add(os.path.basename(intro_path))
            for ann_path in self.available_announcements:
                todos_arquivos.add(os.path.basename(ann_path))

            chaves_para_remover = [k for k in self.songs_cache if os.path.basename(k) not in todos_arquivos]
            for k in chaves_para_remover:
                del self.songs_cache[k]

            logger.info(f"💾 - Cache de Músicas Atualizado: {len(self.available_songs)} músicas, {len(self.available_jingles)} jingles, {len(self.available_intros)} intros, {len(self.available_announcements)} anúncios horários.")
        except Exception as e:
            logger.error(f"⚠️ - Erro ao atualizar cache de músicas: {e}")









    
        # LIGANDO O BOT
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("🎵 - Modúlo DJ carregado.")
        await asyncio.sleep(5)        
        await self.reproduzir()
        await self.verificar_arquivos()
        
        









      # AGENDA A VERIFICAÇÃO PARA RODAR O ANUNCIO
    async def verificar_arquivos(self):
        logger.info("🌐 - Iniciando verificação de arquivos.")
        await self.baixar_arquivos()














    
    # FUNÇÃO PARA BAIXAR OS ARQUIVOS DO REPOSITÓRIO
    async def baixar_arquivos(self, tentativa=1):
        if tentativa > MAX_TENTATIVAS:
            logger.error("❌ - Limite de tentativas atingido. Abortando download.")
            return
        if GITHUB_API_URL_BASE is None or GIT_TOKEN is None:
            logger.error("❌ - SEM DADOS DE REPOSITORIO, VERIFIQUE O .ENV")
            return
        
        async def obter_arquivos_repositorio_recursivo(session, path_atual):
            url = f"{GITHUB_API_URL_BASE}/{path_atual}"
            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    logger.error(f"❌ - Erro ao acessar {url}: {response.status}")
                    return []
                conteudo = await response.json()
                arquivos = []
                for item in conteudo:
                    if item["type"] == "file":
                        arquivos.append(item)
                    elif item["type"] == "dir":
                        await asyncio.sleep(0.5)  # Pequeno delay para evitar rate limits
                        sub_arquivos = await obter_arquivos_repositorio_recursivo(session, item["path"])
                        arquivos.extend(sub_arquivos)
                return arquivos

        # Semáforo para limitar downloads simultâneos e não sobrecarregar a RAM/Rede
        semaforo = asyncio.Semaphore(2)
        async def baixar_arquivo(session, item):
            path_relativo = item["path"]
            caminho_arquivo = os.path.join("musicas_repo", path_relativo)
            if os.path.exists(caminho_arquivo):
                return
            os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
            async with semaforo:
                try:
                    async with session.get(item["download_url"]) as download_response:
                        if download_response.status == 200:
                            # Stream download in chunks to minimize RAM usage
                            with open(caminho_arquivo, "wb") as f:
                                async for chunk in download_response.content.iter_chunked(65536):
                                    f.write(chunk)
                            logger.info(f"✅ - Baixado: {path_relativo}")
                            await asyncio.sleep(0.5)  # Pequeno delay para evitar taxa limite
                        else:
                            logger.error(f"❌ - Erro ao baixar {path_relativo}: Status {download_response.status}")
                except Exception as e:
                    logger.error(f"❌ - Exceção ao baixar {path_relativo}: {e}")

        async with aiohttp.ClientSession() as session:
            remote_files = []
            for pasta_remota in PASTAS:
                logger.info(f"🌐 - Mapeando arquivos da pasta remota: {pasta_remota}")
                arquivos_pasta = await obter_arquivos_repositorio_recursivo(session, pasta_remota)
                remote_files.extend(arquivos_pasta)

            # Mapear caminhos relativos do repo remoto
            arquivos_repo = {item["path"].replace("\\", "/"): item for item in remote_files}

            # Listar arquivos locais
            arquivos_locais = set()
            for pasta_remota in PASTAS:
                pasta_local = os.path.join("musicas_repo", pasta_remota)
                if os.path.exists(pasta_local):
                    for root, _, files in os.walk(pasta_local):
                        for f in files:
                            full_path = os.path.join(root, f)
                            rel_path = os.path.relpath(full_path, "musicas_repo")
                            arquivos_locais.add(rel_path.replace("\\", "/"))

            # 🧹 REMOVE arquivos locais que não existem mais no repo
            for arquivo in arquivos_locais - set(arquivos_repo.keys()):
                caminho = os.path.join("musicas_repo", arquivo)
                if os.path.isfile(caminho):
                    try:
                        os.remove(caminho)
                        logger.info(f"🗑️ - Removido (não existe no repo): {arquivo}")
                    except Exception as e:
                        logger.error(f"⚠️ - Erro ao remover {arquivo}: {e}")

            # 🧹 Limpa diretórios vazios locais
            for pasta_remota in PASTAS:
                pasta_local = os.path.join("musicas_repo", pasta_remota)
                if os.path.exists(pasta_local):
                    for root, dirs, _ in os.walk(pasta_local, topdown=False):
                        for d in dirs:
                            dir_path = os.path.join(root, d)
                            try:
                                if not os.listdir(dir_path):
                                    os.rmdir(dir_path)
                                    logger.info(f"🗑️ - Diretório vazio removido: {dir_path}")
                            except Exception:
                                pass

            # ⬇️ BAIXA arquivos novos
            tarefas = []
            for path_rel, item in arquivos_repo.items():
                tarefas.append(baixar_arquivo(session, item))
            
            if tarefas:
                await asyncio.gather(*tarefas)

        self.atualizar_cache_musicas()
        logger.info("✅ - Biblioteca de músicas 100% sincronizada com o GitHub")

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
                    logger.error(f"❌ - Erro ao limpar mensagens do canal: {e}")

                if not self.check_music.is_running():
                    self.channel = channel
                    self.check_music.start()  # Verificação contínua.
                if not self.hourly_announcements.is_running():
                    self.hourly_announcements.start()  # Inicia sistema de anúncios
                
            except Exception as e:
                logger.error(f"❌ - ({self.client.user}) Erro ao conectar ao canal de voz: {e}")
        else:
            logger.error(f"❌ - ({self.client.user}) Canal de voz não encontrado.")









        #SALVAR O JSON COM AS MUSICAS JÀ TOCADAS
    def save_played_songs(self):
        try:
            with open(self.played_songs_file, "w", encoding="utf-8") as f:
                json.dump(self.played_songs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ - Erro ao salvar played_songs.json: {e}")












        # PROCURA UMA MUSICA ALEATORIA E SELECIONA
    def get_random_song(self):
        try:
            files = self.available_songs
            remaining_songs = [f for f in files if f not in self.played_songs]

            if not remaining_songs:
                self.played_songs.clear()
                remaining_songs = files

            if not remaining_songs:
                return None

            song = random.choice(remaining_songs)
            self.played_songs.append(song)
            return song

        except Exception as e:
            logger.error(f"❌ - Erro ao obter música aleatória do cache: {e}")
            return None

        # PROCURA UM JINGLE ALEATORIO E SELECIONA
    def get_random_jingle(self):
        try:
            return random.choice(self.available_jingles) if self.available_jingles else None
        except Exception as e:
            logger.error(f"❌ - Erro ao obter jingle aleatório do cache: {e}")
            return None

        # PROCURA UMA INTRO DE PEDIDO ALEATÓRIA
    def get_random_pedido_intro(self):
        try:
            return random.choice(self.available_intros) if self.available_intros else None
        except Exception as e:
            logger.error(f"❌ - Erro ao obter intro de pedido aleatório do cache: {e}")
            return None













        # PUXA UM ANUNCIO EM UM DETEMINADO HORARIO
    def get_hourly_announcement(self):
        current_hour = datetime.datetime.now().astimezone(pytz.timezone('America/Sao_Paulo')).hour
        filename = f"{current_hour}H.mp3"
        filepath = os.path.join(self.announcement_folder, filename)
        return filepath if filepath in self.available_announcements else False
    











    # Pega duração da música
    async def get_duration(self, path):
        # Retorna duração em cache para evitar execução repetida de subprocessos ffprobe
        if path in self.songs_cache and "duracao" in self.songs_cache[path]:
            return self.songs_cache[path]["duracao"]

        try:
            proc = await asyncio.create_subprocess_exec(
                "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            try:
                out, _ = await asyncio.wait_for(proc.communicate(), timeout=10.0)
                duracao = float(out.decode().strip())
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                logger.warning(f"⚠️ - Timeout ao obter duração da música com ffprobe: {path}")
                duracao = 180.0
            except Exception:
                duracao = 180.0
            
            if path not in self.songs_cache:
                self.songs_cache[path] = {}
            self.songs_cache[path]["duracao"] = duracao
            return duracao
        except Exception as e:
            logger.error(f"❌ - Erro ao obter duração da música com ffprobe: {e}")
            return 180.0  # Duração fallback padrão (3 minutos)




















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
                        options=f"-af 'afade=t=in:ss=0:d=3,afade=t=out:st={fade_out_start}:d=3' -vn"
                    )
                else:
                    ffmpeg_source = discord.FFmpegPCMAudio(path, **self.ffmpeg_options)

                source = discord.PCMVolumeTransformer(ffmpeg_source, volume=0.5)
                if fade :
                    await self.update_status(path, vc , duration)

                def after_playing(error):
                    if error:
                        logger.error(f"❌ - Erro ao reproduzir: {error}")
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
                    if ffmpeg_source and hasattr(ffmpeg_source, "_process") and ffmpeg_source._process:
                        try:
                            ffmpeg_source._process.kill()
                            ffmpeg_source._process.wait()
                        except Exception:
                            pass
                except Exception as e:
                    logger.error(f"🗑️ - Erro no cleanup: {e}")
                del source
                del ffmpeg_source
                gc.collect()

        try:
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
                            logger.error("❌ - Nenhuma música encontrada na pasta.")
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
                    logger.error("❌ - Nenhuma música encontrada na pasta.")
                    await asyncio.sleep(60)
                    continue
                path = os.path.join(self.music_folder, song)
                await _tocar(vc, path, fade=True)

                if not skip_jingle_next and random.random() < 0.2:
                    jingle = self.get_random_jingle()
                    if jingle and await self.verify_and_cleanup_audio_file(jingle):
                        await _tocar(vc, jingle, fade=False)
        except asyncio.CancelledError:
            logger.info("🎵 - Task de reprodução cancelada limpamente.")
            raise
        except Exception as e:
            logger.error(f"❌ - Erro no loop principal de reprodução: {e}")

















               






    #Verifica se um arquivo de áudio é válido usando ffmpeg.
    async def verify_and_cleanup_audio_file(self, path, update_cache=True):
        # Se já estiver no cache como verificado e o arquivo ainda existe, ignora verificação externa
        if path in self.songs_cache and self.songs_cache[path].get("valido") is True:
            if os.path.exists(path):
                return True
            else:
                # Remove do cache se o arquivo foi excluído fisicamente
                del self.songs_cache[path]

        try:
            # Usando ffmpeg de forma assíncrona com redirecionamento de stdin para evitar bloqueios/timeouts
            proc = await asyncio.create_subprocess_exec(
                'ffmpeg', '-v', 'error', '-i', path, '-f', 'null', '-',
                stdin=asyncio.subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
                exit_code = proc.returncode
                stderr_output = stderr.decode(errors='replace').strip()
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                logger.warning(f"⚠️ - Timeout na verificação do arquivo com ffmpeg: {path}")
                exit_code = -1
                stderr_output = "Timeout"

            if exit_code != 0 or "Invalid data" in stderr_output or "Header missing" in stderr_output:
                logger.info(f"🗑️ - Arquivo corrompido ou inválido. Deletando: {path}")
                logger.warning(f"⚠️ stderr: {stderr_output}")
                try:
                    os.remove(path)
                except Exception as e:
                    logger.error(f"⚠️ - Erro ao deletar arquivo: {e}")
                
                if path in self.songs_cache:
                    del self.songs_cache[path]
                if update_cache:
                    self.atualizar_cache_musicas()
                return False

            if path not in self.songs_cache:
                self.songs_cache[path] = {}
            self.songs_cache[path]["valido"] = True
            return True

        except Exception as e:
            logger.error(f"⚠️ - Erro ao verificar arquivo com ffmpeg: {e}")
            return False



















      

    #Verifica se a música ainda está tocando e se o bot está conectado.
    @tasks.loop(seconds=20)
    async def check_music(self):
        channel = getattr(self, "temp_channel", None) or self.client.get_channel(self.voice_channel_id)
        if not channel:
            logger.error("❌ - [check_music] Canal de voz principal/temporário não configurado ou não encontrado.")
            return

        backoff_delay = 1  # começa com 1 segundo
        reconnected_successfully = False

        for attempt in range(5):  # tenta reconectar no máximo 5 vezes por checagem
            vc = discord.utils.get(self.client.voice_clients, guild=channel.guild)

            if not vc or not vc.is_connected():
                # Para evitar conflitos, cancela a task de reprodução antiga caso ela estivesse ativa
                if self.play_task and not self.play_task.done():
                    self.play_task.cancel()
                    try:
                        await self.play_task
                    except asyncio.CancelledError:
                        pass

                try:
                    vc = channel.guild.voice_client
                    if not vc:
                        vc = await channel.connect(reconnect=True)
                    
                    if self.play_task is None or self.play_task.done():
                        self.play_task = asyncio.create_task(self.play_music(vc))
                    
                    logger.info(f"🔄️ - Reconectado ao canal de voz: {channel.name}")
                    reconnected_successfully = True
                    break  # reconectado com sucesso, sai do loop
                except Exception as e:
                    logger.error(f"❌ - Erro ao reconectar (tentativa {attempt + 1}): {e}")
                    if vc:
                        try:
                            await vc.disconnect()
                        except Exception:
                            pass
                    await asyncio.sleep(backoff_delay)
                    backoff_delay = min(backoff_delay * 2, 60)  # dobra até máximo de 60s
            else:
                reconnected_successfully = True
                break  # já está conectado

        vc = discord.utils.get(self.client.voice_clients, guild=channel.guild)

        # Se não conseguiu conectar depois de todas as tentativas, incrementa falhas consecutivas
        if not vc or not vc.is_connected() or not reconnected_successfully:
            self.consecutive_failed_connections += 1
            logger.warning(f"⚠️ - Falha na conexão de voz detectada (Sequência de falhas: {self.consecutive_failed_connections}/3)")
            if self.consecutive_failed_connections >= 3:
                logger.critical("🚨 - Múltiplas falhas de conexão. Reiniciando bot por garantia...")
                await restart()
                return
        else:
            self.consecutive_failed_connections = 0

        # Se estava em canal temporário e desconectou, reseta para o canal original
        if not (channel and channel.id == self.voice_channel_id):
            if not vc or not vc.is_connected():
                self.temp_channel = None

        # Tenta reiniciar a música se estiver conectado e parado
        if vc and vc.is_connected():
            if not vc.is_playing() and not vc.is_paused():
                self.consecutive_idle_ticks += 1
                logger.warning(f"⏳ - Bot conectado mas ocioso/sem tocar nada (Sequência de ociosidade: {self.consecutive_idle_ticks}/3)")

                if self.play_task is None or self.play_task.done():
                    logger.info("🔄️ - Música parou. Reiniciando stream...")
                    try:
                        self.play_task = asyncio.create_task(self.play_music(vc))
                    except Exception as e:
                        logger.error(f"❌ - Erro ao reiniciar o stream: {e}")
                        try:
                            await vc.disconnect()
                        except Exception:
                            pass
                        await restart()
                        return

                if self.consecutive_idle_ticks >= 3:
                    logger.critical("🚨 - Bot está conectado mas travado sem tocar áudio. Reiniciando bot...")
                    try:
                        await vc.disconnect()
                    except Exception:
                        pass
                    await restart()
                    return
            else:
                self.consecutive_idle_ticks = 0

        



















        # AGENDA A VERIFICAÇÃO PARA RODAR O ANUNCIO
    @tasks.loop(minutes=5)
    async def hourly_announcements(self):
        now = datetime.datetime.now().astimezone(pytz.timezone('America/Sao_Paulo'))
        next_hour = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        seconds_until_next_hour = (next_hour - now).total_seconds()
        logger.info(f"⏳ - Próximo anúncio em {int(seconds_until_next_hour)} segundos")
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


        logger.info(f"💿 - Tocando Agora: {song} ({tempo_total})")
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
            logger.error(f"❌ - Erro ao atualizar mensagem de status: {e}")











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

        musicas = self.available_songs

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








    @dj.command(name="atualizar", description="Força a verificação e download de músicas do repositório.")
    async def cmd_atualizar_musicas(self, interaction: discord.Interaction):
        if interaction.user.id != DONOID:
            await interaction.response.send_message("❌ - Você não tem permissão para usar este comando.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self.verificar_arquivos()
        await interaction.followup.send("✅ - Verificação e download concluídos!")









    @dj.command(name="verificar", description="🤖⠂Verifica todos os arquivos de música e remove os corrompidos.")
    async def verificar_musicas_slash(self, interaction: discord.Interaction):
        if interaction.user.id != DONOID:
            await interaction.response.send_message("Ei ei~ esse comando é exclusivo do dono do bot, viu? Kyu~ 💛",ephemeral=True)           
            return

        await interaction.response.send_message("🔍 | Yoko na área! Começando a verificação dos arquivos de áudio… kyu~ ✨")
        status_msg = await interaction.original_response()

        # Força nova verificação limpando o cache
        self.songs_cache.clear()

        # Coleta todos os arquivos mp3 das pastas
        todos_arquivos = []
        for pasta in [self.music_folder, self.announcement_folder]:
            if os.path.exists(pasta):
                for root, _, files in os.walk(pasta):
                    for nome_arquivo in files:
                        if nome_arquivo.endswith(".mp3"):
                            caminho_completo = os.path.join(root, nome_arquivo)
                            rel_path = os.path.relpath(caminho_completo, pasta)
                            todos_arquivos.append((caminho_completo, rel_path))

        total = len(todos_arquivos)
        verificados = 0
        arquivos_removidos = []
        lock = asyncio.Lock()

        # Fila assíncrona para processar arquivos sem instanciar milhares de tarefas concorrentes em RAM
        fila = asyncio.Queue()
        for item in todos_arquivos:
            fila.put_nowait(item)

        async def worker():
            nonlocal verificados
            while not fila.empty():
                try:
                    caminho_completo, rel_path = fila.get_nowait()
                except asyncio.QueueEmpty:
                    break

                # update_cache=False para evitar atualizar o cache milhares de vezes repetidas em disco/RAM
                valido = await self.verify_and_cleanup_audio_file(caminho_completo, update_cache=False)

                async with lock:
                    verificados += 1
                    if not valido:
                        arquivos_removidos.append(rel_path)
                fila.task_done()
                await asyncio.sleep(0.2)  # Delay entre verificações para poupar CPU/RAM

        # Task de progresso que atualiza a mensagem a cada 5 segundos
        async def atualizar_progresso():
            while verificados < total:
                await asyncio.sleep(5)
                pct = int((verificados / total) * 100) if total else 100
                try:
                    await status_msg.edit(content=f"🔍 | Conferindo tudinho com atenção… {verificados}/{total} ({pct}%) arquivos analisados, kyuuu~ 👀")
                except Exception:
                    pass

        progresso_task = asyncio.create_task(atualizar_progresso())

        # Limita a 2 workers paralelos para não estourar RAM do sistema
        workers = [asyncio.create_task(worker()) for _ in range(2)]
        await asyncio.gather(*workers)

        progresso_task.cancel()
        try:
            await progresso_task
        except asyncio.CancelledError:
            pass

        self.atualizar_cache_musicas()
        gc.collect()  # Libera a memória acumulada do coletor de lixo

        removidos = len(arquivos_removidos)
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
        if interaction.user.id != DONOID:
            await interaction.response.send_message("Ei ei~ esse comando é exclusivo do dono do bot, viu? Kyu~ 💛",ephemeral=True)           
            return

        await interaction.response.defer(ephemeral=True)
        try:
            # INDICA UM NOVO CANAL TEMPORARIO
            self.temp_channel = canal  # <-- registra canal temporário
            self.status_msg = None
            vc = interaction.guild.voice_client
            # Já conectado
            if vc and vc.is_connected():
                # Move diretamente
                await vc.move_to(canal)
            else:
                vc = await canal.connect(reconnect=True)
            await interaction.followup.send( f"🎧 Kyu~ prontinho! A alteração foi feita com sucesso 💖 Agora o canal temporário de reprodução é **{canal.name}**!" )

        except Exception as e:
            await interaction.followup.send( f"🎧 Kyu… deu um errinho aqui 😿 Não consegui me mover para o canal {canal.mention}. Tenta de novo em alguns instantes, tá?" )
            logger.error(f"🚨 Falha ao mover o bot para o canal de voz: {e}")




















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
        nome_exibicao = os.path.basename(música)
        await interaction.response.send_message(f"🎶 Pedido aceito~ kyu! **{nome_exibicao}** já já entra no ar pra você aproveitar.", ephemeral=True , delete_after = 20)







    @tocar_slash.autocomplete('música')
    async def autocomplete_musicas(self, interaction: discord.Interaction, current: str):
        files = self.available_songs
        # name é o que aparece visualmente no Discord (apenas o nome do arquivo)
        # value é o valor relativo enviado ao comando (ex: "Albuns/Pasta/Musica.mp3")
        choices = []
        for f in files:
            nome_display = os.path.basename(f)
            if current.lower() in f.lower() or current.lower() in nome_display.lower():
                choices.append(app_commands.Choice(name=nome_display, value=f))
                if len(choices) == 25:
                    break
        return choices
















async def setup(client:commands.Bot) -> None:
  await client.add_cog(MusicBot(client))
