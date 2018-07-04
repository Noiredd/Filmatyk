# fw-local
**Nie podoba Ci się nowy interfejs filmweb.pl? Zaimportuj swoje oceny i przeglądaj je na swoim komputerze - tak jak lubisz!**

### Co to jest **fw-local**?
fw-local jest odpowiedzią na ostatnie zmiany w interfejsie serwisu filmweb.pl, który dla mnie osobiście stał się nieużywalny.  
fw-local pozwala na *zaimportowanie własnych ocen* z portalu i zapisanie ich lokalnie, dzięki czemu zawsze masz do nich dostęp.
Razem z Twoimi ocenami, fw-local pobiera także podstawowe informacje o obejrzanych przez Ciebie filmach - dzięki temu masz możliwość
*przeglądania ich i filtrowania* na różne sposoby - zupełnie tak, jak w starym, dobrym filmwebie!

<a href="https://raw.githubusercontent.com/Noiredd/fw-local/master/screenshot.png">
<img src="https://github.com/Noiredd/fw-local/blob/master/screenshot.png" width="900" height="432" border="10" alt="Kliknij by zobaczyć w większym rozmiarze" /></a>

### Jak uruchomić fw-local?
Na ten moment program nie ma instalatora, więc pierwsze uruchomienie może być mało wygodne.

0. Pobierz [pliki programu](https://github.com/Noiredd/fw-local/archive/1.0-alpha.4.zip) i wypakuj, gdzie Ci wygodnie.

1. Pierwszym krokiem będzie prawdopodobnie instalacja Python3 ([link do oficjalnego wydania](https://www.python.org/downloads/)) -
na chwilę obecną najnowszym wydaniem jest Python 3.6.5.
fw-local nie uruchomi się w środowisku Python 2.x!\*  
**Ważne:** na początku instalacji zaznacz `Add Python3 to PATH`!  
Jeśli już posiadasz Pythona, możesz przejść do instalacji wymaganych modułów.

2. Instalacja modułów. Jeśli to nie Twoje pierwsze starcie z Pythonem, to zainstaluj `pillow`, `requests_html` i `matplotlib`.
W przeciwnym razie po prostu odpal `setup.bat`, skrypt powinien wszystko zrobić za Ciebie.

3. Samo uruchomienie programu, jest już proste - zwyczajnie odpalasz `fw-local.bat`. Powinno ukazać Ci się okno jak w screenie wyżej (tylko puste).

\* - Uwaga dla posiadaczy Pythona 3 i 2.x *naraz* - w zależności od Twojej konfiguracji, skrypty instalacyjne/uruchamiające mogą znaleźć
różne wersje Pythona. Jeśli po uruchomieniu któregoś z nich widzisz tylko szybko znikające okienko konsoli, prawdopodobnie pierwsza
odnajdywana jest wersja 2.x (możesz to potwierdzić otwierając własne okno konsoli i wpisując `python`).

### Co potrafi fw-local?
Po pierwsze musisz zaimportować swoje oceny z filmwebu. fw-local poprosi Cię o to przy pierwszym uruchomieniu.
Pojawi się okno logowania do filmweb.pl - po wprowadzeniu danych, fw-local chwilę "pomieli" (w oknie konsoli będzie widać znaki życia -
pierwszy raz będzie dłuższy niż następne, ze względu na konieczność doinstalowania jeszcze jednego pakietu, co jednak wydarzy się
automatycznie), po czym powinien ukazać Ci się widok Twoich ocen z możliwością filtrowania, sortowania itp.

Na razie możliwe jest tylko przeglądanie ocen wystawionym filmom.

Wszystkie przyciski powinny być dość intuicyjne. Wyjaśnienie należy się tylko dwóm z nich:
* "Aktualizuj" służy do szybkiego doczytania nowych ocen z Twojego profilu - np. poprzednio było ocenionych 520 filmów, dodano jeszcze 3 oceny,
więc fw-local pobierze tylko te 3 ostatnie. Jeśli w międzyczasie dokonano zmiany którejś z ocen, *aktualizacja* tego nie uwzględni.
* "PRZEŁADUJ" służy do pełnej aktualizacji bazy, tj. cała Twoja historia ocen zostanie przejrzana ponownie i wszystkie oceny zostaną
odświeżone. Potrwa to tym więcej, im więcej masz ocen, ale to jedyna na ten moment metoda, by uwzględnić zmiany w istniejących ocenach.

Układ kolumn w głównym widoku można zmieniać poprzez modyfikację pliku `config.txt`. Może kiedyś dorobię jakieś okno ustawień, teraz mi się nie chce.

### Co planuję dalej?
Mam zamiar dodać możliwość przeglądania seriali, może też gier, a jeśli starczy mi czasu, to także list "chcę zobaczyć".
Jak już się do tego zabiorę, to oczywiście będzie można filtrować je na takie same sposoby jak już teraz można.

Niedługo powinna też dojść opcja widoku podglądu - tj. po dwukliknięciu na jakiś film pojawią się szczegóły (tytuł oryginalny, pełen komentarz etc.)
oraz plakat.

### Czy to bezpieczne?
Udostępniam kod fw-local otwarcie na licencji MIT. Głównie znaczy to, że każdy może sprawdzić, co program robi "pod maską" - dlatego
nie ma obaw, że np. kradnę hasła użytkowników.
