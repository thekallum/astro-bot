import discord
from discord.ext import commands
from discord import app_commands
import os
import random
import string
from email.message import EmailMessage
from dotenv import load_dotenv
import time
import asyncio
import aiosmtplib
from datetime import datetime, timedelta, timezone
import traceback
from collections import deque

import database as db

load_dotenv()
db.init_db()

# --- CONSTANTES ---
BOT_OWNER_ID = 475255757370032138 # Substitua pelo seu ID de usuário
RAID_THRESHOLD_COUNT = 15
RAID_THRESHOLD_SECONDS = 60
recent_joins = {}

# --- BOT ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True 

class PersistentBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerificationKeypad())
        print("View persistente registrada.")

bot = PersistentBot()

# --- FUNÇÕES AUXILIARES ---
def format_seconds(total_seconds: float) -> str:
    if total_seconds < 1: return "menos de um segundo"
    total_seconds = round(total_seconds)
    minutes, seconds = divmod(total_seconds, 60)
    parts = []
    if minutes > 0: parts.append(f"{minutes} minuto{'s' if minutes != 1 else ''}")
    if seconds > 0: parts.append(f"{seconds} segundo{'s' if seconds != 1 else ''}")
    return " e ".join(parts)

async def log_action(guild: discord.Guild, embed: discord.Embed):
    print(f"[DEBUG] Função log_action iniciada para o servidor: {guild.name} ({guild.id})")
    
    try:
        settings = db.get_settings(guild.id)
        if not settings:
            print(f"[DEBUG] FALHA: Não há configurações (settings) no banco de dados para o servidor {guild.id}.")
            return
            
        # CORREÇÃO AQUI: Desempacota 4 valores (verified_role_id, unverified_role_id, log_channel_id, lockdown_enabled)
        _, _, log_channel_id, _ = settings 
        
        if not log_channel_id:
            print(f"[DEBUG] FALHA: O log_channel_id é NULO ou NÃO FOI ENCONTRADO no banco de dados.")
            return

        print(f"[DEBUG] ID do canal de logs encontrado no DB: {log_channel_id}")
        
        log_channel = bot.get_channel(log_channel_id)
        
        if not log_channel:
            print(f"[DEBUG] FALHA: O bot.get_channel({log_channel_id}) retornou None.")
            print(f"[DEBUG] Verifique se o bot tem a permissão 'Ver Canal' ou se o canal foi excluído.")
            return
            
        print(f"[DEBUG] Canal '{log_channel.name}' encontrado. Tentando enviar a mensagem...")
        
        embed.timestamp = datetime.now()
        await log_channel.send(embed=embed)
        print(f"[DEBUG] SUCESSO: Log enviado para #{log_channel.name}.")

    except discord.Forbidden:
        print(f"[DEBUG] ERRO FATAL (Forbidden): O bot não tem permissão para 'Enviar Mensagens' ou 'Incorporar Links' no canal #{log_channel.name}.")
    except Exception as e:
        print(f"[DEBUG] ERRO INESPERADO: Ocorreu um erro ao tentar enviar a mensagem: {e}")
        traceback.print_exc()

async def send_email_async(recipient, code, user_name, guild_name):
    EMAIL, PASSWORD = os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD")
    if not EMAIL or not PASSWORD: return False
    try:
        with open("templates/email_template.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        html_content = html_content.replace("{{NOME_USUARIO}}", user_name).replace("{{NOME_SERVIDOR}}", guild_name).replace("{{CODIGO}}", code)
    except FileNotFoundError:
        print("ERRO: O arquivo 'templates/email_template.html' não foi encontrado.")
        html_content = f"""<p>Olá <strong>{user_name}</strong>,</p><p>Seu código de verificação para o servidor <strong>"{guild_name}"</strong> é:</p><div style="font-size: 28px; font-weight: bold;">{code}</div>"""
    msg = EmailMessage()
    msg["Subject"] = f"Seu Código de Verificação para {guild_name}"
    msg["From"] = EMAIL
    msg["To"] = recipient
    msg.set_content(f"Seu código para '{guild_name}' é: {code}")
    msg.add_alternative(html_content, subtype='html')
    try:
        await aiosmtplib.send(msg, hostname="smtp.gmail.com", port=465, use_tls=True, username=EMAIL, password=PASSWORD)
        return True
    except aiosmtplib.SMTPRecipientsRefused: return "recipient_refused"
    except Exception as e:
        print(f"Falha ao enviar e-mail: {e}")
        return False

async def send_help_message(user: discord.User, guild_name: str):
    embed = discord.Embed(title="🤔 Como usar o sistema de verificação?", description=f"Bem-vindo(a) ao processo de verificação do servidor **{guild_name}**!", color=discord.Color.blue())
    embed.add_field(name="Passo 1", value="Use `/verificar` e forneça seu e-mail.", inline=False)
    embed.add_field(name="Passo 2", value="Receba o código de 6 dígitos no seu e-mail.", inline=False)
    embed.add_field(name="Passo 3", value="Digite o código no teclado na sua DM e clique em `OK`.", inline=False)
    try:
        await user.send(embed=embed)
    except discord.Forbidden:
        print(f"Não foi possível enviar a DM de ajuda para {user.name}")

# --- INTERFACE DE VERIFICAÇÃO ---
class VerificationKeypad(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Site do Astro", style=discord.ButtonStyle.link, url="https://astrobot.discloud.app", row=0))

    def create_embed(self, current_input=" ", status="default"):
        colors = {"default": discord.Color.blue(), "ready": discord.Color.green(), "error": discord.Color.orange()}
        display_code = current_input if current_input and current_input.strip() else " "
        embed = discord.Embed(title="Insira o código recebido", description="Use o teclado numérico e clique em OK.", color=colors.get(status, discord.Color.blue()))
        embed.add_field(name="Código:", value=f"```{display_code}```", inline=False)
        return embed

    async def handle_key_press(self, interaction: discord.Interaction, key: str):
        verification_data = db.get_verification(interaction.user.id)
        if not verification_data: return await interaction.response.edit_message(content="❌ Verificação expirada.", embed=None, view=None)
        *_, current_input = verification_data
        
        if key == "backspace": new_input = current_input[:-1] if current_input else ""
        elif len(current_input) < 6: new_input = current_input + key
        else: return await interaction.response.defer()
        
        db.update_input_code(interaction.user.id, new_input)
        status = "ready" if len(new_input) == 6 else "default"
        await interaction.response.edit_message(embed=self.create_embed(new_input, status), view=self)

    async def handle_submission(self, interaction: discord.Interaction):
        verification_data = db.get_verification(interaction.user.id)
        if not verification_data: return await interaction.response.edit_message(content="❌ Verificação expirada.", embed=None, view=None)
        
        guild_id, correct_code, attempts, created_at_timestamp, current_input = verification_data
        
        if time.time() - created_at_timestamp > 600:
            for item in self.children: item.disabled = True
            await interaction.response.edit_message(content="❌ **Seu código de verificação expirou.**", embed=None, view=self)
            db.delete_verification(interaction.user.id)
            return self.stop()
            
        if not current_input:
            for item in self.children: item.disabled = False
            return await interaction.response.edit_message(content="**Atenção:** Você precisa digitar o código antes de clicar em OK.", view=self)
        
        guild = bot.get_guild(guild_id)
        if current_input == correct_code:
            for item in self.children: item.disabled = True
            await interaction.response.edit_message(content="✅ **Verificação concluída!**", embed=None, view=self)
            
            verified_role_id, unverified_role_id, _, _ = db.get_settings(guild_id)

            if guild and (member := guild.get_member(interaction.user.id)):
                if verified_role := (guild.get_role(verified_role_id) if verified_role_id else None): await member.add_roles(verified_role)
                if unverified_role := (guild.get_role(unverified_role_id) if unverified_role_id else None): await member.remove_roles(unverified_role)
                db.add_verified_user(member.id, guild.id)
                await member.send(f"🎉 **Bem-vindo(a) ao {guild.name}!**")
                log_embed = discord.Embed(title="✅ Verificação Bem-Sucedida", color=discord.Color.green(), description=f"{member.mention} foi verificado.")
                await log_action(guild, embed=log_embed)
            db.delete_verification(interaction.user.id)
            self.stop()
        else:
            db.update_attempts(interaction.user.id)
            attempts += 1
            if attempts >= 3:
                for item in self.children: item.disabled = True
                await interaction.response.edit_message(content="❌ **Limite de tentativas excedido.**", embed=None, view=self)
                if guild:
                    log_embed = discord.Embed(title="⚠️ Falha na Verificação", color=discord.Color.orange(), description=f"{interaction.user.mention} excedeu as tentativas.")
                    await log_action(guild, embed=log_embed)
                db.delete_verification(interaction.user.id)
                self.stop()
            else:
                db.update_input_code(interaction.user.id, "")
                await interaction.response.edit_message(content=f"❌ **Código incorreto.** Restam {3 - attempts} tentativa(s).", embed=self.create_embed("", "error"), view=self)
    
    @discord.ui.button(label="1", style=discord.ButtonStyle.secondary, custom_id="key_1", row=0)
    async def b1(self, i, b): await self.handle_key_press(i, "1")
    @discord.ui.button(label="2", style=discord.ButtonStyle.secondary, custom_id="key_2", row=0)
    async def b2(self, i, b): await self.handle_key_press(i, "2")
    @discord.ui.button(label="3", style=discord.ButtonStyle.secondary, custom_id="key_3", row=0)
    async def b3(self, i, b): await self.handle_key_press(i, "3")
    @discord.ui.button(label="4", style=discord.ButtonStyle.secondary, custom_id="key_4", row=1)
    async def b4(self, i, b): await self.handle_key_press(i, "4")
    @discord.ui.button(label="5", style=discord.ButtonStyle.secondary, custom_id="key_5", row=1)
    async def b5(self, i, b): await self.handle_key_press(i, "5")
    @discord.ui.button(label="6", style=discord.ButtonStyle.secondary, custom_id="key_6", row=1)
    async def b6(self, i, b): await self.handle_key_press(i, "6")
    @discord.ui.button(label="7", style=discord.ButtonStyle.secondary, custom_id="key_7", row=2)
    async def b7(self, i, b): await self.handle_key_press(i, "7")
    @discord.ui.button(label="8", style=discord.ButtonStyle.secondary, custom_id="key_8", row=2)
    async def b8(self, i, b): await self.handle_key_press(i, "8")
    @discord.ui.button(label="9", style=discord.ButtonStyle.secondary, custom_id="key_9", row=2)
    async def b9(self, i, b): await self.handle_key_press(i, "9")
    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.primary, custom_id="key_back", row=3)
    async def back(self, i, b): await self.handle_key_press(i, "backspace")
    @discord.ui.button(label="0", style=discord.ButtonStyle.secondary, custom_id="key_0", row=3)
    async def b0(self, i, b): await self.handle_key_press(i, "0")
    @discord.ui.button(label="OK", style=discord.ButtonStyle.success, custom_id="key_ok", row=3)
    async def ok(self, i, b): await self.handle_submission(i)
    @discord.ui.button(label="Descobrir como usar", style=discord.ButtonStyle.secondary, custom_id="help_button", row=4)
    async def help_button_callback(self, i, b):
        await i.response.defer(ephemeral=True)
        verification_data = db.get_verification(i.user.id)
        guild_name = "seu servidor"
        if verification_data and (guild := bot.get_guild(verification_data[0])): guild_name = guild.name
        await send_help_message(i.user, guild_name)
        await i.followup.send("Enviei as instruções para você!", ephemeral=True)
    @discord.ui.button(label="Reenviar Código", style=discord.ButtonStyle.danger, custom_id="resend_button", row=4)
    async def resend_button_callback(self, i, b):
        await i.response.send_message("❌ Para reenviar, use `/verificar` novamente.", ephemeral=True, delete_after=10)

# --- COMANDOS SLASH ---
@bot.tree.command(name="verificar", description="Inicia o processo de verificação por e-mail.")
@app_commands.describe(email="Seu endereço de e-mail para receber o código.")
async def verificar(interaction: discord.Interaction, email: str):
    await interaction.response.defer(ephemeral=True)
    
    verified_role_id, unverified_role_id, _, lockdown_enabled = db.get_settings(interaction.guild.id)

    if verified_role_id and (verified_role := interaction.guild.get_role(verified_role_id)):
        if verified_role in interaction.user.roles:
            return await interaction.followup.send("✅ Você já está verificado neste servidor!", ephemeral=True)
    
    if lockdown_enabled:
        return await interaction.followup.send("❌ **O servidor está em modo de segurança (lockdown).** Novas verificações estão desativadas.", ephemeral=True)

    if datetime.now(timezone.utc) - interaction.user.created_at < timedelta(days=1):
        return await interaction.followup.send("❌ **Sua conta do Discord é muito recente.** Espere sua conta ter pelo menos 1 dia para se verificar.", ephemeral=True)
    
    try:
        dominio = email.split('@')[1].lower()
        if db.is_domain_blocked(dominio):
            return await interaction.followup.send("❌ **Este provedor de e-mail não é permitido.**", ephemeral=True)
    except IndexError:
        return await interaction.followup.send("❌ **Formato de e-mail inválido.**", ephemeral=True)

    if verification_data := db.get_verification(interaction.user.id):
        *_, created_at_timestamp, _ = verification_data
        cooldown_time = 300
        time_passed = time.time() - created_at_timestamp
        if time_passed < cooldown_time:
            remaining = cooldown_time - time_passed
            return await interaction.followup.send(f"Você está em tempo de espera! Tente novamente em **{format_seconds(remaining)}**.", ephemeral=True)
    
    if not verified_role_id or not unverified_role_id:
        return await interaction.followup.send("❌ Sistema não configurado. Use `/configurar`.", ephemeral=True)
        
    codigo = "".join(random.choices(string.digits, k=6))
    db.create_verification(interaction.user.id, interaction.guild.id, codigo)
    email_status = await send_email_async(email, codigo, interaction.user.display_name, interaction.guild.name)
    
    if email_status is True:
        view = VerificationKeypad()
        try:
            await interaction.user.send(embed=view.create_embed(), view=view)
            await interaction.followup.send("✉️ **Verifique suas Mensagens Diretas (DM)!**", ephemeral=True)
            log_embed = discord.Embed(title="➡️ Início de Verificação", color=discord.Color.blue())
            log_embed.add_field(name="Usuário", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
            log_embed.add_field(name="E-mail", value=f"`{email}`", inline=False)
            await log_action(interaction.guild, embed=log_embed)
        except discord.Forbidden:
            db.delete_verification(interaction.user.id)
            await interaction.followup.send("❌ **Não consegui te enviar uma DM!**", ephemeral=True)
    else:
        db.delete_verification(interaction.user.id)
        if email_status == "recipient_refused":
            await interaction.followup.send("❌ **O e-mail foi recusado.** Verifique se o endereço está correto.", ephemeral=True)
        else:
            await interaction.followup.send("❌ **Ocorreu um erro ao enviar o e-mail.**", ephemeral=True)

# --- COMANDOS DE ADMINISTRAÇÃO ---
@bot.tree.command(name="configurar", description="Configura os cargos de verificação e o canal de logs.")
@app_commands.default_permissions(administrator=True)
async def configurar(interaction: discord.Interaction, 
                     cargo_verificado: discord.Role, 
                     cargo_nao_verificado: discord.Role, 
                     canal_logs: discord.TextChannel): # Certifique-se que é TextChannel

    print(f"[DEBUG - COMANDO CONFIGURAR] Interação recebida de {interaction.user.name} no servidor {interaction.guild.name}.")
    print(f"[DEBUG - COMANDO CONFIGURAR] Cargo Verificado recebido: {cargo_verificado.name} ({cargo_verificado.id})")
    print(f"[DEBUG - COMANDO CONFIGURAR] Cargo Não Verificado recebido: {cargo_nao_verificado.name} ({cargo_nao_verificado.id})")
    print(f"[DEBUG - COMANDO CONFIGURAR] Canal de Logs recebido: {canal_logs.name} ({canal_logs.id})")

    # Verifica se os cargos são válidos
    if cargo_verificado.id == cargo_nao_verificado.id:
        await interaction.response.send_message("Os cargos de verificado e não verificado não podem ser os mesmos.", ephemeral=True)
        return

    # Verifica se o cargo do bot está acima dos cargos de verificação
    bot_member = interaction.guild.get_member(bot.user.id)
    if bot_member and bot_member.top_role < cargo_verificado:
        await interaction.response.send_message(
            f"🚨 O cargo do Astro (`{bot_member.top_role.name}`) precisa estar acima do cargo de verificado (`{cargo_verificado.name}`) na hierarquia de cargos para poder gerenciar as permissões. Por favor, ajuste a ordem dos cargos nas configurações do servidor.", 
            ephemeral=True
        )
        return
    if bot_member and bot_member.top_role < cargo_nao_verificado:
        await interaction.response.send_message(
            f"🚨 O cargo do Astro (`{bot_member.top_role.name}`) precisa estar acima do cargo de não verificado (`{cargo_nao_verificado.name}`) na hierarquia de cargos para poder gerenciar as permissões. Por favor, ajuste a ordem dos cargos nas configurações do servidor.", 
            ephemeral=True
        )
        return

    # Salva as configurações
    db.set_settings(
        interaction.guild.id, 
        cargo_verificado.id, 
        cargo_nao_verificado.id, 
        canal_logs.id,
        "default_email_domain" # Este argumento `allowed_domains` é um resquício. Não impacta mais o DB.
    )

    print(f"[DEBUG - COMANDO CONFIGURAR] Valores passados para db.set_settings: Guild ID={interaction.guild.id}, Verificado ID={cargo_verificado.id}, Não Verificado ID={cargo_nao_verificado.id}, Canal Logs ID={canal_logs.id}")

    embed = discord.Embed(
        title="Configuração Atualizada!",
        description="As configurações de verificação do servidor foram salvas com sucesso.",
        color=0x2ECC71 # Verde
    )
    embed.add_field(name="Cargo Verificado", value=cargo_verificado.mention, inline=False)
    embed.add_field(name="Cargo Não Verificado", value=cargo_nao_verificado.mention, inline=False)
    embed.add_field(name="Canal de Logs", value=canal_logs.mention, inline=False)
    embed.set_footer(text=f"Configurado por {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)

    # Após configurar, tenta enviar um log de teste para o novo canal
    try:
        test_embed = discord.Embed(
            description="✅ Este é um log de teste para confirmar que o canal de logs está funcionando corretamente após a configuração.",
            color=0x2ECC71
        )
        test_embed.set_author(name="Teste de Canal de Logs", icon_url=bot.user.display_avatar.url)
        # await log_action(interaction.guild, test_embed) # Chame sua função log_action de debug

        # OU, para um teste mais direto sem depender do log_action:
        if canal_logs:
            await canal_logs.send(embed=test_embed)
            print("[DEBUG - COMANDO CONFIGURAR] Embed de teste enviado diretamente para o canal de logs.")
        else:
            print("[DEBUG - COMANDO CONFIGURAR] Canal de logs é None após configuração, não foi possível enviar teste direto.")

    except Exception as e:
        print(f"[DEBUG - COMANDO CONFIGURAR] ERRO ao enviar embed de teste após configuração: {e}")
        traceback.print_exc()

@bot.tree.command(name="verificar_manual", description="[Admin] Verifica um membro manualmente.")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.describe(membro="O membro a ser verificado.")
async def verificar_manual(interaction: discord.Interaction, membro: discord.Member):
    verified_role_id, unverified_role_id, _, _ = db.get_settings(interaction.guild.id)
    if not verified_role_id or not unverified_role_id:
        return await interaction.response.send_message("❌ Cargos não configurados.", ephemeral=True)
    verified_role = interaction.guild.get_role(verified_role_id)
    if verified_role and verified_role in membro.roles:
        return await interaction.response.send_message(f"ℹ️ O membro {membro.mention} já está verificado.", ephemeral=True)
    unverified_role = interaction.guild.get_role(unverified_role_id)
    if verified_role and unverified_role:
        await membro.remove_roles(unverified_role, reason="Verificação manual")
        await membro.add_roles(verified_role, reason="Verificação manual")
        db.add_verified_user(membro.id, interaction.guild.id)
        await interaction.response.send_message(f"✅ `{membro.display_name}` verificado manualmente.", ephemeral=True)
        log_embed = discord.Embed(title="ℹ️ Verificação Manual", color=discord.Color.light_grey())
        log_embed.add_field(name="Membro Verificado", value=f"{membro.mention} (`{membro.id}`)", inline=False)
        log_embed.add_field(name="Moderador", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        await log_action(interaction.guild, embed=log_embed)
    else:
        await interaction.response.send_message("❌ Não encontrei um dos cargos configurados.", ephemeral=True)

@bot.tree.command(name="desverificar", description="[Admin] Remove a verificação de um membro.")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.describe(membro="O membro que será desverificado.", motivo="O motivo para a remoção da verificação.")
async def desverificar(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    await interaction.response.defer(ephemeral=True)
    verified_role_id, unverified_role_id, _, _ = db.get_settings(interaction.guild.id)
    if not verified_role_id or not unverified_role_id:
        return await interaction.followup.send("❌ Cargos de verificação não configurados.", ephemeral=True)
    verified_role = interaction.guild.get_role(verified_role_id)
    unverified_role = interaction.guild.get_role(unverified_role_id)
    if not verified_role or not unverified_role:
        return await interaction.followup.send("❌ Um dos cargos de verificação não foi encontrado.", ephemeral=True)
    if verified_role not in membro.roles:
        return await interaction.followup.send(f"ℹ️ O membro {membro.mention} já não possui o cargo de verificado.", ephemeral=True)
    try:
        await membro.remove_roles(verified_role, reason=f"Desverificado por {interaction.user}. Motivo: {motivo}")
        await membro.add_roles(unverified_role, reason=f"Desverificado por {interaction.user}. Motivo: {motivo}")
        db.remove_verified_user(membro.id, interaction.guild.id)
        await interaction.followup.send(f"✅ O membro {membro.mention} foi desverificado.", ephemeral=True)
        log_embed = discord.Embed(title="❗ Membro Desverificado", color=discord.Color.orange())
        log_embed.add_field(name="Membro", value=membro.mention, inline=False)
        log_embed.add_field(name="Moderador", value=interaction.user.mention, inline=False)
        log_embed.add_field(name="Motivo", value=motivo, inline=False)
        await log_action(interaction.guild, embed=log_embed)
        await membro.send(f"⚠️ Sua verificação no servidor **{interaction.guild.name}** foi removida por um administrador. Motivo: **{motivo}**.")
    except discord.Forbidden:
        await interaction.followup.send("❌ Erro de permissão. Não consigo gerenciar os cargos deste membro.", ephemeral=True)

@bot.tree.command(name="info_membro", description="[Admin] Mostra informações detalhadas sobre um membro.")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.describe(membro="O membro sobre o qual você quer informações.")
async def info_membro(interaction: discord.Interaction, membro: discord.Member):
    await interaction.response.defer(ephemeral=True)
    embed = discord.Embed(title=f"Informações de {membro.display_name}", color=membro.color or discord.Color.blue())
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="ID do Usuário", value=f"`{membro.id}`", inline=False)
    if membro.joined_at:
        embed.add_field(name="Entrou no Servidor", value=f"<t:{int(membro.joined_at.timestamp())}:F>", inline=False)
    embed.add_field(name="Conta Criada em", value=f"<t:{int(membro.created_at.timestamp())}:F>", inline=False)
    
    verified_at = db.get_verified_user(membro.id, interaction.guild.id)
    if verified_at: status = f"✅ Verificado em <t:{verified_at}:f>"
    elif db.get_verification(membro.id): status = "⏳ Verificação Pendente"
    else: status = "❌ Não Verificado"
    embed.add_field(name="Status da Verificação", value=status, inline=False)
    
    roles = [role.mention for role in reversed(membro.roles) if role.name != "@everyone"]
    if roles:
        embed.add_field(name=f"Cargos ({len(roles)})", value=" ".join(roles) if len(" ".join(roles)) < 1024 else "Muitos cargos para exibir.", inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="guia_staff", description="[Admin] Mostra um guia de como configurar e usar o bot.")
@app_commands.checks.has_permissions(administrator=True)
async def guia_staff(interaction: discord.Interaction):
    embed = discord.Embed(title="📘 Guia de Configuração e Uso do Bot", color=discord.Color.blue())
    embed.add_field(name="PASSO 1: Configuração", value=f"Use `/configurar` para definir os cargos (`verificado`, `não verificado`) e o `canal de logs`.", inline=False)
    embed.add_field(name="⚠️ PASSO 2: Hierarquia de Cargos", value=f"O cargo do bot deve estar **ACIMA** dos cargos que ele precisa gerenciar.", inline=False)
    embed.add_field(name="Comandos de Staff", value=f"• `/verificar_manual <membro>`\n• `/status_verificacao <membro>`\n• `/seguranca bloqueio <ativar>`\n• `/desverificar <membro> <motivo>`\n• `/info-membro <membro>`", inline=False)
    embed.set_footer(text="Comandos de domínio são restritos ao Dono do Bot.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="status_verificacao", description="[Admin] Checa o status de verificação de um membro.")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.describe(membro="O membro que você deseja checar.")
async def status_verificacao(interaction: discord.Interaction, membro: discord.Member):
    await interaction.response.defer(ephemeral=True)
    verified_role_id, *_, lockdown_enabled = db.get_settings(interaction.guild.id)
    role = interaction.guild.get_role(verified_role_id) if verified_role_id else None
    if not role: return await interaction.followup.send("❌ Cargo de verificado não configurado.", ephemeral=True)
    if role in membro.roles:
        embed = discord.Embed(title="Status: Concluído", description=f"✅ {membro.mention} já está verificado.", color=discord.Color.green())
        return await interaction.followup.send(embed=embed)
    if verification_data := db.get_verification(membro.id):
        *_, attempts, created_at_timestamp, current_input = verification_data
        expiry_time = created_at_timestamp + 600
        embed = discord.Embed(title="Status: Pendente", description=f"⏳ {membro.mention} iniciou o processo.", color=discord.Color.gold())
        embed.add_field(name="Tentativas", value=f"`{attempts} de 3`", inline=True)
        embed.add_field(name="Código Digitado", value=f"`{current_input or 'Nenhum'}`", inline=True)
        embed.add_field(name="Iniciada em", value=f"<t:{created_at_timestamp}:f>", inline=False)
        embed.add_field(name="Expira em", value=f"<t:{int(expiry_time)}:R>", inline=True)
        return await interaction.followup.send(embed=embed)
    embed = discord.Embed(title="Status: Não Iniciado", description=f"ℹ️ {membro.mention} não está verificado.", color=discord.Color.light_grey())
    await interaction.followup.send(embed=embed)

# --- COMANDOS DO DONO ---
@bot.tree.command(name="bloquear_dominio", description="[Dono do Bot] Bloqueia um domínio de e-mail.")
@app_commands.describe(dominio="O domínio a ser bloqueado (ex: temp-mail.org)")
async def bloquear_dominio(interaction: discord.Interaction, dominio: str):
    if interaction.user.id != BOT_OWNER_ID:
        return await interaction.response.send_message("❌ Este comando é restrito ao dono do bot.", ephemeral=True)
    
    dominio_limpo = dominio.lower().strip().replace('@', '')

    db.add_blocked_domain(dominio_limpo)
    await interaction.response.send_message(f"✅ O domínio `{dominio_limpo}` foi adicionado à lista de bloqueio.", ephemeral=True)

@bot.tree.command(name="desbloquear_dominio", description="[Dono do Bot] Remove um domínio da lista de bloqueio.")
@app_commands.describe(dominio="O domínio a ser desbloqueado.")
async def desbloquear_dominio(interaction: discord.Interaction, dominio: str):
    if interaction.user.id != BOT_OWNER_ID:
        return await interaction.response.send_message("❌ Este comando é restrito ao dono do bot.", ephemeral=True)

    dominio_input = dominio.lower().strip()
    dominio_limpo = dominio_input.replace('@', '')
    
    # Tenta remover tanto a versão limpa quanto a versão com @
    removido_limpo = db.remove_blocked_domain(dominio_limpo)
    removido_sujo = db.remove_blocked_domain(dominio_input)

    if removido_limpo > 0 or removido_sujo > 0:
        await interaction.response.send_message(f"✅ O domínio relacionado a `{dominio}` foi removido da lista de bloqueio.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ O domínio `{dominio}` não foi encontrado na lista de bloqueio.", ephemeral=True)

@bot.tree.command(name="listar_dominios_bloqueados", description="[Dono do Bot] Mostra todos os domínios bloqueados.")
async def listar_dominios_bloqueados(interaction: discord.Interaction):
    if interaction.user.id != BOT_OWNER_ID:
        return await interaction.response.send_message("❌ Este comando é restrito ao dono do bot.", ephemeral=True)
    dominios = db.get_all_blocked_domains()
    if not dominios:
        return await interaction.response.send_message("ℹ️ Não há nenhum domínio bloqueado no momento.", ephemeral=True)
    descricao = "\n".join([f"- `{d}`" for d in dominios])
    embed = discord.Embed(title="🚫 Domínios de E-mail Bloqueados", description=descricao, color=discord.Color.orange())
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- GRUPO DE COMANDOS DE SEGURANÇA ---
seguranca_group = app_commands.Group(name="seguranca", description="Comandos para gerenciar a segurança do servidor.")

@seguranca_group.command(name="bloqueio", description="[Admin] Ativa/desativa o modo de segurança do servidor.")
@app_commands.describe(ativar="True para ativar, False para desativar.")
async def lockdown(interaction: discord.Interaction, ativar: bool):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Você precisa ser um administrador para usar este comando.", ephemeral=True)
    db.set_lockdown(interaction.guild.id, ativar)
    status_text, color = ("ATIVADO", discord.Color.red()) if ativar else ("DESATIVADO", discord.Color.green())
    await interaction.response.send_message(f"✅ Modo de Bloqueio (Lockdown) foi **{status_text}**.", ephemeral=True)
    log_embed = discord.Embed(title=f"🛡️ Modo de Segurança {status_text}", color=color)
    log_embed.set_footer(text=f"Ação por: {interaction.user}")
    await log_action(interaction.guild, embed=log_embed)

bot.tree.add_command(seguranca_group)

# --- EVENTOS DO BOT ---
@bot.event
async def on_member_join(member: discord.Member):
    if member.bot: return
    now = time.time()
    if member.guild.id not in recent_joins:
        recent_joins[member.guild.id] = deque()
    recent_joins[member.guild.id].append(now)
    while recent_joins[member.guild.id] and now - recent_joins[member.guild.id][0] > RAID_THRESHOLD_SECONDS:
        recent_joins[member.guild.id].popleft()
    if len(recent_joins[member.guild.id]) >= RAID_THRESHOLD_COUNT:
        alert_embed = discord.Embed(title="🚨 ALERTA DE RAID DETECTADO!", color=discord.Color.dark_red())
        alert_embed.add_field(name="Atividade Suspeita", value=f"**{len(recent_joins[member.guild.id])}** membros entraram nos últimos {RAID_THRESHOLD_SECONDS} segundos.", inline=False)
        alert_embed.add_field(name="Ação Imediata", value="@here Ação da staff é necessária.", inline=False)
        alert_embed.add_field(name="Ação Recomendada", value="Use `/seguranca bloqueio ativar:True` para bloquear novas verificações.")
        await log_action(member.guild, embed=alert_embed)
        recent_joins[member.guild.id].clear()
    
    # CORREÇÃO AQUI: Desempacota 4 valores
    _, unverified_role_id, _, _ = db.get_settings(member.guild.id)
    if unverified_role_id and (role := member.guild.get_role(unverified_role_id)):
        try:
            await member.add_roles(role, reason="Novo membro.")
        except discord.Forbidden:
            log_embed = discord.Embed(title="🔥 Erro de Permissão na Entrada", color=discord.Color.red(), description=f"Não foi possível atribuir o cargo de não verificado para {member.mention}.")
            await log_action(member.guild, embed=log_embed)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    user_error_message = "🔴 Ocorreu um erro inesperado. A equipe de administração foi notificada."
    try:
        if interaction.response.is_done(): await interaction.followup.send(user_error_message, ephemeral=True)
        else: await interaction.response.send_message(user_error_message, ephemeral=True)
    except discord.NotFound:
        print("Não foi possível notificar o usuário sobre um erro.")
    error_embed = discord.Embed(title="🔥 Erro Inesperado em Comando", color=discord.Color.red())
    error_embed.add_field(name="Comando", value=f"`{interaction.command.name}`", inline=False)
    error_embed.add_field(name="Usuário", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
    original_error = getattr(error, 'original', error)
    if isinstance(original_error, discord.errors.Forbidden):
        error_embed.add_field(name="⚠️ Erro de Permissão", value="O bot não tem permissão. Verifique a hierarquia de cargos.", inline=False)
    traceback_str = ''.join(traceback.format_exception(type(original_error), original_error, original_error.__traceback__))
    error_embed.add_field(name="Traceback", value=f"```py\n{traceback_str[:1000]}\n...```", inline=False)
    if interaction.guild: await log_action(interaction.guild, embed=error_embed)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    quantidade_servidores = len(bot.guilds)
    print(f'O bot está em {quantidade_servidores} servidores.')
    activity = discord.Game(name="Astro • Melhor bot de verificação!") 
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"Status definido para 'Jogando {activity.name}'")
    await bot.tree.sync()
    print("Comandos sincronizados.")

bot.run(os.getenv("DISCORD_TOKEN"))