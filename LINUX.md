## Instalacja fw-local na Linuksie

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
3. Uruchomienie programu powinno być proste: *wystarczy* uruchomić plik `fw-local.bat`.
Może się tak zdarzyć, że system zaprotestuje - prawdopodobnie będzie trzeba ustawić odpowiednie pozwolenia dla tego pliku.
Zrobisz to, oczywiście z konsoli, poleceniem `sudo chmod +x fw-local.bat`.

Zaznaczam, że ponieważ istnieje cała masa różnych dystrybucji linuksa, powyższe instrukcje wcale nie muszą zadziałać co do joty w podanej formie.
