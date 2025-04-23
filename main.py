import discord, os, platform, datetime
from os import listdir
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token_radio = os.getenv("DISCORD_TOKEN_RADIO") 




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

        if not self.synced:
            await self.tree.sync()
            self.synced = True
            print(f"\n\n💻 - Comandos sincronizados: {self.synced}")
        print(f"🐍 - Versão do python: {platform.python_version()}")
        print(f"🦊 - O Bot {self.user} já está online e disponível")
        print(f"💖 - Estou em {len(self.guilds)} comunidades com um total de {len(self.users)} membros")
        print(f"⏰ - A hora no sistema é {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n\n")
        

# Criar instância do bot principal
djbraixen = Client()
djbraixen.run(token_radio)