## Change log

### v1.0.0-beta.4
02-06-2020

#### Nowości
* (#31) opcja "zapamiętaj mnie" - już nie trzeba logować się co chwilę od nowa! ([7e33b17](../../commit/7e33b17), [a575bb0](../../commit/a575bb0))
* (#28) nowy, napisany zupełnie od zera algorytm aktualizacji bazy - różnice pomiędzy tym, co widzisz w Filmatyku a co na swoim profilu w Filmwebie, będą występować już tylko w szczególnych okolicznościach (a w planach jest rozwiązanie kompletne: #29) ([fd121b9](../../commit/fd121b9))

#### Poprawki
* aktualizacja mechanizmu logowania w odpowiedzi na drobną zmianę po stronie Filmwebu ([6f38ef2](../../commit/6f38ef2))
* aktualizacja parsera w odpowiedzi na zmiany w wyświetlaniu posterów i roku produkcji na Filmwebie ([261089d](../../commit/261089d))

#### Techniczne
* (#33) wprowadzenie systemu do przechowywania opcji programu ([d4d8287](../../commit/d4d8287), [e2ba9f2](../../commit/e2ba9f2), [09e12b5](../../commit/09e12b5))
* usprawnienia API ([497dadf](../../commit/497dadf)) i systemu odczytu pliku danych ([cdb25a6](../../commit/cdb25a6))
* wątek Updatera nigdy nie był joinowany - naprawiono ([cf0e62e](../../commit/cf0e62e))


### v1.0.0-beta.3
10-05-2020

#### Poprawki
* (#30) naprawiono błąd z parsowaniem ocen ([aac15e9](../../commit/aac15e9))
* uaktualniono system wczytywania do najnowszego standardu strony Filmweb ([485c762](../../commit/485c762))
* uzupełniono listę wymaganych pakietów do automatycznej instalacji ([4e52751](../../commit/4e52751))

#### Techniczne
* wprowadzono pakiet testów podstawowych funkcjonalności:
  * logowania i pobierania danych ([33dbf75](../../commit/33dbf75))
  * parsowania danych ([aac15e9](../../commit/aac15e9), [69e6a8d](../../commit/69e6a8d), [7ede8e0](../../commit/7ede8e0))
  * tworzenia i serializacji bazy danych ([b4343a7](../../commit/b4343a7), [6fe9d55](../../commit/6fe9d55))
  * aktualizacji bazy danych ([52d2dc8](../../commit/52d2dc8), [e5098a3](../../commit/e5098a3), [a48a833](../../commit/a48a833))
* uzupełniono dokumentację modułu `containers` ([a4d948e](../../commit/a4d948e))


### v1.0.0-beta.2
15-12-2019

#### Poprawki
* poprawiono wygląd niektórych filtrów ([c9e5428](../../commit/c9e5428), [3938986](../../commit/3938986))
* (#22) naprawiono zachowanie przycisku "x" w oknie podglądu i logowania ([1d575ed](../../commit/1d575ed))
* (#27) ulepszono filtr daty obejrzenia ([e3e985a](../../commit/e3e985a))
* (#25) dodano możliwość zaznaczania w liście ocen ([ea01fc3](../../commit/ea01fc3))
* (#20) naprawiono błąd w ekranie logowania na Linuksie ([5a35445](../../commit/5a35445))
* (#19, #23) naprawiono błąd z oknem głównym pozostającym na wierzchu ([89b407e](../../commit/89b407e), [55a5e66](../../commit/55a5e66))
* ulepszono updater ([bc0237f](../../commit/bc0237f))
* (#24, ...) poprawiono dokumentację ([eb0f094](../../commit/eb0f094), [cd8b9f9](../../commit/cd8b9f9))
* wykonano kilka mniejszych i większych technicznych poprawek ([8c20158](../../commit/8c20158), [3d8833d](../../commit/3d8833d), [cd9f648](../../commit/cd9f648), [6d2fb2e](../../commit/6d2fb2e))

#### Nowości
* (#16) dodano wsparcie dla Linuksa ([0e552b3](../../commit/0e552b3), [0340c0b](../../commit/0340c0b))

#### Uwagi

Ze względu na dość poważne zmiany w updaterze, tę aktualizację należy wykonać ręcznie
(tj. samodzielnie usunąć starą wersję i pobrać program od nowa).


### v1.0.0-beta.1
31-01-2019

Pierwsze "stabilne" wydanie Filmatyka. Program umie:
* pobierać i zapisywać bazę ocen filmów, seriali i gier prosto z filmweb.pl,
* filtrować listę na różne sposoby (ocena, data, rok produkcji, gatunek, ...),
* wyświetlać ją w konfigurowalnej tabeli,
* sortować tabelę według dowolnego kryterium,
* rysować histogramy wybranego zakresu ocen,
* wyświetlać okno podglądu szczegółów danej pozycji (włącznie z plakatem),
* samodzielnie aktualizować się, gdy wyjdzie nowe wydanie,
* samodzielnie instalować potrzebne moduły.
