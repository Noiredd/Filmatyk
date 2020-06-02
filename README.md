# Filmatyk
**Chcesz pobrać wszystkie swoje oceny z Filmwebu na własny komputer?
Filmatyk pozwala Ci przeglądać/sortować/filtrować swoje oceny offline!**

### Co to jest **Filmatyk**?
Filmatyk pozwala na *zaimportowanie własnych ocen* z portalu i zapisanie ich lokalnie, dzięki czemu zawsze masz do nich dostęp.
Razem z Twoimi ocenami, Filmatyk pobiera także podstawowe informacje o obejrzanych przez Ciebie filmach -
dzięki temu masz możliwość *przeglądania ich i filtrowania* na różne sposoby - zupełnie tak, jak na Filmwebie!
Ponieważ jednak Filmatyk działa na *Twoim* komputerze, wszystko dzieje się natychmiastowo i niezależnie od połączenia z internetem.

<a href="https://raw.githubusercontent.com/Noiredd/Filmatyk/master/readme/screenshot.png">
<img src="https://raw.githubusercontent.com/Noiredd/Filmatyk/master/readme/screenshot.png" width="900" height="453" border="10" alt="Kliknij by zobaczyć w większym rozmiarze" /></a>

**WAŻNE**: Filmatyk jest na razie w fazie *beta*.
Większość funkcjonalności stabilnie działa, ale mogą pojawiać się błędy i niedoróbki.
Razem z nimi - aktualizacje naprawiające niedociągnięcia i dodające nowe możliwości.

**WAŻNE**: Filmatyk na razie działa od ręki tylko w systemie **Windows**.
Na pewno obsługiwane są wersje 7 (z SP 1) oraz 10, prawdopodobnie powinien zadziałać też w Viście.
Jeśli chcesz używać go na Linuksie bądź Maku, prawdopodobnie czeka Cię odrobina więcej pracy - czytaj dalej.

### Jak uruchomić Filmatyka?
Program został napisany w języku Python, co znaczy, że aby go używać,
potrzebujesz mieć zainstalowane środowisko tego języka.
Nie jest ono dostarczane domyślnie z systemem Windows,
więc jeśli nie masz pewności, czy je posiadasz - prawdopodobnie nie.

Poniżej znajduje się krótka instrukcja dla systemu Windows.
Jeśli pracujesz na Linuksie - zobacz [instrukcję instalacji dla Linuksa](readme/LINUX.md).

1. Pierwszym krokiem będzie prawdopodobnie **instalacja Pythona 3** ([link do oficjalnego wydania](https://www.python.org/downloads/)) -
na chwilę obecną najnowszym wydaniem jest Python 3.8.3.
Filmatyk nie uruchomi się w środowisku starszym niż Python 3.7!  
**Ważne:** na początku instalacji zaznacz `Add Python3 to PATH`!  
Jeśli już posiadasz Pythona, możesz przejść do następnego kroku.

2. Pobierz [pliki programu](https://github.com/Noiredd/Filmatyk/archive/v1.0.0-beta.4.zip) i wypakuj, gdzie Ci wygodnie.

3. **Uruchom** program przez `Filmatyk.bat`.  
**Ważne**: za pierwszym razem Filmatyk będzie musiał jednorazowo zainstalować kilka pakietów.
Zobaczysz okno terminala z przewijającymi się komunikatami technicznymi.
W zależności od szybkości Twojego łącza i komputera może to potrwać nawet kilka minut.  
Następnie powinno ukazać Ci się okno jak w screenie wyżej (tylko puste, z prośbą o pierwsze zalogowanie).

### Co potrafi Filmatyk?
Po pierwsze musisz zaimportować swoje oceny z filmwebu.
Filmatyk poprosi Cię o to przy pierwszym uruchomieniu.
Pojawi się okno logowania do filmweb.pl - po wprowadzeniu danych, program chwilę "pomieli" (patrz na pasek postępu), po czym powinien ukazać Ci się widok Twoich ocen z możliwością filtrowania, sortowania itp.

Na razie możliwe jest tylko przeglądanie (filtrowanie, wyszukiwanie, sortowanie)
wystawionych ocen (filmów, gier i seriali).

Wszystkie przyciski powinny być dość intuicyjne. Wyjaśnienie należy się tylko dwóm z nich:
* "Aktualizuj" służy do szybkiego doczytania nowych ocen z Twojego profilu - np. poprzednio było ocenionych 520 filmów, dodano jeszcze 3 oceny, więc Filmatyk pobierze tylko te 3 ostatnie.
Jeśli w międzyczasie dokonano zmiany którejś ze starszych ocen, *aktualizacja* tego nie uwzględni.
* "PRZEŁADUJ" służy do pełnej aktualizacji bazy, tj. cała Twoja historia ocen zostanie przejrzana ponownie i wszystkie oceny zostaną odświeżone.
Potrwa to trochę dłużej (tym więcej, im więcej masz ocen), ale to jedyna na ten moment metoda, by uwzględnić zmiany w istniejących ocenach.

#### Pro-tipy :)
* dwukliknij na interesujący Cię film z listy, by wyświetlić okno szczegółowego podglądu
* prawo-kliknij na nagłówek kolumn by otworzyć menu konfiguracji - możesz dzięki temu wybrać/usunąć dodatkowe kolumny z widoku bądź zmienić ich kolejność

### Co planuję dalej?
Moje pomysły na rozwój Filmatyka znajdziesz [tutaj](https://github.com/Noiredd/Filmatyk/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement).

### Czy to bezpieczne?
Udostępniam kod Filmatyka otwarcie na licencji MIT.
Głównie znaczy to, że każdy może sprawdzić, co program robi "pod maską" - dlatego nie ma obaw, że np. kradnę hasła użytkowników.

### Dla programistów
Powstaje mały [dokument](readme/HOWITWORKS.md) (ENG) opisujący zgrubnie mechanikę Filmatyka.
Może będzie wygodniej czytać kod znając ogólny pomysł na program.  
Propozycje ulepszeń a także kontrybucje są mile widziane! :)
