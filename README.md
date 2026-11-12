# Ponto Away

Bot do Telegram que registra o ponto no [Portal do Servidor](https://portaldoservidor.sistemas.ro.gov.br/) quando você manda `/bater`. Roda no Docker e sobe sozinho quando o computador liga.

O fluxo é o do próprio portal: login no SAURON, menu **Registrar ponto**, botão **Registrar** e confirmação **Sim, Tenho Certeza**. O bot devolve uma foto da tela.

## Configurar

1. No Telegram, fala com o [@BotFather](https://t.me/BotFather), cria um bot e copia o token.
2. Copia o exemplo e preenche:

```bash
cp .env.example .env
```

`PONTO_CPF` e `PONTO_SENHA` são o login do SAURON. `PONTO_MATRICULA` só precisa se você tiver mais de uma matrícula.

3. Sobe o container:

```bash
docker compose up -d --build
```

4. Manda `/start` no chat do bot. Se `TELEGRAM_ALLOWED_IDS` ainda estiver vazio, ele responde o seu id. Coloca esse número no `.env` e recria:

```bash
docker compose up -d --force-recreate
```

Sem esse id, o bot não registra ponto.

## Comandos

- `/bater` registra o ponto
- `/bater 12345` usa essa matrícula
- `/hoje` abre a tela e mostra os horários, sem registrar
- `/id` mostra o seu id do Telegram

## Ligar junto com o computador

Nesta máquina a WSL é a `Ubuntu-24.04` e o Docker já sobe com o systemd. O script abaixo faz três coisas:

- habilita o serviço `ponto-away`, que sobe o container quando a WSL inicia
- cria a tarefa `PontoAway` no Windows, no logon, para acordar a WSL
- grava `vmIdleTimeout=-1` em `C:\Users\Julio\.wslconfig`, para o Windows não desligar a WSL por inatividade

```bash
sudo ./scripts/install-autostart.sh
```

O `vmIdleTimeout` só passa a valer no próximo reinício da WSL. Não reinicie agora se tiver outro container no meio do trabalho.

Um comando enviado com o computador desligado não é executado depois. Isso evita registrar o ponto na hora errada, quando a máquina voltar.

Logs:

```bash
docker logs -f ponto-away
```
