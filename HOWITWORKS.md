# How it works

### Note on the language

This document aims to explain the mechanisms behind *fw-local* and the structure of its code.
Even though this project is aimed at Polish-speaking users, the entire code has been written in English.
Consequently, this document is also in English, in order to avoid the discomfort of translating concepts named in the code in English.

### The general idea

*fw-local* allows retrieving user's movie ratings from their filmweb.pl profile, and displaying them in an easy to browse/sort/filter manner.
The two crucial components that allow this are: the Filmweb API (for scraping of user pages - [`filmweb.py`](fw-local/filmweb.py)) and the GUI (for displaying the results - [`gui.py`](fw-local/gui.py)), which are bound together using a database (storing the ratings as objects - [`database.py`](fw-local/database.py)) and a presenter (responsible for post-processing the results - [`presenter.py`](fw-local/presenter.py)).
Movies (TODO: series and games) are stored as *items*.
Each item is an object of a special type system ([`containers.py`](fw-local/containers.py))
Each of those objects represents a single *item* (movie, series, game), and contains some general information about it.
These objects can also store some user-dependent information, such as rating with comment, or if it's wanted-to-watch.

### Item types

TODO
The very basic `Item` class, blueprints, meta-inheritance, rating info

### Filmweb API

The API allows retrieving user ratings from their Filmweb account, offering a set of functions encapsulated in a special object.
These methods handle everything from logging in to the account, through obtaining the number of movies the user has rated, to retrieving a list of them and returning them as processed objects, ready to store and display.
The other important task of the API object is internal session management.
Every public method is guarded - if the user is logged in, the operation proceeds normally, and in case there is no active session, a callback is made (e.g. to the GUI) for a login.

#### Parsing

Filmweb data divided into two parts - movie information is stored in one place, while rating information is elsewhere.
The API parses the items' generic information first, as it is more complex.
Each particular item info is held in a div with a specific class name (see `Constants` in [`filmweb.py`](fw-local/filmweb.py)) - the first step is finding and extracting those divs.
Each of them contains more nested elements (`div`s, `h3`'s, links etc.), each holding different kind of information.

The goal of parsing is to have a `dict` or similar object, with standardized values to make integration with the GUI easier.
For this reason a concept of parsing rules is introduced.
The idea is that it is known which elements each object type (movie, series, ...) needs to have - e.g. title, duration, cast.
Each of such elements is held by a different element of the HTML document.
Those elements can differ by tag (`div`, `span` etc.), by class name, as well as by means of embedding data in the element (it might be in the elements text directly, or in an attribute of some known name).
Therefore, each element to be extracted comes with a parsing rule that tells the parser exactly where to look for the data.
This parsing rule is a `dict`, with keys are described in the table below.

Key | Type | Reqd | Meaning
--- | ---
`tag` | str | **YES** | tag of the element holding the data (`div`, `h3`, ...)
`class` | str | **YES** | the `class` attribute of the element has to contain this string (e.g. `<div class="blah blah name blah"`)
`text` | bool | **YES** | whether the data is contained directly in the element's text, or in some of its attributes
`attr` | str | if `text` is `False` | which attribute holds the data (e.g. `'attr': 'something'` will extract 90 from `<div class="blah" something=90`)
`list` | bool | if `text` is `True` | specifies that the data is stored as several links (`<a>`) and should be parsed into a `list`

This way of defining the parsing rules is more manageable, but not very good for fast processing.
For each rule, the parser would have to extract all elements of its class, then go through all the elements looking for a given name and then parse the one.
This means that a quite fine search (e.g. for every `div`) would be repeated multiple times, once for every item whose parsing rule states that it will be found in a `div`.
Instead, the API (before doing anything else) retrieves all of the rules and aggregates them by tags, inverting the rule tree.
The *parsing rules caching* (see `FilmwebAPI::__cacheParsingRules`) constructs a sort of  inverted rule tree, in which the tag type in in the top level, then are the class names, and for each of those, a specific parsing rule is defined.
The `text`, `attr` and `list` keys describe how to parse the element and the original rule name contains the name of the element to be produced.
This allows the parser to look by tags, extracting all `div`s just once, scanning through them just once, and - upon finding one with an interesting class name - process the element.

This however only lets the parser obtain the generic item information.
Ratings are held somewhere else in the document - *not* in the same major div as the item.
For this reason they are parsed separately.
Fortunately, each of the ratings is simply a JSON encoded `dict`, so the standard `json` module is used.
The rating information is then appended to the previously parsed generic data, since they share the same ID.

#### Session management

### Presenter
