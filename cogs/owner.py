import discord,os,requests,json,datetime,pytz,asyncio
from discord.ext import commands
from discord import app_commands
from cogs.essential.host import informação,status,restart , obter_nome_bot
from dotenv import load_dotenv


#CARREGA E LE O ARQUIVO .env na raiz
load_dotenv(os.path.join(os.path.dirname(__file__), '.env')) #load .env da raiz
DONOID = int(os.getenv("DONO_ID")) #acessa e define o id do dono


#Função status
async def botstatus(self,interaction):
    await interaction.response.defer()
    fuso = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now().astimezone(fuso)
    try:
      try:
        res_information , host = await informação(self.client.user.name)
        res_status, host = await status(self.client.user.name)
        

        if host == "squarecloud":
          resposta = discord.Embed(
                  colour=discord.Color.yellow(),
                  title=f"🦊┃Informações do {self.client.user.name}",
                  description=f"{res_information['response']['desc']}"
              )
          resposta.set_thumbnail(url=f"{self.client.user.avatar.url}")
          resposta.add_field(name="🖥️⠂squarecloud", value=f"```{res_information['response']['cluster']}```", inline=True)
          resposta.add_field(name="👨‍💻⠂Linguagem", value=f"```{res_information['response']['language']}```", inline=True)
          resposta.add_field(name="🦊⠂Dono", value=f"<@{DONOID}>", inline=True)
          resposta.add_field(name="📊⠂Ram", value=f"```{(res_status['response']['ram'])} / {res_information['response']['ram']} MB```", inline=True)
          resposta.add_field(name="🌡⠂CPU", value=f"```{res_status['response']['cpu']}```", inline=True)
          resposta.add_field(name="🕐⠂Uptime", value=f"<t:{round(res_status['response']['uptime']/1000)}:R>", inline=True)
          resposta.add_field(name="🌐⠂Rede", value=f"```{res_status['response']['network']['total']}```", inline=True)
          resposta.add_field(name="🏓⠂Ping", value=f"```{round(self.client.latency * 1000)}ms```", inline=True)
          resposta.add_field(name="🔮⠂Menção", value=f"<@{self.client.user.id}>", inline=True)
          resposta.add_field(name="🕐⠂Hora Sistema", value=f"```{now.strftime('%d/%m/%y - %H:%M')}```", inline=True)
          resposta.add_field(name="🆔⠂Bot ID", value=f"```{self.client.user.id}```", inline=True)
          resposta.add_field(name="🍀⠂Ambiente", value=f"```Produção```", inline=True)

        if host == "discloud":
          resposta = discord.Embed(
                  colour=discord.Color.yellow(),
                  title=f"🦊┃Informações do {self.client.user.name}",
                  description=f"🖥️⠂Discloud - {res_information['apps']['name']}"
              )
          resposta.set_thumbnail(url=f"{self.client.user.avatar.url}")
          resposta.add_field(name="👨‍💻⠂Linguagem", value=f"```{res_information['apps']['lang']}```", inline=True)
          resposta.add_field(name="🦊⠂Dono", value=f"<@{DONOID}>", inline=True)
          resposta.add_field(name="📊⠂Ram", value=f"```{(res_status['apps']['memory'])}```", inline=True)
          resposta.add_field(name="🗄️⠂Armazenamento", value=f"```{res_status['apps']['ssd']}```", inline=True)
          resposta.add_field(name="🌡⠂CPU", value=f"```{res_status['apps']['cpu']}```", inline=True)
          resposta.add_field(name="🕐⠂Uptime", value=f"{res_status['apps']['last_restart']}", inline=True)
          resposta.add_field(name="🌐⠂Rede", value=f"```⬇️ {res_status['apps']['netIO']['down']}/⬆️ {res_status['apps']['netIO']['up']}```", inline=True)
          resposta.add_field(name="🏓⠂Ping", value=f"```{round(self.client.latency * 1000)}ms```", inline=True)
          resposta.add_field(name="🔮⠂Menção", value=f"<@{self.client.user.id}>", inline=True)
          resposta.add_field(name="🕐⠂Hora Sistema", value=f"```{now.strftime('%d/%m/%y - %H:%M')}```", inline=True)
          resposta.add_field(name="🆔⠂Bot ID", value=f"```{self.client.user.id}```", inline=True)
          resposta.add_field(name="🍀⠂Ambiente", value=f"```Produção```", inline=True)

        await interaction.followup.send(embed=resposta)
      except:
        resposta = discord.Embed(
                colour=discord.Color.yellow(),
                title=f"🦊┃Informações do {self.client.user.name}",
                description=f"DJ Braixen, sem dados de hospedagem.."
            )
        resposta.set_thumbnail(url=f"{self.client.user.avatar.url}")
        resposta.add_field(name="🍀⠂Ambiente", value=f"```Produção```", inline=True)

        await interaction.followup.send(embed=resposta)
    except Exception as e:
      await interaction.followup.send("<:BH_Braix_Shocked:1154338787757932585>┃ A API da Square não me respondeu, ou o meu dono não configurou ela corretamente no meu sistema...\n<:BH_Braix:1154338509839143023>┃ Confira o erro gerado: {}".format(e))
      print(e)





#----------------- CLASSE PRINCIPAL
class owner(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client

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




  @commands.Cog.listener()
  async def on_message(self,message):
  # RETORNO DO BRIX CASO ALGUEM MENCIONE ELE SEM MAIS NENHUMA PALAVRA ADICIONAL
    if f"<@{self.client.user.id}>" in message.content and message.author != self.client.user:
      resposta = discord.Embed( 
        colour=discord.Color.yellow(),
          description= "Preparado para curtir muita musica pokémon aqui na Braixen's House\n\nVenha passar um tempinho comigo em <#1229394932113084518> onde iremos deslizar nas ondas sonoras de varias musicas do mundo pokémon com sua DJ favorita."
        )
      
      resposta.set_author(name= "Kyuuu! Olá, sou a {}~!".format(self.client.user.name) ,icon_url=self.client.user.avatar.url)
      resposta.set_thumbnail(url=self.client.user.avatar.url)
      resposta.set_footer(text="Uma DJ exclusiva da Braixen's House ~kyuu!",icon_url=self.client.user.avatar.url)
      await message.reply(embed=resposta)






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
