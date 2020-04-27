## Filmatyk - test suite

### API tests
[`test_api.py`](test_api.py) performs tests of the `FilmwebAPI` class
([`filmweb.py`](../filmatyk/filmweb.py)) - fetching and parsing content from Filmweb.

Testing the whole program would typically require logging in to Filmweb.pl,
which might get cumbersome after a while.
Therefore, tests are split into two convenient parts: online and offline.
The basic online interface test is tested first, during which data is fetched
and cached locally.
This allows the more detailed tests to run without the need for online connection,
instead these cached files are used as data source.

#### Basic online test: `TestAPIBasics`

Test class `TestAPIBasics` encapsulates tests of the most fundamental functionalities:
* logging in to Filmweb.pl,
* fetching raw HTML data.

However, the most important one are the `fetch_save` tests, which not only grab online data,
but also **store it locally** (in `test/assets`), to simplify performing other tests.
Since this activity prompts for a Filmweb.pl **log-in**, it is disabled by default.
However, it is **required** to execute this test at least once -
otherwise other tests will error out.
To do this:  
`cd test && python test_api.py all`

#### Detailed offline test: `TestAPIParsing`

Test class `TestAPIParsing` performs step-by-step tests of the parsing mechanism.
Items extracted from the raw HTML data are in fact separate -
details of rated items (movies etc.) are stored in one place,
while their ratings are elsewhere.
Tests are done sequentially, from locating the sources for data,
through parsing a single entity, to parsing a complete page.

### Database tests
[`test_database.py`](test_database.py) performs tests of the `Database` class
([`database.py`](../filmatyk/database.py)) - updating and serialization (TODO).

For speed and convenience, the update is not performed online.
Instead, a fake API object is created (`FakeAPI`) that mimmicks the normal `FilmwebAPI` behavior,
except instead of connecting to Filmweb.pl it reads data cached previously by the API tests.

For debugging and development, a `DatabaseDifference` class is introduced
to encapsulate the notion of, well, difference between two `Database` objects.
This object is constructed by a static method `compute` and is `bool`-convertible,
which allows implementing a `!=` operator for the `Database`.
Additionally, it is `str`-convertible, allowing nice printing for explaining the difference.
Before the tests are run, `DatabaseDifference.compute` is injected into the `Database`
as the `__ne__` operator, so all comparisons during the testing are done this way.

*Note*: `Database` is only tested for the `Movie` item type,
as the algorithm is abstract with respect to the item type.

#### Basic tests

The first two tests - `TestDatabaseCreation` and `TestDatabaseSerialization`
are responsible for the most basic functionality of the `Database`.
The creation test is of a particular importance here,
as if that one fails, pretty much everything else after that will also fail.

#### Update tests

Database update tests (`TestDatabaseUpdates`) are performed by loading a reference `Database` first
(this utilizes assets cached in API tests).
Each test simulates a situation in which this reference `Database` is the desired outcome,
and the "current" state is generated dynamically according to some scenario.
`UpdateScenario` encapsulates the idea of such scenario,
for example "the current state misses the first two items" could be expressed by:  
`scenario = UpdateScenario(removals=[0, 1])`  
The function `makeModifiedDatabase` ingests such `Scenario` object
and constructs a new `Database`, simulating a previous state (as if "undoing" an update).
During the test, this "undone" object attempts to update itself to the reference state.
Results are compared using the aforementioned `DatabaseDifference`.

Note that currently all removal tests fail
due to the removal detection not being implemented in the Database update algorithm.

