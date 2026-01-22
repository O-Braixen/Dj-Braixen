import discord, os, platform, datetime , logging
from os import listdir
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN_RADIO = os.getenv("DISCORD_TOKEN_RADIO") 

# Reduzir o nível de log do discord
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.WARNING)  # Ou ERROR se quiser esconder ainda mais

# Se quiser esconder logs de partes específicas (como voice_state ou player):
logging.getLogger('discord.voice_state').setLevel(logging.WARNING)
logging.getLogger('discord.player').setLevel(logging.WARNING)
#redução de logs
logging.getLogger('discord').setLevel(logging.CRITICAL)


class Client(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=commands.when_mentioned, intents=discord.Intents().all())
        self.synced = False
        self.cogslist = []
        for cog in listdir("cogs"):
            if cog.endswith(".py"):
                cog = os.path.splitext(cog)[0]
                self.cogslist.append('cogs.' + cog)




    async def setup_hook(self):
        for ext in self.cogslist:
            await self.load_extension(ext)




    async def on_ready(self):
        await self.wait_until_ready()
        print("\n" + "="*70)
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            print(f"\n\n💻 - Comandos sincronizados: {self.synced}")
        print(f"🐍 - Python: {platform.python_version()} | discord.py: {discord.__version__}")
        print(f"🦊 - O Bot {self.user} já está online e disponível")
        print(f"💖 - Guildas: {len(self.guilds)} | Usuários: {len(self.users)}")
        print(f"⏰ - A hora no sistema é {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n\n")
        print("="*70 + "\n")






# Criar instância do bot principal
djbraixen = Client()
djbraixen.run(TOKEN_RADIO)