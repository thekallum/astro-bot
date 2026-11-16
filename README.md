<div align="center">
<img src="https://i.imgur.com/oCX22MG.jpeg" width="150">

# 🪐 Astro Bot

![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow?logo=github&style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white&style=for-the-badge)
![Discord](https://img.shields.io/badge/discord.py-2.3.2-5865F2?logo=discord&logoColor=white&style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white&style=for-the-badge)
![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC_BY--NC--SA_4.0-lightgrey.svg?logo=creativecommons&style=for-the-badge)

**Verificação por e-mail para servidores do Discord.**
<br>
Um bot de verificação que confirma os novos membros por um código enviado ao e-mail, digitado em um teclado numérico na DM, com proteção contra raids, modo de bloqueio e logs completos para a staff.

[Site do Astro](https://astrobot.discloud.app) • [Reportar Bug](https://github.com/thekallum/astro-bot/issues) • [Solicitar Feature](https://github.com/thekallum/astro-bot/issues)

</div>

---

## 📑 Índice

* [📸 Sobre o Projeto](#-sobre-o-projeto)
  * [Principais Funcionalidades](#principais-funcionalidades)
* [🛠️ Tecnologias Utilizadas](#tecnologias)
* [💻 Pré-requisitos](#-pré-requisitos)
* [🚀 Como Rodar o Projeto Localmente](#-como-rodar-o-projeto-localmente)
* [🤖 Comandos Slash](#-comandos-slash)
* [🚀 Deploy em Produção](#-deploy-em-produção)
* [❓ FAQ & Solução de Problemas](#-perguntas-frequentes-faq--solução-de-problemas)
* [📂 Estrutura do Projeto](#-estrutura-do-projeto)
* [🤝 Como Contribuir](#-como-contribuir)
* [⚖️ Licença](#licenca)

---

## 📸 Sobre o Projeto

O **Astro** é um bot de verificação para servidores do Discord, feito em **Python** com **discord.py**. Quando um membro entra no servidor, ele recebe um cargo de "não verificado". Para liberar o acesso, o membro usa o comando `/verificar` informando o seu e-mail, recebe um **código de 6 dígitos** e o digita em um **teclado numérico** de botões na DM do bot.

Ao acertar o código, o bot troca o cargo de não verificado pelo de verificado e registra tudo no canal de logs da staff. O bot também ajuda a proteger o servidor, com bloqueio de e-mails descartáveis, alerta de raid e modo de segurança (*lockdown*).

Os dados de cada servidor ficam em um banco **SQLite** local (`bot.db`), então o mesmo bot pode atender vários servidores, cada um com as suas configurações.

### Principais Funcionalidades
* **📧 Verificação por E-mail:** O código de 6 dígitos é enviado por e-mail, com um template em HTML personalizável.
* **🔢 Teclado Numérico:** O membro digita o código em botões na DM do bot, sem sair do Discord.
* **🛡️ Modo de Segurança (Lockdown):** Os administradores podem desativar novas verificações em caso de ataque.
* **🚨 Alerta de Raid:** Se muitos membros entrarem em pouco tempo, a staff é avisada no canal de logs.
* **🚫 Domínios Bloqueados:** O dono do bot mantém uma lista de provedores de e-mail que não são aceitos.
* **🕒 Idade Mínima de Conta:** Contas do Discord com menos de 1 dia não podem se verificar.
* **⏳ Limites e Cooldown:** O código expira em 10 minutos, há 3 tentativas por código e 5 minutos de espera entre pedidos.
* **📁 Logs Completos:** Início, sucesso e falha de verificações, ações manuais, bloqueios, raids e erros vão para o canal de logs.
* **🧰 Ferramentas para a Staff:** Verificar e desverificar manualmente, consultar o status de um membro e ver informações detalhadas.
* **💾 Persistência:** As configurações e as verificações pendentes ficam salvas em SQLite, e o teclado continua funcionando após reiniciar o bot.

#### Como funciona a verificação

1. O membro usa `/verificar` e informa o seu e-mail.
2. O bot envia um código de 6 dígitos para o e-mail e abre o teclado numérico na DM.
3. O membro digita o código e clica em **OK**.
4. Se o código estiver correto, o cargo de verificado é concedido e o de não verificado é removido.

#### Regras de segurança

| Regra | Valor |
| :--- | :--- |
| Tamanho do código | 6 dígitos |
| Validade do código | 10 minutos |
| Tentativas por código | 3 |
| Espera entre pedidos de código | 5 minutos |
| Idade mínima da conta do Discord | 1 dia |
| Alerta de raid | 15 entradas em 60 segundos |

---

## <a id="tecnologias"></a>🛠️ Tecnologias Utilizadas

Este projeto foi desenvolvido utilizando as seguintes tecnologias:

* **Linguagem:** Python 3
* **Discord:** [discord.py](https://github.com/Rapptz/discord.py) 2.3.2 (slash commands, botões e views persistentes)
* **E-mail:** [aiosmtplib](https://github.com/cole/aiosmtplib) com SMTP do Gmail
* **Configuração:** [python-dotenv](https://github.com/theskumar/python-dotenv)
* **Banco de Dados:** SQLite (módulo `sqlite3` do Python)
* **Hospedagem:** [Discloud](https://discloud.com)

---

## 💻 Pré-requisitos

Antes de começar, certifique-se de ter:
* [Git](https://git-scm.com)
* [Python 3.8](https://www.python.org/downloads/) ou superior (prefira as versões 3.10 a 3.12, pois o `discord.py` 2.3.2 pode não funcionar em Python 3.13)
* Uma aplicação de bot criada no [Discord Developer Portal](https://discord.com/developers/applications), com a **Server Members Intent** e a **Message Content Intent** ativadas
* Uma conta de e-mail do Gmail para enviar os códigos (use uma [senha de app](https://support.google.com/accounts/answer/185833))
* Um servidor Discord com dois cargos (verificado e não verificado) e um canal de logs

---

## 🚀 Como Rodar o Projeto Localmente

#### 1. Clone o repositório
```bash
git clone https://github.com/thekallum/astro-bot.git
cd astro-bot
```

#### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

#### 3. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Token do bot do Discord (OBRIGATÓRIO)
DISCORD_TOKEN=seu_token_aqui

# Conta do Gmail que envia os códigos de verificação (OBRIGATÓRIO)
EMAIL_ADDRESS=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
```

> [!CAUTION]
> O arquivo **`.env`** contém o token do seu bot e a senha do seu e-mail.
>
> **NUNCA** faça *commit* ou exponha este arquivo publicamente. Crie um `.gitignore` com a linha `.env` e **sempre verifique** antes de enviar suas alterações para o repositório. Se o token vazar, gere um novo no Developer Portal imediatamente.

#### 4. Ajuste as constantes do `main.py`

| Constante | Descrição |
| :--- | :--- |
| **`BOT_OWNER_ID`** | Seu ID de usuário do Discord. Só você pode usar os comandos de domínios bloqueados. |
| **`RAID_THRESHOLD_COUNT`** | Quantidade de entradas que dispara o alerta de raid (padrão: `15`) |
| **`RAID_THRESHOLD_SECONDS`** | Janela de tempo, em segundos, para contar as entradas (padrão: `60`) |

> [!TIP]
> Para copiar o seu ID, ative o **Modo Desenvolvedor** nas configurações do Discord, clique com o botão direito no seu perfil e escolha **Copiar ID**.

#### 5. Convide o bot para o servidor

No Developer Portal, em **OAuth2 → URL Generator**, marque os escopos `bot` e `applications.commands` e dê ao bot as permissões de **Gerenciar Cargos**, **Ver Canais**, **Enviar Mensagens** e **Incorporar Links**.

> [!IMPORTANT]
> O cargo do Astro precisa estar **acima** dos cargos de verificado e de não verificado na hierarquia de cargos do servidor. Sem isso, o bot não consegue trocar os cargos dos membros.

#### 6. Execute o bot

```bash
python main.py
```

#### 7. Configure o servidor

No Discord, use `/configurar` e escolha o **cargo de verificado**, o **cargo de não verificado** e o **canal de logs**. O bot envia uma mensagem de teste no canal de logs para confirmar que tudo está certo.

Depois, qualquer membro já pode usar `/verificar`.

---

## 🤖 Comandos Slash

| Comando | O que faz | Quem pode usar |
| :--- | :--- | :--- |
| `/verificar <email>` | Inicia a verificação por e-mail | Todos os membros |
| `/configurar` | Define os cargos de verificado e não verificado e o canal de logs | Administradores |
| `/guia_staff` | Mostra o guia de configuração e uso do bot | Administradores |
| `/seguranca bloqueio <ativar>` | Ativa ou desativa o modo de segurança (*lockdown*) | Administradores |
| `/verificar_manual <membro>` | Verifica um membro manualmente | Quem tem **Gerenciar Cargos** |
| `/desverificar <membro> <motivo>` | Remove a verificação de um membro | Quem tem **Gerenciar Cargos** |
| `/info_membro <membro>` | Mostra informações detalhadas de um membro | Quem tem **Gerenciar Cargos** |
| `/status_verificacao <membro>` | Mostra se a verificação está concluída, pendente ou não iniciada | Quem tem **Gerenciar Cargos** |
| `/bloquear_dominio <dominio>` | Bloqueia um domínio de e-mail | Dono do bot |
| `/desbloquear_dominio <dominio>` | Remove um domínio da lista de bloqueio | Dono do bot |
| `/listar_dominios_bloqueados` | Lista os domínios bloqueados | Dono do bot |

---

## 🚀 Deploy em Produção

### Discloud

O Astro está pré-configurado para ser implantado na **Discloud**. O arquivo `discloud.config` já está na raiz do projeto:

```ini
TYPE=bot
MAIN=main.py
NAME=Astro
RAM=300
AUTORESTART=true
ID=1761830361600
```

| Parâmetro | Descrição |
| :--- | :--- |
| **`TYPE`** | `bot`, pois a aplicação é um bot de Discord |
| **`MAIN`** | Arquivo principal que a Discloud executa (`main.py`) |
| **`NAME`** | Nome do app no painel |
| **`RAM`** | Memória reservada, em MB (300 no projeto) |
| **`AUTORESTART`** | Reinicia o bot automaticamente se ele cair |
| **`ID`** | Identificador do app na Discloud. Troque pelo seu se for hospedar uma cópia |

#### 🔑 Configurando as Variáveis de Ambiente

No painel da Discloud, adicione as seguintes variáveis de ambiente:

| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| **`DISCORD_TOKEN`** | Token do bot do Discord | `seu_token_aqui` |
| **`EMAIL_ADDRESS`** | Gmail que envia os códigos | `seu_email@gmail.com` |
| **`EMAIL_PASSWORD`** | Senha de app do Gmail | `sua_senha_de_app` |

#### 📦 Realizando o Deploy

1. Acesse o painel da [Discloud](https://discloud.com/)
2. Faça upload do projeto compactado (ZIP), sem o arquivo `.env`
3. Aguarde o build e o início automático do bot

> [!NOTE]
> O banco de dados `bot.db` é criado na pasta do projeto. Antes de atualizar o app, faça um backup dele para não perder as configurações dos servidores.

---

## ❓ Perguntas Frequentes (FAQ) & Solução de Problemas

### 🔌 Erro: "Sistema não configurado. Use /configurar"

Os cargos de verificado e de não verificado ainda não foram definidos no servidor. Um administrador precisa usar o comando `/configurar`.

### 🚨 "O cargo do Astro precisa estar acima do cargo de verificado"

Abra **Configurações do Servidor → Cargos** e arraste o cargo do Astro para cima dos cargos de verificado e de não verificado. Depois, use `/configurar` novamente.

### ✉️ O e-mail com o código não chega

* Confira se `EMAIL_ADDRESS` e `EMAIL_PASSWORD` estão definidos e se a senha é uma **senha de app** do Gmail.
* Verifique a caixa de spam do membro.
* Se o bot responder que o e-mail foi recusado, o endereço informado está incorreto.

### 💬 "Não consegui te enviar uma DM!"

O membro precisa permitir mensagens diretas de membros do servidor, porque o teclado numérico é enviado na DM. Depois de ajustar a privacidade, é só usar `/verificar` de novo.

### ⏳ "Você está em tempo de espera!"

Existe um intervalo de 5 minutos entre os pedidos de código. O bot informa quanto tempo falta.

### ❌ "Seu código de verificação expirou" ou "Limite de tentativas excedido"

O código vale por 10 minutos e permite 3 tentativas. Nesses casos, use `/verificar` novamente para receber um novo código.

### 🆕 "Sua conta do Discord é muito recente"

Para evitar contas criadas só para ataques, o Astro exige que a conta tenha pelo menos 1 dia.

### 🛡️ "O servidor está em modo de segurança (lockdown)"

Um administrador ativou o bloqueio de novas verificações. Para desativar, use `/seguranca bloqueio ativar:False`.

### 📁 Os logs não aparecem no canal

* Confira se o bot consegue ver o canal e tem permissão para enviar mensagens e incorporar links nele.
* Use `/configurar` novamente para definir o canal e receber a mensagem de teste.
* Veja o terminal do bot: as mensagens `[DEBUG]` indicam o motivo da falha.

### 🔒 Erro de "Privileged Intents" ao iniciar

O bot usa as intents `Server Members` e `Message Content`. Ative as duas no Developer Portal, em **Bot → Privileged Gateway Intents**, e reinicie.

### 🔄 Os comandos slash não aparecem

Os comandos são sincronizados globalmente quando o bot inicia, e pode levar alguns minutos para que apareçam no Discord. Confirme também que o bot foi convidado com o escopo `applications.commands`.

### 🐛 Como Reportar um Bug

1. Verifique se já não foi reportado nas [Issues](https://github.com/thekallum/astro-bot/issues)
2. Abra uma nova Issue com:
   * Descrição detalhada do problema
   * Mensagens de erro do terminal onde o bot está rodando
   * Versão do Python e do `discord.py`
   * Sistema operacional

---

## 📂 Estrutura do Projeto

```
astro-bot/
├── main.py              # Código principal: comandos, eventos e interface de verificação
├── database.py          # Funções do banco SQLite
├── requirements.txt     # Dependências do projeto
├── discloud.config      # Configuração para deploy na Discloud
├── bot.db               # Banco de dados SQLite (gerado automaticamente)
├── .env                 # Variáveis de ambiente (NÃO COMITAR!)
├── LICENSE              # Texto completo da licença
├── README.md            # Este arquivo
└── templates/
    └── email_template.html   # Template HTML do e-mail com o código
```

### 📄 Sobre os Arquivos Principais

* **`main.py`**: Arquivo principal do bot que:
  * Registra os slash commands e os eventos de entrada de membros
  * Monta o teclado numérico da DM e valida o código digitado
  * Envia o e-mail com o código pelo SMTP do Gmail
  * Detecta raids, controla o modo de segurança e envia os logs para a staff
* **`database.py`**: Cria o banco `bot.db` e reúne as funções de leitura e escrita, com as tabelas:

| Tabela | Conteúdo |
| :--- | :--- |
| `guild_settings` | Cargos, canal de logs e estado do lockdown de cada servidor |
| `verifications` | Verificações em andamento (código, tentativas e o que já foi digitado) |
| `verified_users` | Membros verificados e a data da verificação |
| `blocked_domains` | Domínios de e-mail bloqueados |

* **`templates/email_template.html`**: Modelo do e-mail enviado ao membro. Usa os marcadores `{{NOME_USUARIO}}`, `{{NOME_SERVIDOR}}` e `{{CODIGO}}`. Se o arquivo não existir, o bot envia um e-mail simples no lugar.

---

## 🤝 Como Contribuir

Contribuições são sempre bem-vindas! Se você tem uma ideia de melhoria:

1. Faça um Fork do projeto
2. Crie uma Branch para sua feature (`git checkout -b feature/NovaFeature`)
3. Faça o Commit das suas mudanças (`git commit -m 'Adiciona NovaFeature'`)
4. Faça o Push para a branch (`git push origin feature/NovaFeature`)
5. Abra um Pull Request

---

## <a id="licenca"></a>⚖️ Licença

Este projeto está licenciado sob a licença **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)**.
### O que isso significa?
* ✅ **Você pode:** Baixar o código, estudar como funciona, modificar e rodar na sua máquina para aprendizado.
* ❌ **Você NÃO pode:** Usar este projeto para fins comerciais (vender, cobrar acesso, usar em empresas) ou criar um produto concorrente direto.
* 🛡️ **Garantia:** O material é fornecido "como está", sem garantias de qualquer tipo.
* 🏷️ **Obrigatório:** Ao utilizar ou adaptar qualquer parte deste código, você deve:

  1. Dar os créditos ao autor original ([**Kallum**](https://github.com/thekallum)).

  2. Licenciar o seu trabalho derivado sob os mesmos termos (CC BY-NC-SA 4.0).

> [!NOTE]
> Este resumo não substitui a licença. Para ler o texto legal completo, consulte o arquivo [LICENSE](./LICENSE) neste repositório ou a [licença oficial](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode).

---

<div align="center">

Feito com 🧡 por [**Kallum**](https://github.com/thekallum)

⭐ Se este projeto te ajudou, considere dar uma estrela!

</div>
