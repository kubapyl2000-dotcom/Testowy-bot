import os
import json
import datetime
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

# ========================
#   ZMIENNE ŚRODOWISKOWE (ustawiasz raz, przy hostingu)
# ========================

TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")
TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", "0"))

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(CONFIG_PATH)) or ".", "obrazki")
os.makedirs(IMAGES_DIR, exist_ok=True)

# ========================
#   DOMYŚLNA KONFIGURACJA
#   Wszystko poniżej edytujesz później komendami /konfiguracja na Discordzie -
#   ten słownik to tylko "seed" na pierwsze uruchomienie.
# ========================

DEFAULT_CONFIG = {
    "nazwa_sklepu": "MójShop",
    "footer": "© {rok} MójShop",

    "colors": {
        "akcent": "#5865F2",     # główny kolor większości paneli
        "sukces": "#57F287",
        "blad": "#ED4245",
    },
    "images": {
        "weryfikacja": "",
        "regulamin": "",
        "ticket_panel": "",
        "opinie": "",
        "partnerstwo": "",
        "statystyki": "",
        "nowa_osoba": "",
    },

    "channels": {
        "weryfikacja": 0,
        "ticket_panel": 0,
        "opinie": 0,
        "partnerstwa": 0,
        "blacklista": 0,
        "nowa_osoba": 0,
    },
    "roles": {
        "staff": 0,
        "zweryfikowany": 0,
        "realizator": 0,
    },
    "ticket_category_id": 0,

    "panel_messages": {},  # klucz -> {"channel_id":.., "message_id":..} - żeby edycja configu edytowała istniejący panel, a nie duplikowała

    # ---- Weryfikacja ----
    "weryfikacja_tytul": "💎 {sklep} × Weryfikacja",
    "weryfikacja_opis": (
        "» Kliknij przycisk **poniżej**, aby się zweryfikować!\n"
        "» Dzięki temu uzyskasz pełny dostęp do wszystkich kanałów serwera.\n\n"
        "*Nie sprzedajemy Cię jako membersa / nie dodajemy Cię nigdzie. "
        "Weryfikacja odbywa się w całości na Discordzie, bez żadnych zewnętrznych stron.*"
    ),

    # ---- Regulamin (wielostronicowy, jak w panelu na screenach) ----
    "regulamin_strony": [
        {
            "tytul": "1. Zasady ogólne",
            "tresc": (
                "1.1. Administracja może odmówić obsługi lub usunąć użytkownika, który łamie regulamin.\n"
                "1.2. Regulamin może zostać zmieniony w każdej chwili.\n"
                "1.3. Korzystając z serwera, akceptujesz ten regulamin."
            ),
        },
        {
            "tytul": "2. Zakupy",
            "tresc": (
                "2.1. Wszystkie zakupy są ostateczne, chyba że wcześniej ustalono inaczej.\n"
                "2.2. Realizacja zamówienia trwa do 6 godzin.\n"
                "2.3. Dane użytkowników przetwarzamy tylko na potrzeby realizacji zamówienia."
            ),
        },
        {
            "tytul": "3. Legit check i reklamacje",
            "tresc": (
                "3.1. Masz 24 godziny na dodanie legit checka po zakupie.\n"
                "3.2. Reklamacje przyjmujemy tylko przez system ticketów.\n"
                "3.3. Bez legit checka reklamacji nie rozpatrujemy."
            ),
        },
        {
            "tytul": "4. Zachowanie na serwerze",
            "tresc": (
                "4.1. Podczas zakupów, reklamacji i pytań wymagana jest kultura i szacunek.\n"
                "4.2. Prowokacje, spam i trolling skutkują ostrzeżeniami lub banem."
            ),
        },
    ],

    # ---- Panel ticketów ----
    "ticket_tytul": "💎 {sklep} × Tickety",
    "ticket_opis": (
        "» Chcesz zakupić produkt bądź potrzebujesz pomocy od administracji?\n"
        "» Skorzystaj z menu **poniżej** i wybierz odpowiednią kategorię, a my zajmiemy się resztą!"
    ),
    "ticket_kategorie": {
        "kupic": {"etykieta": "🛒 Chcę zakupić produkt", "opis": "Kliknij, aby zakupić produkt!"},
        "partnerstwo": {"etykieta": "🤝 Chcę nawiązać partnerstwo", "opis": "Kliknij, jeśli chcesz nawiązać partnerstwo!"},
        "pomoc": {"etykieta": "ℹ️ Potrzebuję pomocy", "opis": "Kliknij, jeśli masz pytanie lub problem!"},
        "reklamacja": {"etykieta": "⚙️ Chcę złożyć reklamację", "opis": "Kliknij, aby złożyć reklamację!"},
    },
    "ticket_wiadomosc_tresc": "Witaj na swoim zgłoszeniu, {mention}! Poczekaj cierpliwie na {rola}.",

    # ---- Nowa osoba ----
    "nowa_osoba_tytul": "💎 {sklep} × Nowa Osoba",
    "nowa_osoba_tresc": (
        "» Hejka {mention}! Miło Cię u nas widzieć!\n"
        "» Jest nam mega miło, że wpadłeś. Rozgość się.\n\n"
        "📌 Przypominamy, że nieprzestrzeganie regulaminu może wiązać się z konsekwencjami.\n\n"
        "Dzięki, że wbiłeś! Jesteś naszym **{ilosc}** użytkownikiem."
    ),

    # ---- Program partnerski ----
    "partnerstwo_stawka": 0.70,      # kwota wypłacana realizatorowi za jedno partnerstwo - edytowalna
    "partnerstwo_waluta": "PLN",
    "partnerstwo_dane": {},          # user_id(str) -> {"liczba": int, "zarobek": float}
    "zostan_realizatorem_tytul": "💎 {sklep} × Zostań Realizatorem",
    "zostan_realizatorem_opis": (
        "» Chcesz zarobić w pełni legalną i szybką kasę? Wystarczy realizować partnerstwa na naszym serwerze!\n\n"
        "Stawka za jedno partnerstwo: **{stawka} {waluta}**."
    ),

    # ---- Blacklista ----
    "blacklista_dane": {},  # klucz (nick, lowercase) -> {"powod":.., "data":.., "dodal": staff_id}

    # ---- Opinie ----
    "opinie_tytul": "💎 {sklep} × Wystaw Opinię",
    "opinie_opis": (
        "» Wystawiając nam opinię dajesz innym znać, co Cię u nas zadowoliło.\n"
        "» Będziemy super wdzięczni za każdą wystawioną opinię - to buduje zaufanie do naszego sklepu."
    ),
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = json.loads(json.dumps(DEFAULT_CONFIG))
            for key, value in data.items():
                if isinstance(value, dict) and isinstance(merged.get(key), dict):
                    merged[key].update(value)
                else:
                    merged[key] = value
            return merged
        except Exception as e:
            print(f"Błąd wczytywania configu, używam domyślnego: {e}")
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, ensure_ascii=False, indent=2)


CONFIG = load_config()


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def render(template: str, **kwargs) -> str:
    base = {"sklep": CONFIG.get("nazwa_sklepu", "Shop"), "rok": datetime.datetime.now().year}
    base.update(kwargs)
    return template.format_map(SafeDict(**base))


def hex_to_color(value: str) -> discord.Color:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError("Kolor musi być w formacie HEX, np. #5865F2")
    return discord.Color(int(value, 16))


def get_color(typ: str = "akcent") -> discord.Color:
    try:
        return hex_to_color(CONFIG["colors"].get(typ, "#5865F2"))
    except ValueError:
        return discord.Color.blurple()


def footer_icon(guild: Optional[discord.Guild]):
    return guild.icon.url if guild and guild.icon else None


def base_embed(typ: str = "akcent", **kwargs) -> discord.Embed:
    embed = discord.Embed(color=get_color(typ), timestamp=datetime.datetime.now(datetime.timezone.utc), **kwargs)
    return embed


def set_footer(embed: discord.Embed, guild: Optional[discord.Guild], extra: str = ""):
    tekst = render(CONFIG["footer"])
    if extra:
        tekst = f"{tekst} • {extra}"
    embed.set_footer(text=tekst, icon_url=footer_icon(guild))


def prepare_embed_image(embed: discord.Embed, typ: str, thumb: bool = False) -> Optional[discord.File]:
    sciezka = CONFIG["images"].get(typ)
    if not sciezka or not os.path.exists(sciezka):
        return None
    nazwa = os.path.basename(sciezka)
    if thumb:
        embed.set_thumbnail(url=f"attachment://{nazwa}")
    else:
        embed.set_image(url=f"attachment://{nazwa}")
    return discord.File(sciezka, filename=nazwa)


async def send_or_edit_panel(target: discord.TextChannel, embed: discord.Embed, view: Optional[discord.ui.View],
                              klucz: str, plik: Optional[discord.File] = None):
    """Wysyła panel na kanał, albo edytuje wcześniej wysłaną wiadomość (ten sam klucz + kanał),
    żeby zmiana treści w configu nie tworzyła duplikatów paneli."""
    info = CONFIG["panel_messages"].setdefault(klucz, {"channel_id": 0, "message_id": 0})
    if info["channel_id"] == target.id and info["message_id"]:
        try:
            msg = await target.fetch_message(info["message_id"])
            if plik:
                await msg.edit(embed=embed, view=view, attachments=[plik])
            else:
                await msg.edit(embed=embed, view=view)
            return msg
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass
    msg = await target.send(embed=embed, view=view, file=plik)
    info["channel_id"] = target.id
    info["message_id"] = msg.id
    save_config()
    return msg


# ========================
#   INICJALIZACJA BOTA
# ========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
ADMIN_ONLY = app_commands.checks.has_permissions(administrator=True)


def is_admin(interaction: discord.Interaction) -> bool:
    return bool(interaction.user.guild_permissions.administrator)


def is_staff(interaction: discord.Interaction) -> bool:
    if is_admin(interaction):
        return True
    staff_id = CONFIG["roles"].get("staff")
    if not staff_id:
        return False
    role = interaction.guild.get_role(staff_id)
    return role is not None and role in interaction.user.roles


# ========================
#   WERYFIKACJA
#   (samo przyznanie roli przez bota - bez żadnych zewnętrznych stron/OAuth)
# ========================

class WeryfikacjaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Kliknij, aby się zweryfikować!", style=discord.ButtonStyle.success,
                        emoji="✅", custom_id="shopbot:weryfikacja")
    async def weryfikuj(self, interaction: discord.Interaction, button: discord.ui.Button):
        rola_id = CONFIG["roles"].get("zweryfikowany")
        rola = interaction.guild.get_role(rola_id) if rola_id else None
        if not rola:
            await interaction.response.send_message(
                "⚠️ Rola weryfikacyjna nie jest jeszcze ustawiona. Napisz do administracji.", ephemeral=True)
            return
        if rola in interaction.user.roles:
            await interaction.response.send_message("✅ Jesteś już zweryfikowany/a!", ephemeral=True)
            return
        try:
            await interaction.user.add_roles(rola, reason="Weryfikacja na serwerze")
        except discord.Forbidden:
            await interaction.response.send_message(
                "⚠️ Nie mam uprawnień, aby nadać Ci rolę. Napisz do administracji.", ephemeral=True)
            return
        await interaction.response.send_message("✅ Zweryfikowano pomyślnie! Miłego pobytu.", ephemeral=True)


async def wyslij_panel_weryfikacji(kanal: discord.TextChannel):
    embed = base_embed("akcent", title=render(CONFIG["weryfikacja_tytul"]),
                        description=render(CONFIG["weryfikacja_opis"]))
    plik = prepare_embed_image(embed, "weryfikacja")
    set_footer(embed, kanal.guild)
    await send_or_edit_panel(kanal, embed, WeryfikacjaView(), "weryfikacja", plik)


# ========================
#   REGULAMIN (panel wielostronicowy z Poprzednia/Nastepna)
# ========================

class RegulaminView(discord.ui.View):
    def __init__(self, strona: int = 0):
        super().__init__(timeout=None)
        self.strona = strona
        self.update_buttons()

    def update_buttons(self):
        strony = CONFIG["regulamin_strony"]
        self.poprzednia.disabled = self.strona <= 0
        self.nastepna.disabled = self.strona >= len(strony) - 1

    def build_embed(self, guild: Optional[discord.Guild]) -> discord.Embed:
        strony = CONFIG["regulamin_strony"]
        strona_dane = strony[self.strona]
        embed = base_embed("akcent",
                            title=f"💎 Regulamin {render('{sklep}')} — strona {self.strona + 1}/{len(strony)}",
                            description=f"**{strona_dane['tytul']}**\n\n{strona_dane['tresc']}")
        set_footer(embed, guild)
        return embed

    @discord.ui.button(label="← Poprzednia", style=discord.ButtonStyle.secondary, custom_id="shopbot:regulamin:prev")
    async def poprzednia(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.strona = max(0, self.strona - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)

    @discord.ui.button(label="Następna →", style=discord.ButtonStyle.secondary, custom_id="shopbot:regulamin:next")
    async def nastepna(self, interaction: discord.Interaction, button: discord.ui.Button):
        strony = CONFIG["regulamin_strony"]
        self.strona = min(len(strony) - 1, self.strona + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)


async def wyslij_panel_regulaminu(kanal: discord.TextChannel):
    view = RegulaminView(0)
    embed = view.build_embed(kanal.guild)
    plik = prepare_embed_image(embed, "regulamin")
    await send_or_edit_panel(kanal, embed, view, "regulamin", plik)


class DodajStroneRegulaminuModal(discord.ui.Modal, title="Dodaj stronę regulaminu"):
    tytul = discord.ui.TextInput(label="Tytuł strony", max_length=100, placeholder="np. 6. Bezpieczeństwo")
    tresc = discord.ui.TextInput(label="Treść", style=discord.TextStyle.paragraph, max_length=3500,
                                  placeholder="6.1. ...\n6.2. ...")

    async def on_submit(self, interaction: discord.Interaction):
        CONFIG["regulamin_strony"].append({"tytul": str(self.tytul), "tresc": str(self.tresc)})
        save_config()
        await interaction.response.send_message(
            f"✅ Dodano nową stronę regulaminu ({len(CONFIG['regulamin_strony'])} stron łącznie). "
            f"Użyj `/regulamin wyslij`, aby odświeżyć panel.", ephemeral=True)


class EdytujStroneRegulaminuModal(discord.ui.Modal, title="Edytuj stronę regulaminu"):
    def __init__(self, numer: int):
        super().__init__()
        self.numer = numer
        strona = CONFIG["regulamin_strony"][numer]
        self.tytul = discord.ui.TextInput(label="Tytuł strony", max_length=100, default=strona["tytul"])
        self.tresc = discord.ui.TextInput(label="Treść", style=discord.TextStyle.paragraph, max_length=3500,
                                           default=strona["tresc"])
        self.add_item(self.tytul)
        self.add_item(self.tresc)

    async def on_submit(self, interaction: discord.Interaction):
        CONFIG["regulamin_strony"][self.numer] = {"tytul": str(self.tytul), "tresc": str(self.tresc)}
        save_config()
        await interaction.response.send_message(
            f"✅ Zaktualizowano stronę {self.numer + 1}. Użyj `/regulamin wyslij`, aby odświeżyć panel.",
            ephemeral=True)


# ========================
#   TICKETY
# ========================

class ZamknijTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zamknij ticket", style=discord.ButtonStyle.danger, emoji="🔒",
                        custom_id="shopbot:ticket:zamknij")
    async def zamknij(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction):
            await interaction.response.send_message("⚠️ Tylko staff może zamykać tickety.", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Ticket zostanie zamknięty za 5 sekund...")
        await interaction.channel.edit(name=f"zamkniety-{interaction.channel.name}"[:100])
        await discord.utils.sleep_until(discord.utils.utcnow() + datetime.timedelta(seconds=5))
        try:
            await interaction.channel.delete(reason=f"Ticket zamknięty przez {interaction.user}")
        except discord.HTTPException:
            pass


class TicketKategoriaSelect(discord.ui.Select):
    def __init__(self):
        opcje = [
            discord.SelectOption(label=dane["etykieta"], description=dane["opis"], value=klucz)
            for klucz, dane in CONFIG["ticket_kategorie"].items()
        ]
        super().__init__(placeholder="Wybierz interesującą Cię kategorię ticketa!", options=opcje,
                          custom_id="shopbot:ticket:select", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        klucz = self.values[0]
        guild = interaction.guild
        kategoria_id = CONFIG.get("ticket_category_id")
        kategoria = guild.get_channel(kategoria_id) if kategoria_id else None

        istniejacy = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name}".lower()[:100])
        if istniejacy:
            await interaction.response.send_message(f"⚠️ Masz już otwarty ticket: {istniejacy.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        staff_id = CONFIG["roles"].get("staff")
        staff_rola = guild.get_role(staff_id) if staff_id else None
        if staff_rola:
            overwrites[staff_rola] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        kanal = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}"[:100],
            category=kategoria,
            overwrites=overwrites,
            reason=f"Nowy ticket ({klucz}) od {interaction.user}",
        )

        embed = base_embed("akcent", title=f"🎫 Ticket — {CONFIG['ticket_kategorie'][klucz]['etykieta']}",
                            description=render(CONFIG["ticket_wiadomosc_tresc"],
                                                mention=interaction.user.mention,
                                                rola=staff_rola.mention if staff_rola else "administracją"))
        set_footer(embed, guild)
        await kanal.send(content=f"{interaction.user.mention}" + (f" {staff_rola.mention}" if staff_rola else ""),
                          embed=embed, view=ZamknijTicketView())

        await interaction.response.send_message(f"✅ Utworzono Twój ticket: {kanal.mention}", ephemeral=True)


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketKategoriaSelect())


async def wyslij_panel_ticketow(kanal: discord.TextChannel):
    embed = base_embed("akcent", title=render(CONFIG["ticket_tytul"]), description=render(CONFIG["ticket_opis"]))
    plik = prepare_embed_image(embed, "ticket_panel")
    set_footer(embed, kanal.guild)
    await send_or_edit_panel(kanal, embed, TicketPanelView(), "ticket_panel", plik)


# ========================
#   OPINIE
# ========================

class OpiniaModal(discord.ui.Modal, title="Wystaw opinię"):
    tresc = discord.ui.TextInput(label="Treść opinii", style=discord.TextStyle.paragraph, max_length=1000)
    produkt = discord.ui.TextInput(label="Ocena produktu (1-5)", max_length=1, default="5")
    czas = discord.ui.TextInput(label="Ocena czasu realizacji (1-5)", max_length=1, default="5")
    przebieg = discord.ui.TextInput(label="Ocena przebiegu transakcji (1-5)", max_length=1, default="5")
    poprawa = discord.ui.TextInput(label="Co możemy poprawić?", required=False, max_length=300, default="Nic")

    async def on_submit(self, interaction: discord.Interaction):
        def gwiazdki(v: str) -> str:
            try:
                n = max(1, min(5, int(v)))
            except ValueError:
                n = 5
            return "⭐" * n + "▫️" * (5 - n)

        kanal_id = CONFIG["channels"].get("opinie")
        kanal = interaction.guild.get_channel(kanal_id) if kanal_id else None
        if not kanal:
            await interaction.response.send_message(
                "⚠️ Kanał opinii nie jest jeszcze ustawiony. Napisz do administracji.", ephemeral=True)
            return

        embed = base_embed("akcent", title="💎 Opinia")
        embed.add_field(name="Twórca opinii", value=interaction.user.mention, inline=False)
        embed.add_field(name="Treść", value=str(self.tresc), inline=False)
        embed.add_field(name="Co możemy poprawić?", value=str(self.poprawa), inline=False)
        embed.add_field(name="🛒 Jakość produktu", value=gwiazdki(str(self.produkt)))
        embed.add_field(name="🏛️ Czas realizacji", value=gwiazdki(str(self.czas)))
        embed.add_field(name="⏱️ Przebieg transakcji", value=gwiazdki(str(self.przebieg)))
        set_footer(embed, interaction.guild)
        wiadomosc = await kanal.send(embed=embed)
        try:
            await wiadomosc.add_reaction("❤️")
        except discord.HTTPException:
            pass
        await interaction.response.send_message(f"✅ Dziękujemy za opinię! Widać ją na {kanal.mention}.", ephemeral=True)


class WystawOpinieView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Kliknij, aby wystawić opinię!", style=discord.ButtonStyle.primary, emoji="✍️",
                        custom_id="shopbot:opinia")
    async def wystaw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OpiniaModal())


async def wyslij_panel_opinii(kanal: discord.TextChannel):
    embed = base_embed("akcent", title=render(CONFIG["opinie_tytul"]), description=render(CONFIG["opinie_opis"]))
    plik = prepare_embed_image(embed, "opinie")
    set_footer(embed, kanal.guild)
    await send_or_edit_panel(kanal, embed, WystawOpinieView(), "opinie", plik)


# ========================
#   BLACKLISTA  (/blacklista dodaj|usun|sprawdz|lista)
# ========================

blacklista_group = app_commands.Group(name="blacklista", description="Zarządzanie blacklistą użytkowników")


@blacklista_group.command(name="dodaj", description="Dodaje użytkownika do blacklisty")
@app_commands.describe(nick="Nick / identyfikator użytkownika", powod="Powód dodania do blacklisty")
async def blacklista_dodaj(interaction: discord.Interaction, nick: str, powod: str):
    if not is_staff(interaction):
        await interaction.response.send_message("⚠️ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return
    klucz = nick.lower().lstrip("@")
    CONFIG["blacklista_dane"][klucz] = {
        "nick": nick,
        "powod": powod,
        "data": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        "dodal": interaction.user.id,
    }
    save_config()

    embed = base_embed("blad", title=f"💎 {render('{sklep}')} × Blacklista")
    embed.add_field(name="Użytkownik", value=nick, inline=False)
    embed.add_field(name="Powód", value=powod, inline=False)
    embed.add_field(name="Dodane przez", value=interaction.user.mention, inline=False)
    set_footer(embed, interaction.guild)

    kanal_id = CONFIG["channels"].get("blacklista")
    kanal = interaction.guild.get_channel(kanal_id) if kanal_id else interaction.channel
    await kanal.send(embed=embed)
    if kanal.id != interaction.channel.id:
        await interaction.response.send_message(f"✅ Dodano do blacklisty. Ogłoszenie na {kanal.mention}.", ephemeral=True)
    else:
        await interaction.response.send_message("✅ Dodano do blacklisty.", ephemeral=True)


@blacklista_group.command(name="usun", description="Usuwa użytkownika z blacklisty")
@app_commands.describe(nick="Nick / identyfikator użytkownika")
async def blacklista_usun(interaction: discord.Interaction, nick: str):
    if not is_staff(interaction):
        await interaction.response.send_message("⚠️ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return
    klucz = nick.lower().lstrip("@")
    if klucz not in CONFIG["blacklista_dane"]:
        await interaction.response.send_message("⚠️ Nie znaleziono takiego wpisu na blackliście.", ephemeral=True)
        return
    del CONFIG["blacklista_dane"][klucz]
    save_config()
    await interaction.response.send_message(f"✅ Usunięto **{nick}** z blacklisty.", ephemeral=True)


@blacklista_group.command(name="sprawdz", description="Sprawdza, czy dany nick jest na blackliście")
@app_commands.describe(nick="Nick / identyfikator użytkownika")
async def blacklista_sprawdz(interaction: discord.Interaction, nick: str):
    klucz = nick.lower().lstrip("@")
    wpis = CONFIG["blacklista_dane"].get(klucz)
    if not wpis:
        await interaction.response.send_message(f"✅ **{nick}** nie widnieje na blackliście.", ephemeral=True)
        return
    embed = base_embed("blad", title="💎 Wpis na blackliście")
    embed.add_field(name="Użytkownik", value=wpis["nick"], inline=False)
    embed.add_field(name="Powód", value=wpis["powod"], inline=False)
    embed.add_field(name="Data dodania", value=wpis["data"], inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@blacklista_group.command(name="lista", description="Wyświetla całą blacklistę")
async def blacklista_lista(interaction: discord.Interaction):
    dane = CONFIG["blacklista_dane"]
    if not dane:
        await interaction.response.send_message("📋 Blacklista jest obecnie pusta.", ephemeral=True)
        return
    linie = [f"• **{wpis['nick']}** — {wpis['powod']} ({wpis['data']})" for wpis in dane.values()]
    embed = base_embed("akcent", title="💎 Blacklista — pełna lista", description="\n".join(linie)[:4000])
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ========================
#   PROGRAM PARTNERSKI
#   Realizator zgłasza nawiązane partnerstwo -> staff je zatwierdza -> naliczana jest wypłata
#   wg aktualnej, edytowalnej stawki. To tylko ewidencja/statystyki - samą wypłatę (np. BLIK)
#   przekazujecie ręcznie tak jak ustalicie.
# ========================

partnerstwo_group = app_commands.Group(name="partnerstwo", description="Program partnerski (realizatorzy)")


def partner_wpis(user_id: int) -> dict:
    dane = CONFIG["partnerstwo_dane"]
    klucz = str(user_id)
    if klucz not in dane:
        dane[klucz] = {"liczba": 0, "zarobek": 0.0}
    return dane[klucz]


class ZostanRealizatoremView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Kliknij, aby zostać realizatorem partnerstw!", style=discord.ButtonStyle.primary,
                        emoji="🔄", custom_id="shopbot:realizator")
    async def zostan(self, interaction: discord.Interaction, button: discord.ui.Button):
        rola_id = CONFIG["roles"].get("realizator")
        rola = interaction.guild.get_role(rola_id) if rola_id else None
        if not rola:
            await interaction.response.send_message(
                "⚠️ Rola realizatora nie jest jeszcze ustawiona. Napisz do administracji.", ephemeral=True)
            return
        if rola in interaction.user.roles:
            await interaction.response.send_message("✅ Jesteś już realizatorem partnerstw!", ephemeral=True)
            return
        await interaction.user.add_roles(rola, reason="Dołączenie do programu partnerskiego")
        await interaction.response.send_message(
            f"✅ Zostałeś/aś realizatorem partnerstw! Stawka: **{CONFIG['partnerstwo_stawka']} {CONFIG['partnerstwo_waluta']}** "
            f"za partnerstwo. Zgłaszaj nawiązane partnerstwa komendą `/partnerstwo zglos`.", ephemeral=True)


async def wyslij_panel_realizatora(kanal: discord.TextChannel):
    embed = base_embed("akcent", title=render(CONFIG["zostan_realizatorem_tytul"]),
                        description=render(CONFIG["zostan_realizatorem_opis"],
                                            stawka=CONFIG["partnerstwo_stawka"],
                                            waluta=CONFIG["partnerstwo_waluta"]))
    plik = prepare_embed_image(embed, "partnerstwo")
    set_footer(embed, kanal.guild)
    await send_or_edit_panel(kanal, embed, ZostanRealizatoremView(), "realizator", plik)


@partnerstwo_group.command(name="zglos", description="Zgłasza nawiązane partnerstwo z innym serwerem")
@app_commands.describe(partner="Osoba/serwer, z którym nawiązano partnerstwo (opis lub wzmianka)")
async def partnerstwo_zglos(interaction: discord.Interaction, partner: str):
    rola_id = CONFIG["roles"].get("realizator")
    rola = interaction.guild.get_role(rola_id) if rola_id else None
    if rola and rola not in interaction.user.roles and not is_staff(interaction):
        await interaction.response.send_message("⚠️ Musisz być realizatorem, aby zgłaszać partnerstwa.", ephemeral=True)
        return

    stawka = CONFIG["partnerstwo_stawka"]
    wpis = partner_wpis(interaction.user.id)
    wpis["liczba"] += 1
    wpis["zarobek"] = round(wpis["zarobek"] + stawka, 2)
    save_config()

    embed = base_embed("sukces", title="🔄 Nawiązano Nowe Partnerstwo!")
    embed.add_field(name="Kto nawiązał", value=interaction.user.mention, inline=False)
    embed.add_field(name="Kto został partnerem", value=partner, inline=False)
    embed.add_field(name="Nawiązał łącznie partnerstw", value=str(wpis["liczba"]))
    embed.add_field(name="Łącznie zarobił", value=f"{wpis['zarobek']} {CONFIG['partnerstwo_waluta']}")
    set_footer(embed, interaction.guild)

    kanal_id = CONFIG["channels"].get("partnerstwa")
    kanal = interaction.guild.get_channel(kanal_id) if kanal_id else interaction.channel
    await kanal.send(embed=embed)
    if kanal.id != interaction.channel.id:
        await interaction.response.send_message(f"✅ Zgłoszono partnerstwo na {kanal.mention}.", ephemeral=True)
    else:
        await interaction.response.send_message("✅ Zgłoszono partnerstwo.", ephemeral=True)


@partnerstwo_group.command(name="statystyki", description="Pokazuje Twoje statystyki w programie partnerskim")
async def partnerstwo_statystyki(interaction: discord.Interaction):
    wpis = partner_wpis(interaction.user.id)
    embed = base_embed("akcent", title="💎 Twoje statystyki partnerskie")
    embed.add_field(name="Nawiązane partnerstwa", value=str(wpis["liczba"]))
    embed.add_field(name="Łączny zarobek", value=f"{wpis['zarobek']} {CONFIG['partnerstwo_waluta']}")
    embed.add_field(name="Aktualna stawka", value=f"{CONFIG['partnerstwo_stawka']} {CONFIG['partnerstwo_waluta']}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@partnerstwo_group.command(name="ranking", description="Pokazuje ranking najlepszych realizatorów")
async def partnerstwo_ranking(interaction: discord.Interaction):
    dane = CONFIG["partnerstwo_dane"]
    if not dane:
        await interaction.response.send_message("📋 Nikt jeszcze nie zgłosił partnerstwa.", ephemeral=True)
        return
    posortowane = sorted(dane.items(), key=lambda kv: kv[1]["zarobek"], reverse=True)[:10]
    linie = []
    for i, (user_id, wpis) in enumerate(posortowane, start=1):
        linie.append(f"**{i}.** <@{user_id}> — {wpis['liczba']} partnerstw, {wpis['zarobek']} {CONFIG['partnerstwo_waluta']}")
    embed = base_embed("akcent", title="💎 Ranking realizatorów partnerstw", description="\n".join(linie))
    await interaction.response.send_message(embed=embed)


@partnerstwo_group.command(name="stawka", description="[Admin] Ustawia stawkę za jedno partnerstwo")
@app_commands.describe(kwota="Nowa kwota, np. 0.70")
async def partnerstwo_stawka_cmd(interaction: discord.Interaction, kwota: float):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Tylko administrator może zmienić stawkę.", ephemeral=True)
        return
    CONFIG["partnerstwo_stawka"] = round(kwota, 2)
    save_config()

    embed = base_embed("akcent", title="💎 Zmieniono Stawkę")
    embed.add_field(name="Nowa stawka", value=f"{kwota} {CONFIG['partnerstwo_waluta']}")
    embed.add_field(name="Zmieniona przez", value=interaction.user.mention)
    set_footer(embed, interaction.guild)
    kanal_id = CONFIG["channels"].get("partnerstwa")
    kanal = interaction.guild.get_channel(kanal_id) if kanal_id else interaction.channel
    await kanal.send(embed=embed)
    await interaction.response.send_message(f"✅ Ustawiono nową stawkę: {kwota} {CONFIG['partnerstwo_waluta']}.", ephemeral=True)


# ========================
#   POWITANIE NOWEJ OSOBY
# ========================

@bot.event
async def on_member_join(member: discord.Member):
    kanal_id = CONFIG["channels"].get("nowa_osoba")
    if not kanal_id:
        return
    kanal = member.guild.get_channel(kanal_id)
    if not kanal:
        return
    embed = base_embed("akcent", title=render(CONFIG["nowa_osoba_tytul"]),
                        description=render(CONFIG["nowa_osoba_tresc"], mention=member.mention,
                                            ilosc=str(member.guild.member_count)))
    plik = prepare_embed_image(embed, "nowa_osoba", thumb=True)
    set_footer(embed, member.guild)
    await kanal.send(embed=embed, file=plik)


# ========================
#   /konfiguracja  — centralne, edytowalne ustawienia (kolory, obrazki, kanały, role)
# ========================

konfiguracja_group = app_commands.Group(name="konfiguracja", description="Ustawienia bota (tylko administracja)")


@konfiguracja_group.command(name="nazwa", description="Ustawia nazwę sklepu używaną we wszystkich panelach")
@app_commands.describe(nazwa="Nowa nazwa, np. PixelShop")
async def konfig_nazwa(interaction: discord.Interaction, nazwa: str):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    CONFIG["nazwa_sklepu"] = nazwa
    save_config()
    await interaction.response.send_message(f"✅ Nazwa sklepu ustawiona na **{nazwa}**.", ephemeral=True)


@konfiguracja_group.command(name="kolor", description="Zmienia kolor paneli bota")
@app_commands.describe(typ="Który kolor zmieniamy", hex="Kolor w formacie HEX, np. #5865F2")
@app_commands.choices(typ=[
    app_commands.Choice(name="Akcent (główny)", value="akcent"),
    app_commands.Choice(name="Sukces", value="sukces"),
    app_commands.Choice(name="Błąd", value="blad"),
])
async def konfig_kolor(interaction: discord.Interaction, typ: app_commands.Choice[str], hex: str):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    try:
        hex_to_color(hex)
    except ValueError:
        await interaction.response.send_message("⚠️ Zły format koloru. Użyj np. `#5865F2`.", ephemeral=True)
        return
    CONFIG["colors"][typ.value] = hex
    save_config()
    await interaction.response.send_message(f"✅ Kolor **{typ.name}** ustawiony na `{hex}`.", ephemeral=True)


@konfiguracja_group.command(name="obrazek", description="Ustawia obrazek/banner dla danego panelu")
@app_commands.describe(panel="Który panel", plik="Obrazek do przesłania")
@app_commands.choices(panel=[
    app_commands.Choice(name="Weryfikacja", value="weryfikacja"),
    app_commands.Choice(name="Regulamin", value="regulamin"),
    app_commands.Choice(name="Panel ticketów", value="ticket_panel"),
    app_commands.Choice(name="Opinie", value="opinie"),
    app_commands.Choice(name="Partnerstwo", value="partnerstwo"),
    app_commands.Choice(name="Nowa osoba", value="nowa_osoba"),
])
async def konfig_obrazek(interaction: discord.Interaction, panel: app_commands.Choice[str], plik: discord.Attachment):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    sciezka = os.path.join(IMAGES_DIR, f"{panel.value}_{plik.filename}")
    await plik.save(sciezka)
    CONFIG["images"][panel.value] = sciezka
    save_config()
    await interaction.response.send_message(
        f"✅ Obrazek dla panelu **{panel.name}** zapisany. Użyj `/panel wyslij` z tym panelem, aby odświeżyć.",
        ephemeral=True)


@konfiguracja_group.command(name="rola", description="Ustawia rolę używaną przez bota")
@app_commands.describe(typ="Która rola", rola="Rola z serwera")
@app_commands.choices(typ=[
    app_commands.Choice(name="Zweryfikowany", value="zweryfikowany"),
    app_commands.Choice(name="Staff", value="staff"),
    app_commands.Choice(name="Realizator partnerstw", value="realizator"),
])
async def konfig_rola(interaction: discord.Interaction, typ: app_commands.Choice[str], rola: discord.Role):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    CONFIG["roles"][typ.value] = rola.id
    save_config()
    await interaction.response.send_message(f"✅ Rola **{typ.name}** ustawiona na {rola.mention}.", ephemeral=True)


@konfiguracja_group.command(name="kanal", description="Ustawia kanał używany przez bota")
@app_commands.describe(typ="Który kanał", kanal="Kanał z serwera")
@app_commands.choices(typ=[
    app_commands.Choice(name="Weryfikacja", value="weryfikacja"),
    app_commands.Choice(name="Panel ticketów", value="ticket_panel"),
    app_commands.Choice(name="Opinie", value="opinie"),
    app_commands.Choice(name="Partnerstwa", value="partnerstwa"),
    app_commands.Choice(name="Blacklista", value="blacklista"),
    app_commands.Choice(name="Powitania (nowa osoba)", value="nowa_osoba"),
])
async def konfig_kanal(interaction: discord.Interaction, typ: app_commands.Choice[str], kanal: discord.TextChannel):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    CONFIG["channels"][typ.value] = kanal.id
    save_config()
    await interaction.response.send_message(f"✅ Kanał **{typ.name}** ustawiony na {kanal.mention}.", ephemeral=True)


@konfiguracja_group.command(name="kategoria_ticketow", description="Ustawia kategorię, w której tworzone są tickety")
@app_commands.describe(kategoria="Kategoria kanałów")
async def konfig_kategoria(interaction: discord.Interaction, kategoria: discord.CategoryChannel):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    CONFIG["ticket_category_id"] = kategoria.id
    save_config()
    await interaction.response.send_message(f"✅ Kategoria ticketów ustawiona na **{kategoria.name}**.", ephemeral=True)


@konfiguracja_group.command(name="podglad", description="Pokazuje aktualną konfigurację bota")
async def konfig_podglad(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    g = interaction.guild
    embed = base_embed("akcent", title="💎 Aktualna konfiguracja")
    embed.add_field(name="Nazwa sklepu", value=CONFIG["nazwa_sklepu"], inline=False)
    embed.add_field(name="Kolory", value="\n".join(f"{k}: `{v}`" for k, v in CONFIG["colors"].items()), inline=True)
    role_txt = "\n".join(f"{k}: {(g.get_role(v).mention if v and g.get_role(v) else '—')}" for k, v in CONFIG["roles"].items())
    embed.add_field(name="Role", value=role_txt or "—", inline=True)
    kanal_txt = "\n".join(f"{k}: {(g.get_channel(v).mention if v and g.get_channel(v) else '—')}" for k, v in CONFIG["channels"].items())
    embed.add_field(name="Kanały", value=kanal_txt or "—", inline=False)
    embed.add_field(name="Stawka partnerstwa", value=f"{CONFIG['partnerstwo_stawka']} {CONFIG['partnerstwo_waluta']}", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ========================
#   /regulamin  — zarządzanie stronami regulaminu
# ========================

regulamin_group = app_commands.Group(name="regulamin", description="Zarządzanie regulaminem")


@regulamin_group.command(name="dodaj_strone", description="Dodaje nową stronę regulaminu")
async def regulamin_dodaj(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    await interaction.response.send_modal(DodajStroneRegulaminuModal())


@regulamin_group.command(name="edytuj_strone", description="Edytuje istniejącą stronę regulaminu")
@app_commands.describe(numer="Numer strony (1, 2, 3...)")
async def regulamin_edytuj(interaction: discord.Interaction, numer: int):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    strony = CONFIG["regulamin_strony"]
    if numer < 1 or numer > len(strony):
        await interaction.response.send_message(f"⚠️ Regulamin ma tylko {len(strony)} stron.", ephemeral=True)
        return
    await interaction.response.send_modal(EdytujStroneRegulaminuModal(numer - 1))


@regulamin_group.command(name="usun_strone", description="Usuwa stronę regulaminu")
@app_commands.describe(numer="Numer strony (1, 2, 3...)")
async def regulamin_usun(interaction: discord.Interaction, numer: int):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    strony = CONFIG["regulamin_strony"]
    if numer < 1 or numer > len(strony):
        await interaction.response.send_message(f"⚠️ Regulamin ma tylko {len(strony)} stron.", ephemeral=True)
        return
    usunieta = strony.pop(numer - 1)
    save_config()
    await interaction.response.send_message(f"✅ Usunięto stronę **{usunieta['tytul']}**.", ephemeral=True)


@regulamin_group.command(name="wyslij", description="Wysyła / odświeża panel regulaminu na wskazanym kanale")
@app_commands.describe(kanal="Kanał, na który wysłać panel")
async def regulamin_wyslij(interaction: discord.Interaction, kanal: discord.TextChannel):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    await wyslij_panel_regulaminu(kanal)
    await interaction.response.send_message(f"✅ Panel regulaminu wysłany/odświeżony na {kanal.mention}.", ephemeral=True)


# ========================
#   /panel  — wysyłanie / odświeżanie pozostałych paneli
# ========================

panel_group = app_commands.Group(name="panel", description="Wysyłanie i odświeżanie paneli bota")


@panel_group.command(name="weryfikacja", description="Wysyła / odświeża panel weryfikacji")
async def panel_weryfikacja(interaction: discord.Interaction, kanal: discord.TextChannel):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    await wyslij_panel_weryfikacji(kanal)
    await interaction.response.send_message(f"✅ Panel weryfikacji wysłany/odświeżony na {kanal.mention}.", ephemeral=True)


@panel_group.command(name="tickety", description="Wysyła / odświeża panel ticketów")
async def panel_tickety(interaction: discord.Interaction, kanal: discord.TextChannel):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    await wyslij_panel_ticketow(kanal)
    await interaction.response.send_message(f"✅ Panel ticketów wysłany/odświeżony na {kanal.mention}.", ephemeral=True)


@panel_group.command(name="opinie", description="Wysyła / odświeża panel 'wystaw opinię'")
async def panel_opinie(interaction: discord.Interaction, kanal: discord.TextChannel):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    await wyslij_panel_opinii(kanal)
    await interaction.response.send_message(f"✅ Panel opinii wysłany/odświeżony na {kanal.mention}.", ephemeral=True)


@panel_group.command(name="realizator", description="Wysyła / odświeża panel 'zostań realizatorem'")
async def panel_realizator(interaction: discord.Interaction, kanal: discord.TextChannel):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Brak uprawnień.", ephemeral=True)
        return
    await wyslij_panel_realizatora(kanal)
    await interaction.response.send_message(f"✅ Panel realizatora wysłany/odświeżony na {kanal.mention}.", ephemeral=True)


# ========================
#   START BOTA
# ========================

bot.tree.add_command(konfiguracja_group)
bot.tree.add_command(regulamin_group)
bot.tree.add_command(panel_group)
bot.tree.add_command(blacklista_group)
bot.tree.add_command(partnerstwo_group)


@bot.event
async def on_ready():
    bot.add_view(WeryfikacjaView())
    bot.add_view(RegulaminView(0))
    bot.add_view(TicketPanelView())
    bot.add_view(ZamknijTicketView())
    bot.add_view(WystawOpinieView())
    bot.add_view(ZostanRealizatoremView())

    if TEST_GUILD_ID:
        guild_obj = discord.Object(id=TEST_GUILD_ID)
        bot.tree.copy_global_to(guild=guild_obj)
        await bot.tree.sync(guild=guild_obj)
    else:
        await bot.tree.sync()

    print(f"Zalogowano jako {bot.user} — bot gotowy.")


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Ustaw zmienną środowiskową DISCORD_TOKEN przed uruchomieniem bota.")
    bot.run(TOKEN)
