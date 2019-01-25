## fw-local na Linuksie

### Instalacja

Tutorial zakłada, że potrafisz otworzyć terminal na swoim systemie.
Będzie to potrzebne w jednym z kroków.

0. Prawdopodobnie twoja dystrybucja jest już wyposażona w Pythona 3.
Jeśli jednak tak nie jest, musisz sobie własnoręcznie zainstalować środowisko.
W razie wątpliwości użyj swojej ulubionej wyszukiwarki i wpisz frazę: "`(nazwa mojej dystrybucji) install python3`".
1. Pobierz pliki programu (link na [poprzedniej stronie](README.md)).
2. Instalacja modułów. fw-local wymaga do działania kilku dodatkowych modułów do pythona.
Są to: `pillow`, `requests_html` oraz `matplotlib`.
Standardowo moduły instaluje się z poziomu terminala poleceniem: `python3 -m pip install nazwa_modułu`.  
W przypadku popularnej dystrybucji Ubuntu (oraz podobnych, bazujących na Debianie wydaniach) konieczne może okazać się doinstalowanie jeszcze pewnego pakietu systemowego.
Zrobisz to poleceniem `sudo apt-get install python-beautifulsoup` ([źródło](https://stackoverflow.com/a/26281671/6919631)).

Zaznaczam, że ponieważ istnieje cała masa różnych dystrybucji linuksa, powyższe instrukcje wcale nie muszą zadziałać co do joty w podanej formie.

### Uruchamianie

Od wersji 1.0.0-beta.1 fw-local może być nieco niewygodny do uruchomienia,
ponieważ domyślny skrypt uruchamiający (`fw-local.bat`) jest zaprojektowany z myślą o Windowsie.
Na chwilę obecną, najwygodniej uruchomisz program z konsoli poleceniem `python3 fw-local/gui.py`
(z założeniem, że jesteś w folderze głównym programu, a więc tam gdzie widnieje plik `VERSION.json`).

### Co może nie działać

Przy aktualizacji, fw-local będzie próbował się zrestartować.
Zrobi to funkcją `os.system`, która jednak odwoła się, na windowsowską modłę,
do pliku `fw-local.bat`.
Przez to, na linuksie program nie będzie zdolny do zrestartowania.
Dlatego po aktualizacji prawdopodobnie zauważysz,
że fw-local po prostu wyłącza się i nie wstaje.

Na razie nie mam na to lepszego pomysłu niż "po prostu włącz go jeszcze raz samemu",
ale jeśli będzie zainteresowanie linuksową edycją, to poświęcę chwilę na wymyślenie
bardziej wygodnego rozwiązania.
