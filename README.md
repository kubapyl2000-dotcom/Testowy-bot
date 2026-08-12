# ShopBot — panel weryfikacji, ticketów, opinii, blacklisty i programu partnerskiego

Panele bota wyglądają jak jedna spójna "karta" — kolorowy pasek z boku, nagłówek, treść,
przyciski i stopka w tej samej ramce (dokładnie tak jak w oryginalnym stylu, na którym się wzorowałeś).
Osiągnięte to jest przez nowszy system UI Discorda, tzw. **Components V2** (`discord.ui.Container` /
`TextDisplay` / `Section` / `Separator`), dlatego wymagana jest świeższa wersja `discord.py` — patrz niżej.

## 1. Instalacja

```bash
pip install -r requirements.txt
```

**Wymagane discord.py >= 2.6.0** (Components V2 nie działa na starszych wersjach).

## 2. Uruchomienie

Ustaw token bota jako zmienną środowiskową i uruchom:

```bash
export DISCORD_TOKEN="twój_token_bota"
export TEST_GUILD_ID="id_twojego_serwera"   # opcjonalnie - komendy pojawią się natychmiast, nie po ~1h
python3 bot.py
```

Bot zapisuje ustawienia do pliku `config.json` (tworzy się automatycznie przy pierwszym uruchomieniu)
oraz przesłane obrazki do folderu `obrazki/`.

## 3. Uprawnienia bota na Discordzie

Przy tworzeniu zaproszenia (OAuth2 → bot) zaznacz:
- `bot`, `applications.commands`
- Uprawnienia: `Manage Roles`, `Manage Channels`, `Send Messages`, `Embed Links`,
  `Attach Files`, `Add Reactions`, `Read Message History`

**Rola bota musi być wyżej** niż rola "Zweryfikowany" i "Realizator" na liście ról serwera,
inaczej nie będzie mógł ich nadawać.

## 4. Pierwsza konfiguracja (na serwerze, jako administrator)

1. `/konfiguracja nazwa` — nazwa Twojego sklepu (pojawia się we wszystkich panelach)
2. `/konfiguracja kolor` — kolory paneli (akcent / sukces / błąd), HEX np. `#5865F2`
3. `/konfiguracja rola` — role: `zweryfikowany`, `staff`, `realizator`
4. `/konfiguracja kanal` — kanały: weryfikacja, panel ticketów, opinie, partnerstwa, blacklista, powitania
5. `/konfiguracja kategoria_ticketow` — kategoria, w której mają się tworzyć kanały ticketów
6. `/konfiguracja obrazek` — opcjonalny banner/obrazek dla każdego panelu
7. `/konfiguracja podglad` — podgląd całej aktualnej konfiguracji

## 5. Wysyłanie paneli

- `/panel weryfikacja #kanał` — panel z przyciskiem weryfikacji (nadaje rolę od razu, bez żadnych zewnętrznych stron)
- `/panel tickety #kanał` — panel z listą kategorii ticketów
- `/panel opinie #kanał` — panel „wystaw opinię”
- `/panel realizator #kanał` — panel „zostań realizatorem partnerstw”
- `/regulamin wyslij #kanał` — panel regulaminu (strzałki Poprzednia/Następna)

Każda z tych komend, wywołana ponownie na tym samym kanale, **edytuje istniejący panel** zamiast
tworzyć duplikat — więc możesz spokojnie zmieniać treści i odświeżać.

## 6. Regulamin

- `/regulamin dodaj_strone` — otwiera formularz (tytuł + treść), dodaje nową stronę na koniec
- `/regulamin edytuj_strone numer:2` — edytuje wskazaną stronę
- `/regulamin usun_strone numer:2` — usuwa stronę
- `/regulamin wyslij #kanał` — odświeża panel po zmianach

## 7. Program partnerski

- Osoba klika „Zostań realizatorem” → dostaje rolę `realizator`
- `/partnerstwo zglos partner:"opis/serwer"` — realizator zgłasza nawiązane partnerstwo,
  automatycznie nalicza mu się kwota wg aktualnej stawki
- `/partnerstwo stawka kwota:0.70` — **admin** zmienia stawkę w dowolnym momencie
- `/partnerstwo statystyki` — realizator widzi swoje statystyki
- `/partnerstwo ranking` — ranking najlepszych realizatorów

Wypłatę (BLIK, PayPal itd.) przekazujecie ręcznie — bot tylko prowadzi ewidencję i liczy kwoty.

## 8. Blacklista

- `/blacklista dodaj nick:"ktoś" powod:"opis"` — dodaje wpis i publikuje go na kanale blacklisty
- `/blacklista usun nick:"ktoś"`
- `/blacklista sprawdz nick:"ktoś"`
- `/blacklista lista` — cała lista

## 9. Czego bot celowo NIE robi

- Nie ma żadnej zewnętrznej strony/OAuth do „weryfikacji” — rola nadawana jest bezpośrednio przez bota.
- Nie zawiera gotowego cennika/sprzedaży kont czy „boostów” — to dodajesz sam, w swoim panelu produktów,
  jeśli sprzedajesz legalne, własne usługi/produkty.
- Nie ma mechanizmu przenoszenia rang/rang między kontami.

## 10. Rozbudowa

Kod jest podzielony na czytelne sekcje (weryfikacja, regulamin, tickety, opinie, blacklista,
partnerstwo, konfiguracja) — możesz mi wysłać ten plik ponownie z prośbą o dodanie kolejnej
funkcji (np. panel produktów z cennikiem, system giveaway, statystyki sprzedaży) i rozbuduję go dalej.
