#!/usr/bin/env python3

import bottle
import hashlib # računanje MD5 kriptografski hash za gesla
# from datetime import datetime  #to nevemo še če bomo rabili
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki

######################################################################
# Konfiguracija

# Vklopi debug, da se bodo predloge same osvežile in da bomo dobivali
# lepa sporočila o napakah.
bottle.debug(True)

# Mapa s statičnimi datotekami
static_dir = "./static"

# Skrivnost za kodiranje cookijev; na zacetku secret=None
# uporabnik ne ve, kaj je notri, ne more spreminjat, krast
# odkomentiraj, ko boš nastavil cookie-je:
# secret = "to skrivnost je zelo tezko uganiti 1094107c907cw982982c42"
secret = None

######################################################################
# Pomožne funkcije: jih ne gledamo, dokler jih ne rabimo ;)


######################################################################
# Funkcije, ki obdelajo zahteve odjemalcev.

@bottle.route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova
       /static/..."""
    return bottle.static_file(filename, root=static_dir)

@bottle.route("/")
def main():
    """Glavna stran."""
    return 'To je glavni dokument, trenutno je še prazen. Pojdi raje na <a href="/login/">ta naslov</a>.'
    # return bottle.template("main.html", ...)

# to je ce pridemo prvic:
@bottle.get("/login/")  
def login_get():
    """Serviraj formo za login."""
       return bottle.template("login.html",
                           napaka=None,   #na zacetku ni username-a in ni napake
                           username=None)
    
#@bottle.post("/login/")


##@bottle.get("/logout/")


#@bottle.get("/register/")


#@bottle.post("/register/")


#@bottle.route("/user/<username>/")

    
#@bottle.post("/user/<username>/")




######################################################################
# Glavni program

### priklopimo se na bazo postgresql; vnesi svoje up.ime in geslo:
conn = psycopg2.connect(database='seminarska_matejav', host='audrey.fmf.uni-lj.si', user='matejav', password='onceuponatime')
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# poženemo strežnik na portu 8080, glej http://localhost:8080/
bottle.run(host='localhost', port=8080)
