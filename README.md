#Hotelirji

A web site implemented in [bottle](http://bottlepy.org/) and [psycopg2](http://www.stickpeople.com/projects/python/win-psycopg/), also using other technology, as needed. For educational purposes, I am not actually trying to get rich.
From here on in Slovene.

Projekt pri predmetu Osnove podatkovnih baz

## Datoteke:
* `bottle.py` -- knjižnica Bottle
* `shema.sql` -- shema za bazo (ukazi `CREATE TABLE`)
* `hoteli.py` -- strežnik (verzija Python 3)
* `views` -- predloge za spletne strani 
* `static` -- statične spletne strani in datoteke ([Bootstrap](http://getbootstrap.com/))
* `oseba.csv`, `soba.csv`, `termini.csv`  -- podatki za začetno polnitev baze
* `uvoz.py` -- program za uvoz podatkov v podatkovno bazo na strežniku

## Namestitev:
Med bazami odkomentiramo pravo in poženemo dokument `hotel.py`.
