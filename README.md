# fw-local
**Nie podoba Ci się nowy interfejs filmweb.pl? Zaimportuj swoje oceny i przeglądaj je na swoim komputerze - tak jak lubisz!**

### Co to jest **fw-local**?
fw-local jest odpowiedzią na ostatnie zmiany w interfejsie serwisu filmweb.pl, który dla mnie osobiście stał się nieużywalny.  
fw-local pozwala na *zaimportowanie własnych ocen* z portalu i zapisanie ich lokalnie, dzięki czemu zawsze masz do nich dostęp.
Razem z Twoimi ocenami, fw-local pobiera także podstawowe informacje o obejrzanych przez Ciebie filmach -
dzięki temu masz możliwość *przeglądania ich i filtrowania* na różne sposoby - zupełnie tak, jak w starym, dobrym filmwebie!

<a href="https://raw.githubusercontent.com/Noiredd/fw-local/master/screenshot.png">
<img src="https://github.com/Noiredd/fw-local/blob/master/screenshot.png" width="900" height="485" border="10" alt="Kliknij by zobaczyć w większym rozmiarze" /></a>

**WAŻNE**: fw-local jest na razie w fazie *alfa* - to znaczy, że nie jest jeszcze gotowy i może (oraz będzie) ulegać różnym zmianom!

**WAŻNE**: fw-local na razie działa poprawnie tylko w systemie **Windows**.
Na pewno obsługiwane są wersje 7 (z SP 1) oraz 10, prawdopodobnie powinien zadziałać też w Viście.
Jeśli chcesz używać go na Linuksie bądź Maku, prawdopodobnie czeka Cię odrobina więcej pracy - czytaj dalej.

### Jak uruchomić fw-local?
Na ten moment program nie ma instalatora, więc pierwsze uruchomienie może być mało wygodne.
Poniżej znajduje się instrukcja instalacji dla systemu Windows.
Jeśli pracujesz na Linuksie - zobacz [instrukcję instalacji dla Linuksa](LINUX.md).

0. Pierwszym krokiem będzie prawdopodobnie **instalacja Pythona 3** ([link do oficjalnego wydania](https://www.python.org/downloads/)) -
na chwilę obecną najnowszym wydaniem jest Python 3.7.1.
fw-local nie uruchomi się w środowisku starszym niż Python 3.6!  
**Ważne:** na początku instalacji zaznacz `Add Python3 to PATH`!  
Jeśli już posiadasz Pythona, możesz przejść do następnego kroku.

1. Pobierz [pliki programu](https://github.com/Noiredd/fw-local/archive/v1.0-alpha.10.zip) i wypakuj, gdzie Ci wygodnie.

2. **Instalacja modułów**. Po prostu odpal `setup.bat`, skrypt powinien wszystko zrobić za Ciebie.  
Jeśli interesują Cię szczegóły tego, co się wydarzy: przejrzyj treść skryptu lub/i instrukcję dla Linuksa.

3. Samo **uruchomienie** programu jest już banalne - zwyczajnie odpalasz `fw-local.bat`.
Powinno ukazać Ci się okno jak w screenie wyżej (tylko puste, z prośbą o pierwsze zalogowanie).

### Co potrafi fw-local?
Po pierwsze musisz zaimportować swoje oceny z filmwebu. fw-local poprosi Cię o to przy pierwszym uruchomieniu.
Pojawi się okno logowania do filmweb.pl - po wprowadzeniu danych, fw-local chwilę "pomieli" (patrz na pasek postępu), po czym powinien ukazać Ci się widok Twoich ocen z możliwością filtrowania, sortowania itp.

Na razie możliwe jest tylko przeglądanie ocen wystawionym filmom.

Wszystkie przyciski powinny być dość intuicyjne. Wyjaśnienie należy się tylko dwóm z nich:
* "Aktualizuj" służy do szybkiego doczytania nowych ocen z Twojego profilu - np. poprzednio było ocenionych 520 filmów, dodano jeszcze 3 oceny, więc fw-local pobierze tylko te 3 ostatnie.
Jeśli w międzyczasie dokonano zmiany którejś z ocen, *aktualizacja* tego nie uwzględni.
* "PRZEŁADUJ" służy do pełnej aktualizacji bazy, tj. cała Twoja historia ocen zostanie przejrzana ponownie i wszystkie oceny zostaną odświeżone.
Potrwa to trochę dłużej (tym więcej, im więcej masz ocen), ale to jedyna na ten moment metoda, by uwzględnić zmiany w istniejących ocenach.

#### Pro-tipy :)
* dwukliknij na interesujący Cię film z listy, by wyświetlić okno szczegółowego podglądu
* prawo-kliknij na nagłówek kolumn by otworzyć menu konfiguracji - możesz dzięki temu wybrać/usunąć dodatkowe kolumny z widoku bądź zmienić ich kolejność

### Co planuję dalej?
Następnym krokiem będzie dodanie możliwości przeglądania ocen seriali i gier.
Dalej - list "chcę zobaczyć".
Oczywiście nowe kategorie będzie można filtrować na takie same sposoby jak obecnie.

Myślę też o poszerzeniu widoku statystyk o parę ciekawszych wskaźników.

### Czy to bezpieczne?
Udostępniam kod fw-local otwarcie na licencji MIT.
Głównie znaczy to, że każdy może sprawdzić, co program robi "pod maską" - dlatego nie ma obaw, że np. kradnę hasła użytkowników.

### Dla programistów
Powstaje mały [dokument](HOWITWORKS.md) (ENG) opisujący zgrubnie mechanikę fw-local.
Może będzie wygodniej czytać kod znając ogólny pomysł na program.  
Propozycje ulepszeń a także kontrybucje są mile widziane! :)
