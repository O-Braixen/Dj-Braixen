# Dj-Braixen - Uma Dj personalizada

![bot image](img/dj_braixen_avatar.png)


Codigo em Python de um bot de musica que funciona como uma verdadeira radio com uma Dj carismatica que até faz participação vocal.

Esse codigo é somente referencia para um reproduzir de musica a partir de duas pastas, uma chamada **musicas** e outra chamada **anuncios**, o codigo foi desenvolvido para ser usado diretamente em alguma comunidade, neste caso é simples, o codigo ta programado para sincronizar um repositorio, e a partir disso começa a tocar as musicas, onde que a cada hora verifica se existe algum anuncio para aquele deteminado horario e o toca, bem simples e automatizado.

Para funcionamento do bot é necessario criar um repositorio privado (private) e será nele que você guardará todas as musicas e arquivos de anuncios que serão usados pelo bot, já dentro do repositorio Crie duas pastas uma chamada **musicas** e outra chamada **anuncios** e serão dentro delas que você deve armazenar seus arquivos sempre no formato **.mp3** (outros formatos não são compativeis)


**Como Funciona os anúncios?**

O Bot possui 2 tipos de anuncios, os de horarios fixos que ocorrem sempre em algum horario cheio tipo 9h/10h e assim vai e também os anúncios aleatórios chamados (Jingles) esses jingles podem ser reproduzidos em ordem aleátoria após cada música e também em chamadas quando existe algum pedido de musica de usuários, e você pode colocar quantos Jingles quiser, sempre respeitando essa sequencia aqui.


*Jingles entre as músicas*

📄 jingle-01.mp3
📄 jingle-02.mp3


*Jingles de anúncio de pedidos dos membros*

📄 pedidos-01.mp3
📄 pedidos-02.mp3


Já a parte dos horarios fixos não suporta multiplos arquivos e sua nomeação dos arquivos deve ocorrer no formato 24H sendo apenas entre (0 e 23) para indicar cada horário, segue um exemplo.

📄 0H.mp3 (meia noite)
📄 1H.mp3 (uma hora da manhã)
📄 16H.mp3 (quatro horas da tarde)
📄 23H.mp3 (onze horas da noite)

Sempre renomeie o H como Maiusculo.


**Estrutura das pastas no seu repositorio particular de músicas**

📁 anuncios
    📄 9H.mp3
    📄 jingle.mp3
    📄 pedidos.mp3
📁 musicas
    📄 suamusica.mp3


**Estrutura das pastas final na host**
📁 cogs
📁 img
📁 musicas_repo (Criada automaticamente)
    📁 anuncios
        📄 9H.mp3
        📄 jingle.mp3
        📄 pedidos.mp3
    📁 musicas
        📄 suamusica.mp3
📄 .env
📄 main.py
📄 requirements.txt
🤖 discloud.config
🤖 squarecloud.app


**Lista dos comandos**

- /dj ping
- /dj status
- /dj restart (Apenas dono)
- /radio tocadas
- /radio verificar (Apenas dono)
- /radio mover (Apenas dono)
- /radio pedido
- Menção do bot


**Variaveis exigidas**

- SUA ID em DONO_ID
- Token do seu bot em DISCORD_TOKEN_RADIO
- Token da square em square_token
- Token da discloud em discloud_token
- Token do github para acesso a repositorio particular
- Link do seu repositorio de musicas e anúncios, lembre-se que precisa obrigatoriamente ambas as pastas, mesmo que não tenha anúncios
- ID do canal onde o bot irá se conectar