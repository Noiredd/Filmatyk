## Filmatyk - test suite

### API tests
[`test.api`](test_api.py) performs tests of the `FilmwebAPI` class
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

However, the most important one is the `fetch_save` test, which not only grabs online data,
but also **stores it locally** (in `test/assets`), to simplify performing other tests.
Since this activity prompts for a Filmweb.pl **log-in**, it is disabled by default.
However, it is **required** to execute this test at least once -
otherwise other tests will error out.
To do this:  
`cd test && python test_api.py all`
