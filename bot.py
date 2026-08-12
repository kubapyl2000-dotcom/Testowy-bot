import os
import json
import random
import re
import datetime
from typing import Optional, List, Tuple

import discord
from discord.ext import commands, tasks
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
    "footer": "© {rok} {sklep}",

    "colors": {
        "akcent": "#5865F2",
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
        "konkurs": "",
    },

    "channels": {
        "weryfikacja": 0,
        "ticket_panel": 0,
        "opinie": 0,
        "partnerstwa": 0,
        "blacklista": 0,
        "nowa_osoba": 0,
        "konkursy": 0,
    },
    "roles": {
        "staff": 0,
        "zweryfikowany": 0,
        "realizator": 0,
    },
    "ticket_category_id": 0,

    "panel_messages": {},  # klucz -> {"channel_id":.., "message_id":..}

    # ---- Weryfikacja ----
    "weryfikacja_opis": (
        "» **Hej!** Naciśnij przycisk **poniżej**, żeby się zweryfikować! Dzięki temu uzyskasz pełny "
        "dostęp **do wszystkich** kanałów serwera.\n\n"
        "» pssst! Nie sprzedajemy cię jako membersa/**nie dodajemy** cię nigdzie!"
    ),

    # ---- Regulamin ----
    "regulamin_strony": [
        {"tytul": "1. Zasady ogólne", "tresc": (
            "1.1. Administracja może odmówić obsługi lub usunąć użytkownika, który łamie regulamin.\n"
            "1.2. Regulamin może zostać zmieniony w każdej chwili.\n"
            "1.3. Korzystając z serwera, akceptujesz ten regulamin.")},
        {"tytul": "2. Zakupy", "tresc": (
            "2.1. Wszystkie zakupy są ostateczne, chyba że wcześniej ustalono inaczej.\n"
            "2.2. Realizacja zamówienia trwa do 6 godzin.\n"
            "2.3. Dane użytkowników przetwarzamy tylko na potrzeby realizacji zamówienia.")},
        {"tytul": "3. Legit check i reklamacje", "tresc": (
            "3.1. Masz 24 godziny na dodanie legit checka po zakupie.\n"
            "3.2. Reklamacje przyjmujemy tylko przez system ticketów.\n"
            "3.3. Bez legit checka reklamacji nie rozpatrujemy.")},
        {"tytul": "4. Zachowanie na serwerze", "tresc": (
            "4.1. Podczas zakupów, reklamacji i pytań wymagana jest kultura i szacunek.\n"
            "4.2. Prowokacje, spam i trolling skutkują ostrzeżeniami lub banem.")},
    ],

    # ---- Panel ticketów ----
    "ticket_opis": (
        "» Chcesz zakupić produkt bądź potrzebujesz pomocy od administracji? Bądź Twój produkt wygasł "
        "i chcesz go wymienić? Lub coś innego?\n\n"
        "» Skorzystaj z menu **poniżej** i wybierz odpowiednią kategorię, a my zajmiemy się resztą!"
    ),
    "ticket_kategorie": {
        "kupic": {"etykieta": "🛒 Chcę zakupić produkt", "opis": "Kliknij, aby zakupić produkt!"},
        "partnerstwo": {"etykieta": "🤝 Chcę nawiązać partnerstwo", "opis": "Kliknij, jeśli chcesz nawiązać partnerstwo!"},
        "middleman": {"etykieta": "🎥 Middleman", "opis": "Kliknij, jeśli potrzebujesz mm do transakcji!"},
        "pomoc": {"etykieta": "ℹ️ Potrzebuję pomocy", "opis": "Kliknij, jeśli masz pytanie lub problem!"},
        "reklamacja": {"etykieta": "⚙️ Chcę złożyć reklamację", "opis": "Kliknij, aby złożyć reklamację!"},
    },
    "ticket_wiadomosc_tresc": "Witaj na swoim zgłoszeniu, {mention}! Poczekaj cierpliwie na {rola}.",

    # ---- Nowa osoba ----
    "nowa_osoba_tresc": (
        "» **Hejka {mention}!** Miło Cię u nas widzieć!\n"
        "» Jest nam mega miło, że wpadłeś. Rozgość się.\n\n"
        "📌 Przypominamy, że nieprzestrzeganie regulaminu może wiązać się z konsekwencjami.\n\n"
        "Dzięki, że wbiłeś! Jesteś naszym **{ilosc}** użytkownikiem."
    ),

    # ---- Program partnerski ----
    "partnerstwo_stawka": 0.70,
    "partnerstwo_waluta": "PLN",
    "partnerstwo_dane": {},
    "zostan_realizatorem_opis": (
        "» Chcesz **zarobić** w pełni **legalną** i szybką kaskę? Wystarczy **realizować partnerstwa** "
        "na naszym serwerze!\n\n"
        "» Kliknij w przycisk **poniżej**, aby zostać realizatorem partnerstw!\n\n"
        "Stawka za jedno partnerstwo: **{stawka} {waluta}**."
    ),

    # ---- Blacklista ----
    "blacklista_dane": {},

    # ---- Konkursy (giveaway'e) ----
    "konkursy": {},          # id -> dane konkursu
    "konkurs_licznik": 0,    # licznik do generowania kolejnych ID konkursów

    # ---- Opinie ----
    "opinie_opis": (
        "» Wystawiając nam opinię dajesz innym znać, co Cię u nas zadowoliło.\n"
        "» Będziemy super wdzięczni za każdą wystawioną opinię - to buduje zaufanie do naszego sklepu.\n"
        "» Opinię możesz napisać klikając w przycisk **poniżej**."
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


_SMALL_CAPS = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘqʀꜱᴛᴜᴠᴡxʏᴢ",
)


def small_caps(text: str) -> str:
    """Efekt wizualny 'small caps' w nagłówkach paneli, tak jak w oryginalnym stylu."""
    return text.lower().translate(_SMALL_CAPS)


def header_text(sekcja: str) -> discord.ui.TextDisplay:
    """Duży, wytłuszczony nagłówek panelu (Markdown heading), tak jak w oryginalnym stylu."""
    nazwa = CONFIG.get("nazwa_sklepu", "Shop").upper()
    etykieta = f"## 💎 {nazwa} X {sekcja.upper()}"
    return discord.ui.TextDisplay(etykieta)


def cytuj(tekst: str) -> str:
    """Dodaje formatowanie cytatu (szara pionowa kreska obok każdej linijki) - dokładnie tak
    jak w oryginalnym stylu. Puste linie zostają puste, żeby oddzielać osobne bloki/kreski."""
    linie = []
    for linia in tekst.split("\n"):
        linie.append(f"> {linia}" if linia.strip() else "")
    return "\n".join(linie)


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


def footer_line(sekcja: str) -> str:
    return f"-# © {datetime.datetime.now().year} {render('{sklep}')} x {sekcja}"


def image_file_and_url(typ: str) -> Tuple[Optional[discord.File], Optional[str]]:
    sciezka = CONFIG["images"].get(typ)
    if not sciezka or not os.path.exists(sciezka):
        return None, None
    nazwa = os.path.basename(sciezka)
    return discord.File(sciezka, filename=nazwa), f"attachment://{nazwa}"


class PanelView(discord.ui.LayoutView):
    """Generyczny budowniczy 'karty' w stylu Components V2 - dokładnie taki wygląd (ramka,
    nagłówek-pigułka, treść, przyciski/select w tej samej ramce, stopka) jak na oryginalnych screenach."""

    def __init__(self, sekcja: str, opis: str, typ_koloru: str = "akcent",
                 items: Optional[List[discord.ui.Item]] = None, obrazek_typ: Optional[str] = None,
                 miniaturka: bool = False):
        super().__init__(timeout=None)
        self.plik: Optional[discord.File] = None

        opis_cytowany = cytuj(opis)
        dzieci: List[discord.ui.Item] = [header_text(sekcja)]
        dzieci.append(discord.ui.Separator())
        dzieci.append(discord.ui.TextDisplay(opis_cytowany))

        if obrazek_typ:
            plik, url = image_file_and_url(obrazek_typ)
            if url:
                self.plik = plik
                if miniaturka:
                    # doczepiamy miniaturkę do bloku treści zamiast osobnej sekcji
                    dzieci[-1] = discord.ui.Section(opis_cytowany, accessory=discord.ui.Thumbnail(media=url))
                else:
                    dzieci.append(discord.ui.Separator())
                    dzieci.append(discord.ui.MediaGallery(discord.MediaGalleryItem(url)))

        if items:
            dzieci.append(discord.ui.Separator())
            dzieci.append(discord.ui.ActionRow(*items))

        dzieci.append(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        dzieci.append(discord.ui.TextDisplay(footer_line(sekcja)))

        self.container = discord.ui.Container(*dzieci, accent_color=get_color(typ_koloru))
        self.add_item(self.container)


async def send_or_edit_panel(target: discord.TextChannel, view: PanelView, klucz: str):
    """Wysyła panel na kanał, albo edytuje wcześniej wysłaną wiadomość (ten sam klucz + kanał),
    żeby zmiana treści w configu nie tworzyła duplikatów paneli."""
    info = CONFIG["panel_messages"].setdefault(klucz, {"channel_id": 0, "message_id": 0})
    if info["channel_id"] == target.id and info["message_id"]:
        try:
            msg = await target.fetch_message(info["message_id"])
            if view.plik:
                await msg.edit(view=view, attachments=[view.plik])
            else:
                await msg.edit(view=view)
            return msg
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass
    if view.plik:
        msg = await target.send(view=view, file=view.plik)
    else:
        msg = await target.send(view=view)
    info["channel_id"] = target.id
    info["message_id"] = msg.id
    save_config()
    return msg


async def send_dynamic_card(target: discord.abc.Messageable, sekcja: str, opis: str, typ_koloru: str = "akcent",
                             obrazek_typ: Optional[str] = None, miniaturka: bool = False,
                             ekstra_reakcja: Optional[str] = None):
    """Jednorazowa karta (np. ogłoszenie opinii/blacklisty/partnerstwa) w tym samym stylu co panele."""
    view = PanelView(sekcja, opis, typ_koloru, items=None, obrazek_typ=obrazek_typ, miniaturka=miniaturka)
    if view.plik:
        wiadomosc = await target.send(view=view, file=view.plik)
    else:
        wiadomosc = await target.send(view=view)
    if ekstra_reakcja:
        try:
            await wiadomosc.add_reaction(ekstra_reakcja)
        except discord.HTTPException:
            pass
    return wiadomosc


# ========================
#   INICJALIZACJA BOTA
# ========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


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

class WeryfikacjaButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Kliknij, aby zweryfikować się na naszym serwerze!",
                          style=discord.ButtonStyle.success, emoji="✅", custom_id="shopbot:weryfikacja")

    async def callback(self, interaction: discord.Interaction):
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


def build_weryfikacja_panel() -> PanelView:
    return PanelView("Weryfikacja", render(CONFIG["weryfikacja_opis"]), items=[WeryfikacjaButton()],
                      obrazek_typ="weryfikacja", miniaturka=True)


async def wyslij_panel_weryfikacji(kanal: discord.TextChannel):
    await send_or_edit_panel(kanal, build_weryfikacja_panel(), "weryfikacja")


# ========================
#   REGULAMIN (panel wielostronicowy z Poprzednia/Nastepna)
# ========================

class RegulaminNawigacja(discord.ui.LayoutView):
    def __init__(self, strona: int = 0):
        super().__init__(timeout=None)
        self.strona = strona
        self.plik = None
        strony = CONFIG["regulamin_strony"]
        strona_dane = strony[strona]

        nazwa = CONFIG.get("nazwa_sklepu", "Shop").upper()
        etykieta_naglowka = f"## 💎 REGULAMIN {nazwa} - STRONA {strona + 1}/{len(strony)}"
        naglowek = discord.ui.TextDisplay(etykieta_naglowka)
        tresc = cytuj(f"**{strona_dane['tytul']}**\n\n{strona_dane['tresc']}")

        poprzednia = discord.ui.Button(label="← Poprzednia", style=discord.ButtonStyle.secondary,
                                        custom_id="shopbot:regulamin:prev", disabled=(strona <= 0))
        nastepna = discord.ui.Button(label="Następna →", style=discord.ButtonStyle.secondary,
                                      custom_id="shopbot:regulamin:next", disabled=(strona >= len(strony) - 1))
        poprzednia.callback = self._callback_factory(-1)
        nastepna.callback = self._callback_factory(1)

        dzieci = [naglowek, discord.ui.Separator(), discord.ui.TextDisplay(tresc),
                  discord.ui.Separator(), discord.ui.ActionRow(poprzednia, nastepna),
                  discord.ui.Separator(spacing=discord.SeparatorSpacing.small),
                  discord.ui.TextDisplay(footer_line("Regulamin"))]
        self.container = discord.ui.Container(*dzieci, accent_color=get_color("akcent"))
        self.add_item(self.container)

    def _callback_factory(self, kierunek: int):
        async def callback(interaction: discord.Interaction):
            strony = CONFIG["regulamin_strony"]
            nowa_strona = max(0, min(len(strony) - 1, self.strona + kierunek))
            await interaction.response.edit_message(view=RegulaminNawigacja(nowa_strona))
        return callback


async def wyslij_panel_regulaminu(kanal: discord.TextChannel):
    await send_or_edit_panel(kanal, RegulaminNawigacja(0), "regulamin")


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

class ZamknijTicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Zamknij ticket", style=discord.ButtonStyle.danger, emoji="🔒",
                          custom_id="shopbot:ticket:zamknij")

    async def callback(self, interaction: discord.Interaction):
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


def build_ticket_wiadomosc(mention: str, rola_mention: str) -> PanelView:
    tresc = render(CONFIG["ticket_wiadomosc_tresc"], mention=mention, rola=rola_mention)
    return PanelView("Ticket", tresc, items=[ZamknijTicketButton()])


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

        view = build_ticket_wiadomosc(interaction.user.mention, staff_rola.mention if staff_rola else "administracją")
        await kanal.send(content=f"{interaction.user.mention}" + (f" {staff_rola.mention}" if staff_rola else ""),
                          view=view)

        await interaction.response.send_message(f"✅ Utworzono Twój ticket: {kanal.mention}", ephemeral=True)


class TicketPanelWidok(PanelView):
    def __init__(self):
        super().__init__("Tickety", render(CONFIG["ticket_opis"]), items=[TicketKategoriaSelect()],
                          obrazek_typ="ticket_panel")


async def wyslij_panel_ticketow(kanal: discord.TextChannel):
    await send_or_edit_panel(kanal, TicketPanelWidok(), "ticket_panel")


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

        tresc = (
            f"» **Twórca opinii:** {interaction.user.mention}\n"
            f"» **Treść:** {self.tresc}\n"
            f"» **Co możemy poprawić?** {self.poprawa}\n\n"
            f"🛒 **Jakość produktu:** {gwiazdki(str(self.produkt))}\n"
            f"🏛️ **Czas realizacji:** {gwiazdki(str(self.czas))}\n"
            f"⏱️ **Przebieg transakcji:** {gwiazdki(str(self.przebieg))}"
        )
        await send_dynamic_card(kanal, "Opinia", tresc, "akcent", ekstra_reakcja="❤️")
        await interaction.response.send_message(f"✅ Dziękujemy za opinię! Widać ją na {kanal.mention}.", ephemeral=True)


class WystawOpinieButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Kliknij, aby wystawić opinię!", style=discord.ButtonStyle.primary, emoji="✍️",
                          custom_id="shopbot:opinia")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(OpiniaModal())


class WystawOpiniePanel(PanelView):
    def __init__(self):
        super().__init__("Wystaw Opinię", render(CONFIG["opinie_opis"]), items=[WystawOpinieButton()])


async def wyslij_panel_opinii(kanal: discord.TextChannel):
    await send_or_edit_panel(kanal, WystawOpiniePanel(), "opinie")


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
        "nick": nick, "powod": powod,
        "data": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        "dodal": interaction.user.id,
    }
    save_config()

    tresc = (f"» **Użytkownik:** {nick}\n» **Data dodania:** {CONFIG['blacklista_dane'][klucz]['data']}\n"
              f"» **Powód:** {powod}\n» **Dodane przez:** {interaction.user.mention}")

    kanal_id = CONFIG["channels"].get("blacklista")
    kanal = interaction.guild.get_channel(kanal_id) if kanal_id else interaction.channel
    await send_dynamic_card(kanal, "Blacklista", tresc, "blad")
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
    tresc = f"» **Użytkownik:** {wpis['nick']}\n» **Powód:** {wpis['powod']}\n» **Data dodania:** {wpis['data']}"
    view = PanelView("Wpis Na Blackliście", tresc, "blad")
    await interaction.response.send_message(view=view, ephemeral=True)


@blacklista_group.command(name="lista", description="Wyświetla całą blacklistę")
async def blacklista_lista(interaction: discord.Interaction):
    dane = CONFIG["blacklista_dane"]
    if not dane:
        await interaction.response.send_message("📋 Blacklista jest obecnie pusta.", ephemeral=True)
        return
    linie = [f"• **{wpis['nick']}** — {wpis['powod']} ({wpis['data']})" for wpis in dane.values()]
    view = PanelView("Blacklista — Pełna Lista", "\n".join(linie)[:3900], "akcent")
    await interaction.response.send_message(view=view, ephemeral=True)


# ========================
#   KONKURSY (GIVEAWAY'E)
# ========================

DLUGOSC_JEDNOSTKI = {"d": "days", "h": "hours", "m": "minutes", "s": "seconds"}
WZORZEC_CZASU = re.compile(r"(\d+)\s*(d|h|m|s)", re.IGNORECASE)


def parsuj_czas(tekst: str) -> Optional[datetime.timedelta]:
    """Parsuje czas trwania konkursu, np. '1d12h', '30m', '2h30m' -> timedelta."""
    dopasowania = WZORZEC_CZASU.findall(tekst.strip())
    if not dopasowania:
        return None
    wartosci = {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}
    for liczba, jednostka in dopasowania:
        wartosci[DLUGOSC_JEDNOSTKI[jednostka.lower()]] += int(liczba)
    delta = datetime.timedelta(**wartosci)
    return delta if delta.total_seconds() > 0 else None


def nowy_id_konkursu() -> str:
    CONFIG["konkurs_licznik"] = CONFIG.get("konkurs_licznik", 0) + 1
    save_config()
    return str(CONFIG["konkurs_licznik"])


def konkurs_wpis(konkurs_id: str) -> Optional[dict]:
    return CONFIG["konkursy"].get(konkurs_id)


def forma_osob(ilosc: int) -> str:
    if ilosc == 1:
        return "osoba"
    if 2 <= ilosc % 10 <= 4 and not (12 <= ilosc % 100 <= 14):
        return "osoby"
    return "osób"


class DolaczKonkursButton(discord.ui.Button):
    def __init__(self, konkurs_id: str, disabled: bool = False):
        super().__init__(label="Kliknij, aby dołączyć do konkursu!", style=discord.ButtonStyle.success,
                          emoji="🎉", custom_id=f"shopbot:konkurs:dolacz:{konkurs_id}", disabled=disabled)
        self.konkurs_id = konkurs_id

    async def callback(self, interaction: discord.Interaction):
        wpis = konkurs_wpis(self.konkurs_id)
        if not wpis or wpis.get("zakonczony"):
            await interaction.response.send_message("⚠️ Ten konkurs już się zakończył.", ephemeral=True)
            return

        rola_id = wpis.get("wymagana_rola")
        if rola_id:
            rola = interaction.guild.get_role(rola_id)
            if rola and rola not in interaction.user.roles:
                await interaction.response.send_message(
                    f"⚠️ Aby dołączyć do tego konkursu, musisz posiadać rolę {rola.mention}.", ephemeral=True)
                return

        uczestnicy = wpis.setdefault("uczestnicy", [])
        if interaction.user.id in uczestnicy:
            uczestnicy.remove(interaction.user.id)
            save_config()
            await interaction.response.send_message("↩️ Zrezygnowałeś/aś z udziału w konkursie.", ephemeral=True)
        else:
            uczestnicy.append(interaction.user.id)
            save_config()
            await interaction.response.send_message("🎉 Dołączono do konkursu! Powodzenia!", ephemeral=True)

        try:
            kanal = interaction.guild.get_channel(wpis["kanal_id"])
            wiadomosc = await kanal.fetch_message(wpis["message_id"])
            await wiadomosc.edit(view=build_konkurs_panel(self.konkurs_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException, AttributeError):
            pass


class UczestnicyKonkursButton(discord.ui.Button):
    """Nieklikalny przycisk-licznik pokazujący liczbę uczestników (tak jak w oryginalnym stylu)."""

    def __init__(self, konkurs_id: str, ilosc: int):
        super().__init__(label=f"W konkursie wzięło udział {ilosc} {forma_osob(ilosc)}!",
                          style=discord.ButtonStyle.secondary, emoji="👥",
                          custom_id=f"shopbot:konkurs:licznik:{konkurs_id}", disabled=True)


def build_konkurs_panel(konkurs_id: str) -> PanelView:
    wpis = konkurs_wpis(konkurs_id)
    ilosc_uczestnikow = len(wpis.get("uczestnicy", []))
    koniec_ts = int(wpis["koniec"])
    zakonczony = wpis.get("zakonczony", False)

    linie = [
        f"🎁 **Nagrodą w konkursie jest:** `{wpis['nagroda']}`",
        f"👤 **Nagrodę może wygrać:** `{wpis['ilosc_zwyciezcow']} {forma_osob(wpis['ilosc_zwyciezcow'])}`",
    ]
    if zakonczony:
        linie.append(f"🏛️ **Zakończono:** <t:{koniec_ts}:R> (<t:{koniec_ts}:F>)")
    else:
        linie.append(f"🏛️ **Koniec:** <t:{koniec_ts}:R> (<t:{koniec_ts}:F>)")
    if wpis.get("wymagania"):
        linie.append(f"» **Wymagania:** `{wpis['wymagania']}`")
    if wpis.get("wymagana_rola"):
        linie.append(f"🔒 **Wymagana rola:** <@&{wpis['wymagana_rola']}>")
    linie.append(f"🧑‍🎤 **Organizator:** <@{wpis['host_id']}>")

    if zakonczony:
        zwyciezcy = wpis.get("zwyciezcy", [])
        if zwyciezcy:
            wzmianki = ", ".join(f"<@{uid}>" for uid in zwyciezcy)
            linie.append(f"\n🏆 **Zwycięzca(y):** {wzmianki}")
        else:
            linie.append("\n🏆 **Zwycięzcy:** Brak (za mało uczestników).")

    opis = "\n".join(linie)

    dolacz = DolaczKonkursButton(konkurs_id, disabled=zakonczony)
    licznik = UczestnicyKonkursButton(konkurs_id, ilosc_uczestnikow)

    return PanelView("Konkurs", opis, "sukces" if not zakonczony else "akcent",
                      items=[dolacz, licznik], obrazek_typ="konkurs")


async def wylosuj_zwyciezcow(wpis: dict) -> List[int]:
    uczestnicy = list(wpis.get("uczestnicy", []))
    ile = min(wpis.get("ilosc_zwyciezcow", 1), len(uczestnicy))
    if ile <= 0:
        return []
    return random.sample(uczestnicy, ile)


async def zakoncz_konkurs(bot_instance: commands.Bot, konkurs_id: str, reroll: bool = False):
    """Kończy konkurs (lub losuje ponownie) — edytuje wiadomość i ogłasza zwycięzców na kanale."""
    wpis = konkurs_wpis(konkurs_id)
    if not wpis:
        return None

    zwyciezcy = await wylosuj_zwyciezcow(wpis)
    wpis["zwyciezcy"] = zwyciezcy
    wpis["zakonczony"] = True
    save_config()

    kanal = bot_instance.get_channel(wpis["kanal_id"])
    if kanal:
        try:
            wiadomosc = await kanal.fetch_message(wpis["message_id"])
            await wiadomosc.edit(view=build_konkurs_panel(konkurs_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

        if zwyciezcy:
            wzmianki = ", ".join(f"<@{uid}>" for uid in zwyciezcy)
            naglowek = "🔄 Wylosowano ponownie" if reroll else "🎊 Konkurs zakończony"
            tresc = (f"» **{naglowek}!** Gratulacje {wzmianki} — wygrywasz(cie) **{wpis['nagroda']}**!\n"
                      f"» Skontaktuj się z organizatorem <@{wpis['host_id']}>, aby odebrać nagrodę.")
            await send_dynamic_card(kanal, "Konkurs — Wyniki", tresc, "sukces")
        else:
            await send_dynamic_card(kanal, "Konkurs — Wyniki",
                                     f"» Konkurs na **{wpis['nagroda']}** zakończył się bez zwycięzców "
                                     f"— za mało uczestników.", "blad")
    return zwyciezcy


@tasks.loop(seconds=30)
async def sprawdzaj_konkursy():
    teraz = datetime.datetime.now(datetime.timezone.utc).timestamp()
    for konkurs_id, wpis in list(CONFIG["konkursy"].items()):
        if not wpis.get("zakonczony") and wpis.get("koniec", 0) <= teraz:
            await zakoncz_konkurs(bot, konkurs_id)


konkurs_group = app_commands.Group(name="konkurs", description="Zarządzanie konkursami (giveaway'ami)")


@konkurs_group.command(name="stworz", description="Tworzy nowy konkurs")
@app_commands.describe(
    nagroda="Co można wygrać, np. Nitro Boost",
    zwyciezcy="Ile osób wygra konkurs",
    czas="Czas trwania, np. 1d, 12h, 30m, 1d12h",
    kanal="Kanał, na który wysłać konkurs (domyślnie ustawiony w /konfiguracja kanal)",
    wymagania="Opcjonalny opis wymagań (informacyjny), np. 'zaproś 1 osobę'",
    wymagana_rola="Opcjonalna rola wymagana, aby dołączyć",
)
async def konkurs_stworz(interaction: discord.Interaction, nagroda: str, zwyciezcy: int, czas: str,
                          kanal: Optional[discord.TextChannel] = None, wymagania: Optional[str] = None,
                          wymagana_rola: Optional[discord.Role] = None):
    if not is_staff(interaction):
        await interaction.response.send_message("⚠️ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return
    if zwyciezcy < 1:
        await interaction.response.send_message("⚠️ Liczba zwycięzców musi wynosić co najmniej 1.", ephemeral=True)
        return

    delta = parsuj_czas(czas)
    if not delta:
        await interaction.response.send_message(
            "⚠️ Zły format czasu. Użyj np. `1d`, `12h`, `30m`, `1d12h30m`.", ephemeral=True)
        return

    docelowy_kanal = kanal
    if docelowy_kanal is None:
        kanal_id = CONFIG["channels"].get("konkursy")
        docelowy_kanal = interaction.guild.get_channel(kanal_id) if kanal_id else interaction.channel
    if docelowy_kanal is None:
        await interaction.response.send_message("⚠️ Nie udało się ustalić kanału konkursu.", ephemeral=True)
        return

    koniec = datetime.datetime.now(datetime.timezone.utc) + delta
    konkurs_id = nowy_id_konkursu()

    CONFIG["konkursy"][konkurs_id] = {
        "nagroda": nagroda,
        "ilosc_zwyciezcow": zwyciezcy,
        "koniec": koniec.timestamp(),
        "wymagania": wymagania or "",
        "wymagana_rola": wymagana_rola.id if wymagana_rola else 0,
        "host_id": interaction.user.id,
        "kanal_id": docelowy_kanal.id,
        "message_id": 0,
        "uczestnicy": [],
        "zakonczony": False,
        "zwyciezcy": [],
    }
    save_config()

    view = build_konkurs_panel(konkurs_id)
    if view.plik:
        wiadomosc = await docelowy_kanal.send(view=view, file=view.plik)
    else:
        wiadomosc = await docelowy_kanal.send(view=view)

    CONFIG["konkursy"][konkurs_id]["message_id"] = wiadomosc.id
    save_config()
    bot.add_view(build_konkurs_panel(konkurs_id), message_id=wiadomosc.id)

    await interaction.response.send_message(
        f"✅ Utworzono konkurs **#{konkurs_id}** na {docelowy_kanal.mention}.", ephemeral=True)


@konkurs_group.command(name="zakoncz", description="Kończy konkurs przed czasem i losuje zwycięzców")
@app_commands.describe(id="ID konkursu (widoczne w /konkurs lista)")
async def konkurs_zakoncz(interaction: discord.Interaction, id: str):
    if not is_staff(interaction):
        await interaction.response.send_message("⚠️ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return
    wpis = konkurs_wpis(id)
    if not wpis:
        await interaction.response.send_message("⚠️ Nie znaleziono konkursu o takim ID.", ephemeral=True)
        return
    if wpis.get("zakonczony"):
        await interaction.response.send_message("⚠️ Ten konkurs już się zakończył.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ Kończenie konkursu **#{id}**...", ephemeral=True)
    await zakoncz_konkurs(bot, id)


@konkurs_group.command(name="reroll", description="Losuje nowych zwycięzców zakończonego konkursu")
@app_commands.describe(id="ID konkursu (widoczne w /konkurs lista)")
async def konkurs_reroll(interaction: discord.Interaction, id: str):
    if not is_staff(interaction):
        await interaction.response.send_message("⚠️ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return
    wpis = konkurs_wpis(id)
    if not wpis:
        await interaction.response.send_message("⚠️ Nie znaleziono konkursu o takim ID.", ephemeral=True)
        return
    if not wpis.get("zakonczony"):
        await interaction.response.send_message("⚠️ Ten konkurs jeszcze się nie zakończył.", ephemeral=True)
        return
    await interaction.response.send_message(f"🔄 Losowanie ponowne konkursu **#{id}**...", ephemeral=True)
    await zakoncz_konkurs(bot, id, reroll=True)


@konkurs_group.command(name="usun", description="Usuwa konkurs bez losowania zwycięzców")
@app_commands.describe(id="ID konkursu (widoczne w /konkurs lista)")
async def konkurs_usun(interaction: discord.Interaction, id: str):
    if not is_staff(interaction):
        await interaction.response.send_message("⚠️ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return
    wpis = CONFIG["konkursy"].pop(id, None)
    if not wpis:
        await interaction.response.send_message("⚠️ Nie znaleziono konkursu o takim ID.", ephemeral=True)
        return
    save_config()
    try:
        kanal = interaction.guild.get_channel(wpis["kanal_id"])
        wiadomosc = await kanal.fetch_message(wpis["message_id"])
        await wiadomosc.delete()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException, AttributeError):
        pass
    await interaction.response.send_message(f"✅ Usunięto konkurs **#{id}**.", ephemeral=True)


@konkurs_group.command(name="lista", description="Wyświetla listę aktywnych konkursów")
async def konkurs_lista(interaction: discord.Interaction):
    aktywne = {k: v for k, v in CONFIG["konkursy"].items() if not v.get("zakonczony")}
    if not aktywne:
        await interaction.response.send_message("📋 Brak aktywnych konkursów.", ephemeral=True)
        return
    linie = []
    for konkurs_id, wpis in aktywne.items():
        linie.append(f"**#{konkurs_id}** — `{wpis['nagroda']}` — <t:{int(wpis['koniec'])}:R> — "
                      f"{len(wpis.get('uczestnicy', []))} {forma_osob(len(wpis.get('uczestnicy', [])))}")
    view = PanelView("Aktywne Konkursy", "\n".join(linie)[:3900], "akcent")
    await interaction.response.send_message(view=view, ephemeral=True)


# ========================
#   PROGRAM PARTNERSKI
# ========================

partnerstwo_group = app_commands.Group(name="partnerstwo", description="Program partnerski (realizatorzy)")


def partner_wpis(user_id: int) -> dict:
    dane = CONFIG["partnerstwo_dane"]
    klucz = str(user_id)
    if klucz not in dane:
        dane[klucz] = {"liczba": 0, "zarobek": 0.0}
    return dane[klucz]


class ZostanRealizatoremButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Kliknij, aby zostać realizatorem partnerstw!", style=discord.ButtonStyle.primary,
                          emoji="🔄", custom_id="shopbot:realizator")

    async def callback(self, interaction: discord.Interaction):
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


class ZostanRealizatoremPanel(PanelView):
    def __init__(self):
        opis = render(CONFIG["zostan_realizatorem_opis"], stawka=CONFIG["partnerstwo_stawka"],
                      waluta=CONFIG["partnerstwo_waluta"])
        super().__init__("Zostań Realizatorem", opis, items=[ZostanRealizatoremButton()], obrazek_typ="partnerstwo")


async def wyslij_panel_realizatora(kanal: discord.TextChannel):
    await send_or_edit_panel(kanal, ZostanRealizatoremPanel(), "realizator")


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

    tresc = (f"» **Kto nawiązał:** {interaction.user.mention}\n» **Kto został partnerem:** {partner}\n"
              f"» **Nawiązał łącznie partnerstw:** {wpis['liczba']}\n"
              f"» **Łącznie zarobił:** {wpis['zarobek']} {CONFIG['partnerstwo_waluta']}")

    kanal_id = CONFIG["channels"].get("partnerstwa")
    kanal = interaction.guild.get_channel(kanal_id) if kanal_id else interaction.channel
    await send_dynamic_card(kanal, "Nawiązano Nowe Partnerstwo", tresc, "sukces")
    if kanal.id != interaction.channel.id:
        await interaction.response.send_message(f"✅ Zgłoszono partnerstwo na {kanal.mention}.", ephemeral=True)
    else:
        await interaction.response.send_message("✅ Zgłoszono partnerstwo.", ephemeral=True)


@partnerstwo_group.command(name="statystyki", description="Pokazuje Twoje statystyki w programie partnerskim")
async def partnerstwo_statystyki(interaction: discord.Interaction):
    wpis = partner_wpis(interaction.user.id)
    tresc = (f"» **Nawiązane partnerstwa:** {wpis['liczba']}\n"
              f"» **Łączny zarobek:** {wpis['zarobek']} {CONFIG['partnerstwo_waluta']}\n"
              f"» **Aktualna stawka:** {CONFIG['partnerstwo_stawka']} {CONFIG['partnerstwo_waluta']}")
    view = PanelView("Twoje Statystyki Partnerskie", tresc, "akcent")
    await interaction.response.send_message(view=view, ephemeral=True)


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
    view = PanelView("Ranking Realizatorów Partnerstw", "\n".join(linie), "akcent")
    await interaction.response.send_message(view=view)


@partnerstwo_group.command(name="stawka", description="[Admin] Ustawia stawkę za jedno partnerstwo")
@app_commands.describe(kwota="Nowa kwota, np. 0.70")
async def partnerstwo_stawka_cmd(interaction: discord.Interaction, kwota: float):
    if not is_admin(interaction):
        await interaction.response.send_message("⚠️ Tylko administrator może zmienić stawkę.", ephemeral=True)
        return
    CONFIG["partnerstwo_stawka"] = round(kwota, 2)
    save_config()

    tresc = f"» **Nowa stawka:** {kwota} {CONFIG['partnerstwo_waluta']}\n» **Zmieniona przez:** {interaction.user.mention}"
    kanal_id = CONFIG["channels"].get("partnerstwa")
    kanal = interaction.guild.get_channel(kanal_id) if kanal_id else interaction.channel
    await send_dynamic_card(kanal, "Zmieniono Stawkę", tresc, "akcent")
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
    tresc = render(CONFIG["nowa_osoba_tresc"], mention=member.mention, ilosc=str(member.guild.member_count))
    await send_dynamic_card(kanal, "Nowa Osoba", tresc, "akcent", obrazek_typ="nowa_osoba", miniaturka=True)


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


@konfiguracja_group.command(name="obrazek", description="Ustawia obrazek dla danego panelu")
@app_commands.describe(panel="Który panel", plik="Obrazek do przesłania")
@app_commands.choices(panel=[
    app_commands.Choice(name="Weryfikacja", value="weryfikacja"),
    app_commands.Choice(name="Regulamin", value="regulamin"),
    app_commands.Choice(name="Panel ticketów", value="ticket_panel"),
    app_commands.Choice(name="Opinie", value="opinie"),
    app_commands.Choice(name="Partnerstwo", value="partnerstwo"),
    app_commands.Choice(name="Nowa osoba", value="nowa_osoba"),
    app_commands.Choice(name="Konkurs", value="konkurs"),
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
    app_commands.Choice(name="Konkursy (domyślny kanał)", value="konkursy"),
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
    role_txt = "\n".join(f"{k}: {(g.get_role(v).mention if v and g.get_role(v) else '—')}" for k, v in CONFIG["roles"].items())
    kanal_txt = "\n".join(f"{k}: {(g.get_channel(v).mention if v and g.get_channel(v) else '—')}" for k, v in CONFIG["channels"].items())
    kolor_txt = "\n".join(f"{k}: `{v}`" for k, v in CONFIG["colors"].items())
    tresc = (f"» **Nazwa sklepu:** {CONFIG['nazwa_sklepu']}\n\n"
              f"**Kolory:**\n{kolor_txt}\n\n**Role:**\n{role_txt}\n\n**Kanały:**\n{kanal_txt}\n\n"
              f"**Stawka partnerstwa:** {CONFIG['partnerstwo_stawka']} {CONFIG['partnerstwo_waluta']}")
    view = PanelView("Aktualna Konfiguracja", tresc, "akcent")
    await interaction.response.send_message(view=view, ephemeral=True)


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
#   /pomoc  — panel ze wszystkimi komendami bota
# ========================

POMOC_KATEGORIE = {
    "ogolne": {
        "etykieta": "🧭 Ogólne",
        "tresc": (
            "» **Weryfikacja** i **tickety** nie mają osobnych komend — obsługujesz je przyciskami "
            "na panelach wysłanych przez administrację.\n\n"
            "`/pomoc` — Pokazuje ten panel pomocy."
        ),
    },
    "regulamin": {
        "etykieta": "📜 Regulamin",
        "tresc": (
            "`/regulamin dodaj_strone` — Dodaje nową stronę regulaminu. *(Admin)*\n"
            "`/regulamin edytuj_strone <numer>` — Edytuje istniejącą stronę. *(Admin)*\n"
            "`/regulamin usun_strone <numer>` — Usuwa stronę regulaminu. *(Admin)*\n"
            "`/regulamin wyslij <kanal>` — Wysyła / odświeża panel regulaminu. *(Admin)*"
        ),
    },
    "blacklista": {
        "etykieta": "🚫 Blacklista",
        "tresc": (
            "`/blacklista dodaj <nick> <powod>` — Dodaje użytkownika do blacklisty. *(Staff)*\n"
            "`/blacklista usun <nick>` — Usuwa użytkownika z blacklisty. *(Staff)*\n"
            "`/blacklista sprawdz <nick>` — Sprawdza, czy nick jest na blackliście.\n"
            "`/blacklista lista` — Wyświetla całą blacklistę."
        ),
    },
    "partnerstwo": {
        "etykieta": "🤝 Partnerstwo",
        "tresc": (
            "`/partnerstwo zglos <partner>` — Zgłasza nawiązane partnerstwo. *(Realizator/Staff)*\n"
            "`/partnerstwo statystyki` — Pokazuje Twoje statystyki partnerskie.\n"
            "`/partnerstwo ranking` — Pokazuje ranking najlepszych realizatorów.\n"
            "`/partnerstwo stawka <kwota>` — Ustawia stawkę za partnerstwo. *(Admin)*"
        ),
    },
    "konkursy": {
        "etykieta": "🎉 Konkursy",
        "tresc": (
            "`/konkurs stworz <nagroda> <zwyciezcy> <czas>` — Tworzy nowy konkurs. *(Staff)*\n"
            "`/konkurs zakoncz <id>` — Kończy konkurs przed czasem i losuje zwycięzców. *(Staff)*\n"
            "`/konkurs reroll <id>` — Losuje nowych zwycięzców ponownie. *(Staff)*\n"
            "`/konkurs usun <id>` — Usuwa konkurs bez losowania. *(Staff)*\n"
            "`/konkurs lista` — Wyświetla listę aktywnych konkursów."
        ),
    },
    "panele": {
        "etykieta": "🖼️ Panele",
        "tresc": (
            "`/panel weryfikacja <kanal>` — Wysyła / odświeża panel weryfikacji. *(Admin)*\n"
            "`/panel tickety <kanal>` — Wysyła / odświeża panel ticketów. *(Admin)*\n"
            "`/panel opinie <kanal>` — Wysyła / odświeża panel opinii. *(Admin)*\n"
            "`/panel realizator <kanal>` — Wysyła / odświeża panel realizatora. *(Admin)*"
        ),
    },
    "konfiguracja": {
        "etykieta": "⚙️ Konfiguracja",
        "tresc": (
            "`/konfiguracja nazwa <nazwa>` — Ustawia nazwę sklepu. *(Admin)*\n"
            "`/konfiguracja kolor <typ> <hex>` — Zmienia kolor paneli. *(Admin)*\n"
            "`/konfiguracja obrazek <panel> <plik>` — Ustawia obrazek panelu. *(Admin)*\n"
            "`/konfiguracja rola <typ> <rola>` — Ustawia rolę używaną przez bota. *(Admin)*\n"
            "`/konfiguracja kanal <typ> <kanal>` — Ustawia kanał używany przez bota. *(Admin)*\n"
            "`/konfiguracja kategoria_ticketow <kategoria>` — Ustawia kategorię ticketów. *(Admin)*\n"
            "`/konfiguracja podglad` — Pokazuje aktualną konfigurację bota. *(Admin)*"
        ),
    },
}


class PomocSelect(discord.ui.Select):
    def __init__(self, aktualna: str):
        opcje = [
            discord.SelectOption(label=dane["etykieta"], value=klucz, default=(klucz == aktualna))
            for klucz, dane in POMOC_KATEGORIE.items()
        ]
        super().__init__(placeholder="Wybierz kategorię komend...", options=opcje,
                          custom_id="shopbot:pomoc:select", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=PomocPanel(self.values[0]))


class PomocPanel(discord.ui.LayoutView):
    def __init__(self, kategoria: str = "ogolne"):
        super().__init__(timeout=300)
        self.plik = None
        dane = POMOC_KATEGORIE.get(kategoria, POMOC_KATEGORIE["ogolne"])

        nazwa = CONFIG.get("nazwa_sklepu", "Shop").upper()
        naglowek = discord.ui.TextDisplay(f"## 💎 {nazwa} X POMOC — {dane['etykieta'].upper()}")

        dzieci = [naglowek, discord.ui.Separator(), discord.ui.TextDisplay(cytuj(dane["tresc"])),
                  discord.ui.Separator(), discord.ui.ActionRow(PomocSelect(kategoria)),
                  discord.ui.Separator(spacing=discord.SeparatorSpacing.small),
                  discord.ui.TextDisplay(footer_line("Pomoc"))]
        self.container = discord.ui.Container(*dzieci, accent_color=get_color("akcent"))
        self.add_item(self.container)


@bot.tree.command(name="pomoc", description="Pokazuje wszystkie dostępne komendy bota")
async def pomoc_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(view=PomocPanel(), ephemeral=True)


# ========================
#   START BOTA
# ========================

bot.tree.add_command(konfiguracja_group)
bot.tree.add_command(regulamin_group)
bot.tree.add_command(panel_group)
bot.tree.add_command(blacklista_group)
bot.tree.add_command(partnerstwo_group)
bot.tree.add_command(konkurs_group)


@bot.event
async def on_ready():
    bot.add_view(build_weryfikacja_panel())
    bot.add_view(RegulaminNawigacja(0))
    bot.add_view(TicketPanelWidok())
    bot.add_view(build_ticket_wiadomosc("_", "_"))
    bot.add_view(WystawOpiniePanel())
    bot.add_view(ZostanRealizatoremPanel())

    # Przywracamy trwałe widoki wszystkich niezakończonych konkursów (żeby przyciski
    # działały po restarcie bota) i doganiamy te, których czas minął w międzyczasie.
    teraz = datetime.datetime.now(datetime.timezone.utc).timestamp()
    for konkurs_id, wpis in list(CONFIG["konkursy"].items()):
        if not wpis.get("zakonczony"):
            if wpis.get("koniec", 0) <= teraz:
                await zakoncz_konkurs(bot, konkurs_id)
            elif wpis.get("message_id"):
                bot.add_view(build_konkurs_panel(konkurs_id), message_id=wpis["message_id"])

    if not sprawdzaj_konkursy.is_running():
        sprawdzaj_konkursy.start()

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
