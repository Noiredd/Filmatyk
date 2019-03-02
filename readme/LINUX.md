## Filmatyk na Linuksie

### Instalacja

Tutorial zakłada, że potrafisz otworzyć terminal na swoim systemie
i wpisać (wkleić) do niego podstawowe komendy Linuksa.

0. Prawdopodobnie twoja dystrybucja jest już wyposażona w Pythona 3.
Jeśli jednak tak nie jest, musisz sobie własnoręcznie zainstalować środowisko.
W razie wątpliwości użyj swojej ulubionej wyszukiwarki i wpisz frazę:
"`(nazwa mojej dystrybucji) install python3`".
1. Pobierz pliki programu (link na [poprzedniej stronie](../README.md)).
2. Uruchom program za pomocą `Filmatyk_linux.sh`.
Niewykluczone, że system zabroni Ci odpalić skrypt -
w tej sytuacji najprawdopodobniej trzeba będzie ustawić zezwolenie na uruchamianie.
W dystrybucjach typu Ubuntu można wygodnie zrobić to we właściwościach pliku,
w zakładce "zezwolenia" (bądź podobnie brzmiącej) szukając opcji "pozwól na uruchamianie".
  
### Znane problemy i jak je rozwiązać

Być może twoja dystrybucja Linuksa wyposażona jest w Pythona,
ale bez specjalnego pakietu `pip` służącego do instalacji modułów
(było tak na moim Xubuntu 18.04).
W tej sytuacji Filmatyk nie będzie w stanie zainstalować potrzebnych modułów.
Filmatyk wychwyci ten problem, drukując komunikat `No module named pip`.
Aby go doinstalować, wpisz w terminalu następującą komendę:  
`sudo apt-get install python3-pip`  
uruchom i potwierdź (`y`).
Po zainstalowaniu, uruchom skrypt `Filmatyk_linux.sh` ponownie.

W przypadku popularnej dystrybucji Ubuntu
(oraz podobnych, bazujących na Debianie wydaniach)
konieczne może okazać się doinstalowanie jeszcze paru pakietów systemowych.
Zrobisz to poleceniem:  
`sudo apt-get install python-beautifulsoup python3-tkinter python3-pil.imagetk`  
([źródło](https://stackoverflow.com/a/26281671/6919631)).

Zaznaczam, że ponieważ istnieje cała masa różnych dystrybucji Linuksa, powyższe instrukcje wcale nie muszą zadziałać co do joty w podanej formie.
