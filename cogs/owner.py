import discord,os,requests,json,datetime,pytz,asyncio
from discord.ext import commands , tasks
from discord import app_commands
from cogs.essential.host import informação,status,restart , obter_nome_bot
from dotenv import load_dotenv






#CARREGA E LE O ARQUIVO .env na raiz
load_dotenv(os.path.join(os.path.dirname(__file__), '.env')) #load .env da raiz
DONOID = int(os.getenv("DONO_ID")) #acessa e define o id do dono
CHANNEL_ID = int(os.getenv("RADIO_CHANNEL_ID"))
















#Função status
async def botstatus(self, interaction: discord.Interaction):
    await interaction.response.defer()
    fuso = pytz.timezone("America/Sao_Paulo")
    now = datetime.datetime.now().astimezone(fuso)

    try:
        res_information, host = await informação(self.client.user.name)
        res_status, host = await status(self.client.user.name)
        ambiente = "Produção"
        # ==========================================
        # SQUARECLOUD
        if host == "squarecloud":
            descricao = (
                f"## 🦊┃Informações do {self.client.user.name}\n"
                f"{res_information['response']['desc'] or 'Sem descrição'}\n\n"

                f"### 🖥️┃Hospedagem SquareCloud\n"
                f"**🗄️┃Cluster:** `{res_information['response']['cluster']}`\n"
                f"**👨‍💻┃Linguagem:** `{res_information['response']['language']}`\n"
                f"**📊┃RAM:** `{res_status['response']['ram']} / {res_information['response']['ram']} MB`\n"
                f"**🌡️┃CPU:** `{res_status['response']['cpu']}`\n"
                f"**🌐┃Rede:** `{res_status['response']['network']['total']}`\n"
                f"**🕐┃Uptime:** <t:{round(res_status['response']['uptime']/1000)}:R>\n\n"

                f"### 🤖┃Bot\n"
                f"**🏓┃Ping:** `{round(self.client.latency * 1000)}ms`\n"
                f"**🔮┃Menção:** <@{self.client.user.id}>\n"
                f"**🆔┃Bot ID:** `{self.client.user.id}`\n"
                f"**🦊┃Dono:** <@{DONOID}>\n"
                f"**🕐┃Hora Sistema:** `{now.strftime('%d/%m/%y - %H:%M')}`\n"
                f"**🍀┃Ambiente:** `{ambiente}`"
            )

        # ==========================================
        # DISCLOUD
        else:
            descricao = (
                f"## 🦊┃Informações do {self.client.user.name}\n"
                f"Hospedado via Discloud\n\n"

                f"### 🖥️┃Hospedagem Discloud\n"
                f"**🗄️┃Cluster:** `{res_information['apps']['clusterName']}`\n"
                f"**👨‍💻┃Linguagem:** `{res_information['apps']['lang']}`\n"
                f"**📊┃RAM:** `{res_status['apps']['memory']}`\n"
                f"**🗄️┃Armazenamento:** `{res_status['apps']['ssd']}`\n"
                f"**🌡️┃CPU:** `{res_status['apps']['cpu']}`\n"
                f"**🌐┃Rede:** `⬇️ {res_status['apps']['netIO']['down']} / ⬆️ {res_status['apps']['netIO']['up']}`\n"
                f"**🕐┃Uptime:** `{res_status['apps']['last_restart']}`\n\n"

                f"### 🤖┃Bot\n"
                f"**🏓┃Ping:** `{round(self.client.latency * 1000)}ms`\n"
                f"**🔮┃Menção:** <@{self.client.user.id}>\n"
                f"**🆔┃Bot ID:** `{self.client.user.id}`\n"
                f"**🦊┃Dono:** <@{DONOID}>\n"
                f"**🕐┃Hora Sistema:** `{now.strftime('%d/%m/%y - %H:%M')}`\n"
                f"**🍀┃Ambiente:** `{ambiente}`"
            )

        resposta = discord.Embed( colour=discord.Color.yellow(), description=descricao )
        resposta.set_thumbnail(url=self.client.user.avatar.url)
        resposta.set_footer( text=f"{self.client.user.name} • Sistema de Status" )
        await interaction.followup.send(embed=resposta)

    except Exception as e:
        await interaction.followup.send(f"<:BH_Braix_Shocked:1154338787757932585>┃ A API da hospedagem não respondeu corretamente...\n"f"```py\n{e}\n```")
        print(e)




















#----------------- CLASSE PRINCIPAL
class owner(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client
    self.limit_ram = False









  @commands.Cog.listener()
  async def on_ready(self):
    print("🦊 - Modúlo Owner carregado.")

    # Editando o Nome do bot para o padrão que está na host
    novo_nome = obter_nome_bot()
    if self.client.user.name != novo_nome:
      try:
        await self.client.user.edit(username=novo_nome)
        print(f"🤖 - Nome do bot foi alterado para {novo_nome}")
      except discord.HTTPException as e:
        print(f"❌ - Erro ao alterar nome do bot: {e}")

    await asyncio.sleep(20)
    if not self.memory_check.is_running():
      self.memory_check.start()  # Inicia a verificação de memoria.














  @commands.Cog.listener()
  async def on_message(self,message):
  # RETORNO DO BRIX CASO ALGUEM MENCIONE ELE SEM MAIS NENHUMA PALAVRA ADICIONAL
    if f"<@{self.client.user.id}>" in message.content and message.author != self.client.user:
      resposta = discord.Embed( 
        colour=discord.Color.yellow(),
          description= f"Preparado para curtir muita musica pokémon aqui na Braixen's House\n\nVenha passar um tempinho comigo em <#{CHANNEL_ID}> onde iremos deslizar nas ondas sonoras de varias musicas do mundo pokémon com sua DJ favorita."
        )
      
      resposta.set_author(name= "Kyuuu! Olá, sou a {}~!".format(self.client.user.name) ,icon_url=self.client.user.avatar.url)
      resposta.set_thumbnail(url=self.client.user.avatar.url)
      resposta.set_footer(text="Uma DJ exclusiva da Braixen's House ~kyuu!",icon_url=self.client.user.avatar.url)
      await message.reply(embed=resposta)















  
  # Monitorar Memoria no sistema DJ
  @tasks.loop(seconds=25)
  async def memory_check(self):
    try:
      if self.limit_ram is False:
        res_information , host = await informação(self.client.user.name)
        if host == "squarecloud":
          total_ram = int(res_information['response']['ram'])
          self.limit_ram = total_ram - int(total_ram * 0.05)

        elif host == "discloud":
          total_ram = int(res_information['apps']['ram'])
          self.limit_ram = total_ram - int(total_ram * 0.05)
        print(f"🤖 - LIMITE DE RAM DEFINIDO PARA: {self.limit_ram} ")
      res_status, host = await status(self.client.user.name)

      if host == "squarecloud":
        ram_str = res_status['response']['ram']
      elif host == "discloud":
        ram_str = res_status['apps']['memory'].split('/')[0]

      ram_value = float(ram_str.replace("MB", "").strip())
      self._falhas_memoria = 0  # resetar contador se for bem-sucedido

      if ram_value >= self.limit_ram:
          print(f"🤖 - Uso de RAM alto!\nTotal de Ram usado:{ram_value} / {self.limit_ram}\nReiniciando o app pela {host}...")
          await restart(self.client.user.name)

    except Exception as e:
        self._falhas_memoria += 1
        print(f"🤖 - falha ao checar memoria na hospedagem ({self._falhas_memoria}/50)...\nError: {e}")
        if self._falhas_memoria >= 50:
            print("🚨 - Muitas falhas consecutivas ao checar memória. Reiniciando preventivamente...")
            await asyncio.sleep(10)
            await restart(self.client.user.name)




















    #GRUPO BOT 
  bot=app_commands.Group(name="dj",description="Comandos de gestão do sistema DJ Braixen.",allowed_installs=app_commands.AppInstallationType(guild=True,user=False),allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=False, private_channel=False))













  #COMANDO PING
  @bot.command(name="ping",description='🤖⠂Exibe o ping da Dj Braixen.')
  async def ping(self,interaction: discord.Interaction):
    bot_latency = round(self.client.latency * 1000)  # Convertendo de segundos para milissegundos

    start_time = discord.utils.utcnow()
    await interaction.response.defer()
    end_time = discord.utils.utcnow()

    api_latency = round((end_time - start_time).total_seconds() * 1000)
    resposta = discord.Embed( colour=discord.Color.yellow(), title="🏓┃Pong ~kyu", description="**🤖┃Latência:** {}ms. (`{:,.2f} Segundos`)\n**📶┃Api:** {}ms. (`{:,.2f} Segundos`)".format(bot_latency,bot_latency/1000,api_latency,api_latency/1000))
    resposta.set_thumbnail(url="https://cdn.discordapp.com/attachments/1346125499474247731/1346126144512196720/1579523806.png?ex=67f531aa&is=67f3e02a&hm=e52fee2a59cc7082561977aabcf8f23033c7fc274c78daeaea246c34747017bd&")
    await interaction.followup.send(embed=resposta)












  #COMANDO STATUS BOT
  @bot.command(name="status",description='🤖⠂Exibe informações sobre o status de DJ Braixen.')
  async def botstatusslash(self, interaction: discord.Interaction):
    await botstatus(self,interaction)
  












  #COMANDO RESTART BOT NA HOST
  @bot.command(name="restart",description='🤖⠂Reinicia a DJ Braixen na Host.')
  async def botstatusslash(self, interaction: discord.Interaction):
    if interaction.user.id == DONOID:
      await interaction.response.defer()
      await interaction.followup.send(f"Solicitando seu pedido...")
      retorno, host = await restart(self.client.user.name)
      await interaction.followup.send(f"Retorno da sua solicitação: {retorno['status']} em {host}")

    await interaction.response.send_message("Este comando é somente para o Dono do bot usar ~kyuu.")
   
    
















async def setup(client:commands.Bot) -> None:
  await client.add_cog(owner(client))
