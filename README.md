# Dj-Braixen - Uma Dj personalizada

![bot image](img/dj_braixen_avatar.png)


Codigo em Python de um bot de musica que funciona como uma verdadeira radio com uma Dj carismatica que até faz participação vocal.

Esse codigo é somente referencia para um reproduzir de musica a partir de duas pastas, uma chamada **musica** e outra chamada **anuncios**, o codigo foi desenvolvido para ser usado diretamente em alguma comunidade, neste caso é simples, o codigo ta programado para sincronizar um repositorio, e a partir disso começa a tocar as musicas, onde que a cada hora verifica se existe algum anuncio para aquele deteminado horario e o toca, bem simples e automatizado.

Para funcionamento do bot é necessario criar um repositorio privado (private) e será nele que você guardará todas as musicas e arquivos de anuncios que serão usados pelo bot, já dentro do repositorio Crie duas pasts uma chamada **musica** e outra chamada **anuncios** e serão dentro delas que você deve armazenar seus arquivos sempre no formato **.mp3** (outros formatos não são compativeis)


**Lista dos comandos**

- /dj ping
- /dj status
- Menção do bot


**Variaveis exigidas**

- SUA ID em DONO_ID
- Token do seu bot em DISCORD_TOKEN_RADIO
- Token da square em square_token
- Token do github para acesso a repositorio particular
- Link do seu repositorio de musicas e anúncios, lembre-se que precisa obrigatoriamente ambas as pastas, mesmo que não tenha anúncios
- ID do canal onde o bot irá se conectar
