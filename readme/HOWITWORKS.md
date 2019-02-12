# How it works

### Note on the language

This document aims to explain the mechanisms behind *Filmatyk* and the structure of its code.
Even though this project is aimed at Polish-speaking users, the entire code has been written in English.
Consequently, this document is also in English, in order to avoid the discomfort of translating concepts named in the code in English.

### The general idea

*Filmatyk* allows retrieving user's movie ratings from their filmweb.pl profile, and displaying them in an easy to browse/sort/filter manner.
The two crucial components that allow this are: the Filmweb API (for scraping of user pages - [`filmweb.py`](../filmatyk/filmweb.py)) and the GUI (for displaying the results - [`gui.py`](../filmatyk/gui.py)), which are bound together using a database (storing the ratings as objects - [`database.py`](../filmatyk/database.py)) and a presenter (responsible for post-processing the results - [`presenter.py`](../filmatyk/presenter.py)).
Movies (TODO: series and games) are stored as *items*.
Each item is an object of a special type system ([`containers.py`](../filmatyk/containers.py))
Each of those objects represents a single *item* (movie, series, game), and contains some general information about it.
These objects can also store some user-dependent information, such as rating with comment, or if it's wanted-to-watch.

### Item types

TODO
The very basic `Item` class, blueprints, meta-inheritance, rating info

### [Filmweb API](../filmatyk/filmweb.py)

The API allows retrieving user ratings from their Filmweb account, offering a set of functions encapsulated in a special object.
These methods handle everything from logging in to the account, through obtaining the number of movies the user has rated, to retrieving a list of them and returning them as processed objects, ready to store and display.
The other important task of the API object is internal session management.
Every public method is guarded - if the user is logged in, the operation proceeds normally, and in case there is no active session, a callback is made (e.g. to the GUI) for a login.

#### Parsing

Filmweb data divided into two parts - movie information is stored in one place, while rating information is elsewhere.
The API parses the items' generic information first, as it is more complex.
Each particular item info is held in a div with a specific class name (see `Constants`) -
the first step is finding and extracting those divs.
Each of them contains more nested elements (`div`s, `h3`'s, links etc.), each holding different kind of information.

The goal of parsing is to have a `dict` or similar object, with standardized values to make integration with the GUI easier.
For this reason a concept of parsing rules is introduced.
The idea is that it is known which elements each object type (movie, series, ...) needs to have - e.g. title, duration, cast.
Each of such elements is held by a different element of the HTML document.
Those elements can differ by tag (`div`, `span` etc.), by class name, as well as by means of embedding data in the element (it might be in the elements text directly, or in an attribute of some known name).
Therefore, each element to be extracted comes with a parsing rule that tells the parser exactly where to look for the data.
This parsing rule is a `dict`, with keys are described in the table below.

Key | Type | Reqd | Meaning
--- | --- | --- | ---
`tag` | str | **YES** | tag of the element holding the data (`div`, `h3`, ...)
`class` | str | **YES** | the `class` attribute of the element has to contain this string (e.g. `<div class="blah blah name blah"`)
`text` | bool | **YES** | whether the data is contained directly in the element's text, or in some of its attributes
`attr` | str | if `text` is `False` | which attribute holds the data (e.g. `'attr': 'something'` will extract 90 from `<div class="blah" something=90`)
`list` | bool | if `text` is `True` | specifies that the data is stored as several links (`<a>`) and should be parsed into a `list`
`type` | type | no | use to enforce conversion of a datum to a specified type (e.g. `int`)

This way of defining the parsing rules is more manageable, but not very good for fast processing.
For each rule, the parser would have to extract all elements of its class, then go through all the elements looking for a given name and then parse the one.
This means that a quite fine search (e.g. for every `div`) would be repeated multiple times, once for every item whose parsing rule states that it will be found in a `div`.
Instead, the API (before doing anything else) retrieves all of the rules and aggregates them by tags, inverting the rule tree.
The *parsing rules caching* (see `FilmwebAPI::__cacheParsingRules`) constructs a sort of  inverted rule tree, in which the tag type in in the top level, then are the class names, and for each of those, a specific parsing rule is defined.
The `text`, `attr` and `list` keys describe how to parse the element and the original rule name contains the name of the element to be produced.
This allows the parser to look by tags, extracting all `div`s just once, scanning through them just once, and - upon finding one with an interesting class name - retrieve the element and optionally convert it to the given `type`.

This however only lets the parser obtain the generic item information.
Ratings are held somewhere else in the document - *not* in the same major div as the item.
For this reason they are parsed separately.
Fortunately, each of the ratings is simply a JSON encoded `dict`, so the standard `json` module is used.
The rating information is then appended to the previously parsed generic data, since they share the same ID.

#### Session management

Retrieving some information from the website requires an active session with the website.
API functions that access that information are guarded by an `enforceSession` decorator.
Its job is to check whether there is an active session before executing any guarded call, and if there isn't - request a new session or disallow the operation.
This decorator is perhaps a little weird, as it is defined as a method, but actually it shall not be called on any live `FilmwebAPI` object (see the comment at its definition).

Requesting a new session is done by the `requestSession` method.
Since in order to acquire a session the user has to authenticate, there is a GUI interaction necessary.
However, the API is independent from the GUI.
Instead, the API object shall be provided a callback to a function that *actually* establishes a session:
that is, queries the user for their credentials, attempts to log in, and returns a session.
This is where the `Login` class comes into play - the master object (`Main`) instantiates a *login manager*, whose job is exactly that: ask the user for credentials, log in, return session.
Of course, the actual login is an API operation (`FilmwebAPI::login`), so the `Login` class relies back on the API to perform it.

In the end, the mechanism is as follows:
* Database makes an API request,
* the API method's decoration (`enforceSession`) launches and checks for the session,
* failing to find an active session, it calls `requestSession`,
* a GUI callback is called, blocking the execution,
* the user fills in their credentials - GUI calls the API for login,
* login either succeeds and a new session is returned, or fails and `None` is returned,
* the GUI either lets the user try again (on failure) or hides the window, returning the session to the original caller.

The motivation for this mechanism was to give the user immediate feedback on a failed login, while still separating API from the GUI:
had the API only asked the GUI for credentials, then performed the login attempt on its own, it would have to execute a callback to the GUI to inform it of a failure or success.
This may feel convoluted, but it's still simpler than having the API control the GUI -
button callbacks would have to be routed back to the API while the API should call GUI methods to notify of login error or hide on success etc.

### [Presenter](../filmatyk/presenter.py)

`Presenter` is a class responsible for displaying items from the database.
This process consists of 4 steps: retrieving the items from the DB (`totalUpdate`), (optionally) filtering them through some user-given criteria (`filtersUpdate`), (optionally) sorting them by some user-given key (`sortingUpdate`) and eventually putting them into a TreeView for interactive display (`displayUpdate`).
Those actions are arranged into a call chain; that is, triggering one of them automatically triggers all subsequent steps (this way, updating the sorting method does not require the database to be read again).

The first step is rather trivial, as the Presenter essentially acquires a copy of the data held by the database.
Rest of the steps will be briefly explained below.

#### [Filtering](../filmatyk/filters.py)

In this step, the list of items is filtered through a set of criteria chosen by the user.
The mechanism consists of two parts: a set of `Filters` - objects that encapsulate filtering by a given criterion - and a `FilterMachine` which wraps them as if they were a single object.  
Each `Filter` defines both its functionality (filters return a callable object that inputs an `Item` and returns a `bool`) as well as a GUI representation (filters directly draw their user-interactive widgets).  
A `FilterMachine` is a parent to all the instances of a `Filter` - its job is to construct a wrapping callable from all of the callables returned by each individual filter.
This callable is then evaluated by the `Presenter` on each of the items on the list, resulting in a new list of items which passed all of the criteria.

##### Filter class

The `buildUI` function is responsible for constructing a `tk.Frame` which can then be placed within the `Presenter` using a standard Tkinter interface (either a `grid` or `pack`, which wrap around the `Frame` directly).
Some filters might need a list of possible values (e.g. all directors) - a way to allow it to retrieve such a list is to implement a `populateChoices` method.
This method will be called by the `FilterMachine` (triggered by the `Presenter` whenever the database changes), automatically causing all filters to refresh their internals.  
Within a filter there is usually some update method (most concrete implementations feature an `_update`) that changes its internal state, generating a new callable.  
A filter is supposed to notify the machine about each change -- `notifyMachine` is defined in the base class for this purpose.
Since a filter is (supposed to be) equipped with a callback to the machine, this function executes said callback automatically passing the new callable to it, along with a filter ID for identification.
Each new object of `Filter` assigns itself a unique ID -- see the `__getNewID` class method.  
Filters can be reset to defaults using a `reset` and `_reset` methods.
The underscore-prefixed version **shall not** be overridden as it is responsible for the most basic aspect of a reset, that is: returning an always-`True` lambda and calling back to the machine.
The `reset` function performs a filter-specific activities, and then **shall** call to the `_reset` for the usual.

##### FilterMachine class

`Presenter` does not interact directly with the filters, with the only exception being the moment when it's being added (`Presenter::addFilter`).
Aside from that, a `FilterMachine` manages the individual filter objects, returning a callable that aggregates all of the individual filter callables -- the presenter uses this callable directly in the `filtersUpdate` on the list of its items.  
When a database changes, `Presenter` calls `FilterMachine::populateChoices`, and the machine calls the same function on all of its filters.
Similarly, the *reset all* button calls back `FilterMachine::resetAllFilters` instead of each individual filter directly.  
`FilterMachine` stores filters and their callables by IDs, allowing only the specific filter-generated callables to be replaced when a filter is modified by the user.
Each new filter has to be registered with the machine (`registerFilter`).
Whenever that happens, the machine also endows the filter with a notification callback to itself (`updateCallback`).  
Finally, whenever any filter is changed and calls back to the machine, the machine also calls back to the presenter, notifying it that it should execute the display chain from the filtering step.

#### Sorting

`TreeView` headers can be clicked to set/change the method to sort the entries.
This behavior is encapsulated in the `SortingMachine` class,
whose instance is created at the initialization of a `Presenter`.
The only thing a `Presenter` does is detection whether a header was clicked -
in this case it identifies *which column* was hit and passes it in a call to the machine.

`SortingMachine` is responsible for constructing and remembering the current
sorting criterion and for managing the `TreeView` header names.
Headings are prepended with a '▲' or '▼' character to indicate the current sorting direction.
Whenever the direction changes (by clicking on the same column again),
the label has to change as well - either by changing to the opposite sign,
or by restoring the original heading and changing the newly selected one.  
The machine constructs a `dict` containing two keys:
`key`, being the name of the property to sort by, and
`reverse`, a `bool` indicating whether the sort direction.

After the `SortingMachine` finishes the update, it returns control to the `Presenter`,
back to the `changeSorting` callback.
As the last step, it calls `sortingUpdate`, starting the display chain from there.
Only then is the sorting `dict` retrieved from the machine.
The keys are specifically named so that it can be directly passed as kwargs to the standard `list.sort`.

#### Display

A `TreeView` displays items by taking them as a `list` argument to its `insert` method.
Said list needs to have as many items as the number of columns in the TV.
However, the columns that the TV has does *not* always have to be the columns it shows -
only some columns can be marked as "display columns".
This does not change anything in the call to `insert` though -
there still has to be one value for each of the columns.

In the final step of the display chain the `displayUpdate` method,
items are placed into the `TreeView`.
First, all of the existing items are removed from the tree.
Then, for every item in the filtered and sorted list, its properties are retrieved,
going by the list of all properties the tree needs to have.
However, only some of those properties are *actually* needed,
for every property a check is needed whether it indeed has to be fetched.
This way time isn't wasted on fetching and formatting values
that will not eventually be displayed.

#### Configuring the Presenter

As a fairly abstract entity, `Presenter` in general has no knowledge
of the items that it will display.
Still, as a flexible means of data presentation,
it allows changing the configuration of columns, including:
selecting which ones are to be displayed, their order and pixel width.
All of this behavior is encapsulated in a `Config` class.

The `Config` instance is responsible for handling the configuration of a `TreeView`.
It stores the current config, allows serializing it
(in order to save it in the user data file)
and deserializing during the instantiation of the `Presenter`.
Finally, it features a separate GUI window to allow
reconfiguration of the `Presenter` by the user at runtime.

A `Config` is not instantiated directly by its owning `Presenter` -
instead, it is deserialized using a factory function `restoreFromString`.
Only in the case of an empty configuration string,
a *default* configuration is pulled from the [`defaults`](../filmatyk/defaults.py) module.
The caller passes the item type string, so that `Config` knows which class will be displayed.
It then queries this class for all available properties.
The final object stores all available columns,
and keeps track which of these are set to be displayed.
The `Presenter` makes simple `getX` requests whenever it needs to reconfigure itself.

Another aspect is the `Config`'s GUI form.
It allows the user to interact with the configuration,
showing, hiding and reordering columns to their liking.
The GUI is rather simple and features two `TreeViews` of its own.  
`Presenter` requests this window indirectly,
via a right-click menu which then calls `Config.popUp`.
This GUI steals focus from all other widgets for safety.
After the user is done reconfiguring the columns and they exit the window,
`Config` calls back to its `Presenter`,
first - if any changes have been made - making it reconfigure the `TreeView`,
and then forcing it to make a `displayUpdate`.
It is up to `Presenter`'s `configureColumns` to actually change the
layout of its `TreeView` - it only requests the information from the `Config`.

`Config` also remembers column widths.
Whenever the user manually resizes a column,
a callback bound to release of the left mouse button is executed.
It then calls `Config.manualResize` in order to store the new width.

Last two words about the format in which `Config` holds its actual configuration.
An instance of `OrderedDict` - in order to preserve the order of columns -
holds the names of columns as keys and their configured widths as values.
Names are not headings!
The exact text to display on the column headers is stored in the property `Blueprint`.
As to widths, by default they are `None`,
which only means that the width shall be also pulled from the corresponding `Blueprint`.
If however the user resizes a column,
their chosen width is stored as the value, unambiguously preserving the configuration.

### Updater

TODO
