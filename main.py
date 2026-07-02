import discord
from discord import app_commands
from discord.ui import Button, View, Modal
import datetime

# إعدادات البوت
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ========== إعدادات المتجر ==========
STORE_NAME = "Zero Code"  # ← اكتب اسم متجرك هنا
SUPPORT_ROLE_ID = 1522221153073238036  # ← ضع معرف رتبة الدعم هنا
TICKET_CATEGORY_ID = 1520757766501961859  # ← ضع معرف تصنيف التكتات هنا
# ====================================

# ========== الأزرار الاحترافية ==========
class TicketButtons(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # زر شراء المنتج 🛒
        self.buy_button = Button(
            label="شراء منتج",
            custom_id="buy_product",
            emoji="🛒",
            style=discord.ButtonStyle.green
        )
        self.buy_button.callback = self.buy_callback
        self.add_item(self.buy_button)
        
        # زر الاستفسار ❓
        self.inquiry_button = Button(
            label="استفسار",
            custom_id="inquiry",
            emoji="❓",
            style=discord.ButtonStyle.blue
        )
        self.inquiry_button.callback = self.inquiry_callback
        self.add_item(self.inquiry_button)
        
        # زر المشكلة ⚠️
        self.problem_button = Button(
            label="مشكلة",
            custom_id="problem",
            emoji="⚠️",
            style=discord.ButtonStyle.red
        )
        self.problem_button.callback = self.problem_callback
        self.add_item(self.problem_button)
    
    async def buy_callback(self, interaction: discord.Interaction):
        await self.create_ticket(interaction, "شراء منتج", "🛒")
    
    async def inquiry_callback(self, interaction: discord.Interaction):
        await self.create_ticket(interaction, "استفسار", "❓")
    
    async def problem_callback(self, interaction: discord.Interaction):
        await self.create_ticket(interaction, "مشكلة", "⚠️")
    
    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str, emoji: str):
        # التحقق من وجود تكت بالفعل
        for channel in interaction.guild.text_channels:
            if f"tkt-{interaction.user.name}" in channel.name:
                embed = discord.Embed(
                    title="⚠️ لديك تكت مفتوح بالفعل!",
                    description=f"تكتك الحالي: {channel.mention}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # إنشاء التكت
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # إضافة رتبة الدعم
        if SUPPORT_ROLE_ID:
            support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        channel_name = f"tkt-{interaction.user.name}-{ticket_type}"
        
        category = None
        if TICKET_CATEGORY_ID:
            category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        
        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"تكت من قبل {interaction.user.name}"
        )
        
        # إنشاء الإيمبدج الترحيبي
        embed = discord.Embed(
            title=f"{emoji} {STORE_NAME} - نظام الدعم",
            description=f"**مرحباً {interaction.user.mention}!**\n\n"
                       f"**نوع التكت:** {ticket_type}\n"
                       f"**تم إنشاء التكت:** <t:{int(datetime.datetime.now().timestamp())}:R>\n\n"
                       f"📝 **يرجى شرح طلبك بالتفصيل وسنقوم بالرد عليك في أقرب وقت**",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"ID: {interaction.user.id}")
        
        # أزرار التكت
        close_button = Button(
            label="إغلاق التكت",
            custom_id="close_ticket",
            emoji="🔒",
            style=discord.ButtonStyle.red
        )
        close_button.callback = lambda i: self.close_ticket(i, channel)
        
        claim_button = Button(
            label="استلام التكت",
            custom_id="claim_ticket",
            emoji="📥",
            style=discord.ButtonStyle.green
        )
        claim_button.callback = lambda i: self.claim_ticket(i, channel)
        
        view = View()
        view.add_item(claim_button)
        view.add_item(close_button)
        
        await channel.send(
            content=f"{interaction.user.mention} | <@&{SUPPORT_ROLE_ID}>" if SUPPORT_ROLE_ID else f"{interaction.user.mention}",
            embed=embed,
            view=view
        )
        
        # رسالة النجاح
        success_embed = discord.Embed(
            title="✅ تم إنشاء التكت بنجاح!",
            description=f"تم إنشاء تكتك: {channel.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    async def close_ticket(self, interaction: discord.Interaction, channel):
        # التحقق من الصلاحيات
        if interaction.user.id != channel.name.split('-')[1] and not interaction.user.guild_permissions.administrator:
            if SUPPORT_ROLE_ID:
                role = interaction.guild.get_role(SUPPORT_ROLE_ID)
                if role not in interaction.user.roles:
                    await interaction.response.send_message("❌ ليس لديك صلاحية إغلاق هذا التكت!", ephemeral=True)
                    return
        
        # تأكيد الإغلاق
        confirm_view = View()
        confirm_button = Button(label="تأكيد الإغلاق", style=discord.ButtonStyle.red, emoji="✅")
        cancel_button = Button(label="إلغاء", style=discord.ButtonStyle.gray, emoji="❌")
        
        async def confirm_close(i):
            await channel.delete(reason="تم إغلاق التكت")
        
        async def cancel_close(i):
            await i.message.delete()
        
        confirm_button.callback = confirm_close
        cancel_button.callback = cancel_close
        confirm_view.add_item(confirm_button)
        confirm_view.add_item(cancel_button)
        
        await interaction.response.send_message(
            "⚠️ هل أنت متأكد من إغلاق التكت؟",
            view=confirm_view,
            ephemeral=True
        )

    async def claim_ticket(self, interaction: discord.Interaction, channel):
        if SUPPORT_ROLE_ID:
            role = interaction.guild.get_role(SUPPORT_ROLE_ID)
            if role and role not in interaction.user.roles:
                await interaction.response.send_message("❌ يجب أن تكون من فريق الدعم!", ephemeral=True)
                return
        
        embed = discord.Embed(
            title="📥 تم استلام التكت",
            description=f"**الموظف:** {interaction.user.mention}\n"
                       f"**الوقت:** <t:{int(datetime.datetime.now().timestamp())}:R>",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ تم استلام التكت!", ephemeral=True)

# ========== رسالة التكتات الرئيسية ==========
async def send_ticket_panel(ctx):
    embed = discord.Embed(
        title=f"🎫 **{STORE_NAME}** - نظام الدعم الفني",
        description="**مرحباً بك في نظام الدعم!**\n\n"
                   "اختر نوع طلبك من الأزرار أدناه لإنشاء تكت:\n\n"
                   "🛒 **شراء منتج** - للاستفسار عن المنتجات والشراء\n"
                   "❓ **استفسار** - لأي استفسار عام\n"
                   "⚠️ **مشكلة** - للإبلاغ عن مشكلة\n\n"
                   f"**{STORE_NAME}** - نحن هنا لمساعدتك! 💙",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now()
    )
    embed.set_author(name=STORE_NAME, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    
    await ctx.send(embed=embed, view=TicketButtons())

# ========== حدث عند جاهزية البوت ==========
@client.event
async def on_ready():
    print(f'✅ البوت متصل: {client.user}')
    print(f'🔗 الرابط: https://discord.com/api/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot%20applications.commands')
    
    # مزامنة الأوامر
    await tree.sync()

# ========== أمر إنشاء لوحة التكتات ==========
@tree.command(name="ticket", description="إنشاء لوحة التكتات")
@tree.command(name="panel", description="إرسال لوحة التكتات")
async def ticket_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ ليس لديك صلاحية استخدام هذا الأمر!", ephemeral=True)
        return
    
    await interaction.response.send_message("✅ تم إرسال لوحة التكتات!")
    await send_ticket_panel(interaction)

# ========== عند منشن البوت ==========
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # التحقق من المنشن
    if client.user.mentioned_in(message):
        # البحث عن تكتات المستخدم
        user_tickets = []
        for channel in message.guild.text_channels:
            if f"tkt-{message.author.name}" in channel.name:
                user_tickets.append(channel.mention)
        
        if user_tickets:
            embed = discord.Embed(
                title="🎫 تكتاتك المفتوحة",
                description="**لديك التكتات التالية:**\n\n" + "\n".join(user_tickets),
                color=discord.Color.blue()
            )
            await message.author.send(embed=embed)
            await message.reply("✅ تم إرسال معلومات تكتاتك في الخاص!", delete_after=5)
        else:
            embed = discord.Embed(
                title="🎫 لا يوجد تكتات مفتوحة",
                description="ليس لديك تكتات مفتوحة حالياً.\nاستخدم الأزرار لإنشاء تكت جديد!",
                color=discord.Color.orange()
            )
            await message.author.send(embed=embed)
            await message.reply("✅ تم الإرسال في الخاص!", delete_after=5)

# ========== تشغيل البوت ==========
# استخدم:
import os
from dotenv import load_dotenv

load_dotenv()
client.run(os.getenv('DISCORD_TOKEN'))