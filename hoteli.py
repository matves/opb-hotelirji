#!/usr/bin/env python3

import bottle
import hashlib # računanje MD5 kriptografski hash za gesla
# from datetime import datetime  #to nevemo še če bomo rabili
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki

### priklopimo se na bazo postgresql; vnesi svoje up.ime in geslo:
baza = psycopg2.connect(database='seminarska_matejav', host='audrey.fmf.uni-lj.si', user='matejav', password='onceuponatime')
#baza = psycopg2.connect(database='seminarska_tadejd', host='audrey.fmf.uni-lj.si', user='tadejd', password='stormymonday')
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)  #kurzor

######################################################################
# Konfiguracija

# Vklopi debug, da se bodo predloge same osvežile in da bomo dobivali
# lepa sporočila o napakah.
bottle.debug(True)

# Mapa s statičnimi datotekami
static_dir = "./static"

# Skrivnost za kodiranje cookijev; na zacetku secret=None
# uporabnik ne ve, kaj je notri, ne more spreminjat, krast
secret = "to skrivnost je zelo tezko uganiti 1094107c907cw982982c421"

######################################################################
# Pomožne funkcije: jih ne gledamo, dokler jih ne rabimo ;)

##### Funkcija, ki v cookie spravi sporocilo: to ne vem če sploh rabmo

def password_md5(s):
    """Vrni MD5 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    h = hashlib.md5()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

def rezervacija():
    """Vrne vse rezervacije, ki so trenutno na bazi---ta vpogled bo imel administrator. To je osnovna verzija, ki prikaže le številko sobe, ter začetek in konec rezervacije
"""
    c = baza.cursor()
    c.execute(
    """SELECT soba, zacetek, konec
FROM termin
""")
    # Rezultat predelamo v nabor.
    termin = tuple(c)
    c.close()
    # Vrnemo nabor, kot je opisano v dokumentaciji funkcije:
    return ((soba, zacetek, konec)
            for (soba, zacetek, konec) in termin)

#### Funkcija, ki preveri, kdo je prijavljen uporabnik in ga ustrezno usmeri
def get_user(auto_login = True):
    """Poglej cookie in ugotovi, kdo je prijavljeni uporabnik,
       vrni njegov username in ime. Če ni prijavljen, preusmeri
       na stran za prijavo ali vrni None (odvisno od auto_login).
    """
    # Dobimo username iz piškotka
    uporabnisko_ime = bottle.request.get_cookie('uporabnisko_ime', secret=secret)
    # Preverimo, ali ta uporabnik obstaja
    if uporabnisko_ime is not None:
        cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT uporabnisko_ime, ime, priimek FROM oseba WHERE uporabnisko_ime=%s",
                  [uporabnisko_ime])
        r = cur.fetchone()
        cur.close ()
        if r is not None:
            # uporabnik obstaja, vrnemo njegove podatke
            return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        bottle.redirect('/login/')
    else:
        return None



######################################################################
#### Funkcije, ki obdelajo zahteve odjemalcev.

@bottle.route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova
       /static/..."""
    return bottle.static_file(filename, root=static_dir)

## glavna stran: kasneje bo dodana še funkcija get_user za redirectanje na login  
@bottle.route("/")
def main():
    """Glavna stran."""
    # Iz cookieja dobimo uporabnika (ali ga preusmerimo na login, če
    # nima cookija)
    (uporabnisko_ime, ime, oid) = get_user()
    #Seznam vseh sob v bazi
    termin = rezervacija()
    return bottle.template("main.html",
                           oid=oid,
                           termin=termin)

## ko pridemo prvic gor, nam samo odpre login:
@bottle.get("/login/")  
def login_get():
    """Serviraj formo za login."""
    return bottle.template("login.html",
                           napaka=None,   #na zacetku ni username-a in ni napake
                           uporabnisko_ime=None)

## ko začne vpisovat noter in preveriš, če je uporabnik že vpisan
@bottle.post("/login/")
def login_post():
    """Obdelaj izpolnjeno formo za prijavo"""
    # Uporabniško ime, ki ga je uporabnik vpisal v formo
    uporabnisko_ime = bottle.request.forms.uporabnisko_ime
    geslo = bottle.request.forms.geslo
    # Izračunamo MD5 hash gesla, ki ga bomo spravili
    geslo = password_md5(bottle.request.forms.geslo)
    ##geslo = hashlib.md5(bottle.request.forms.geslo).hexdigest()
    
    # Preverimo, ali se je uporabnik pravilno prijavil: daj mi tega, ki ima ta username in password
    cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT 1 FROM oseba WHERE uporabnisko_ime=%s AND geslo=%s",[uporabnisko_ime, geslo])
    #mi da prvi rezultat, če je to none, se ni prijavil pravilno
    if cur.fetchone() is None:    
        # Username in geslo se ne ujemata
        print("Username in geslo se ne ujemata.",uporabnisko_ime,geslo)
        return bottle.template("login.html",
                               napaka="Nepravilna prijava",
                               uporabnisko_ime=uporabnisko_ime)
          #username mu vpišemo nazaj, gesla mu seveda ne bomo nazaj poslali
    else:
        # Vse je v redu, nastavimo cookie in preusmerimo na glavno stran
        print(uporabnisko_ime, geslo)
        ##cookie: ime cookieja, ime vrednosti, kje je veljaven, kako je zakodiran (nekaj naključnega)
        bottle.response.set_cookie('uporabnisko_ime', uporabnisko_ime, path='/', secret=secret)
        bottle.redirect("/")
        ##pošljemo ga na glavno stran in če bo rpavilno delovala, bo vidla njegov cookie

## to bo implementirano v glavno stran:
@bottle.get("/logout/")
def logout():
    """Pobriši cookie in preusmeri na login."""
    bottle.response.delete_cookie('uporabnisko_ime')
    bottle.redirect('/login/')


@bottle.get("/register/")
def register_get():    #zakaj je tuki pisal login get?
    """Prikaži formo za registracijo."""
    return bottle.template("register.html", 
                           uporabnisko_ime=None,
                           ime=None,
                           priimek=None,
                           napaka=None)


@bottle.post("/register/")
def register_post():
    """Registriraj novega uporabnika."""
    #naslov="Null"  #za primer če ne vnese naslova
    uporabnisko_ime = bottle.request.forms.uporabnisko_ime
    ime = bottle.request.forms.ime
    priimek = bottle.request.forms.priimek
    naslov = bottle.request.forms.naslov
    email = bottle.request.forms.email
    tel_st = bottle.request.forms.tel_st
    geslo1 = bottle.request.forms.geslo1
    geslo2 = bottle.request.forms.geslo2
    print(ime,priimek)
    # Ali uporabnik že obstaja?
    cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT 1 FROM oseba WHERE uporabnisko_ime=%s", [uporabnisko_ime])
    if cur.fetchone():
        # Če dobimo takega userja: uporabnik že obstaja; pri nas nas zanima samo username, za ime nam je vseeno (nas ne briga, če bi se isti človek prijavil 2x
        # pri 2 različnih rezervacijah
        return bottle.template("register.html",
                               uporabnisko_ime=uporabnisko_ime,
                               ime=ime,
                               priimek=priimek,
                               email=email,
                               tel_st=tel_st,
                               geslo1=geslo1,
                               geslo2=geslo2,
                               napaka='To uporabniško ime je že zasedeno.')
    elif not geslo1 == geslo2:
        # Gesli se ne ujemata, vrnemo vse prejšnje noter, da ni treba še enkrat pisat
        return bottle.template("register.html",
                               uporabnisko_ime=uporabnisko_ime,
                               ime=ime,
                               priimek=priimek,
                               email=email,
                               tel_st=tel_st,
                               napaka='Gesli se ne ujemata.')
    else:
        # Vse je v redu, vstavi novega uporabnika v bazo
        print("Vnesli vas bomo v bazo.")
        geslo = password_md5(geslo1)
        cur.execute("INSERT INTO oseba (ime, priimek, naslov, email, tel_st, uporabnisko_ime, geslo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                  (ime, priimek, naslov, email, tel_st, uporabnisko_ime, geslo))
        # Daj uporabniku cookie, zato da ga direktno logina
        print("Vnesli smo vas v bazo.")
        bottle.response.set_cookie('uporabnisko_ime', uporabnisko_ime, path='/', secret=secret)
        bottle.redirect("/")
        


######################################################################
# Glavni program

# poženemo strežnik na portu 8080, glej http://localhost:8080/
# če naštimaš tuki reloader=True, pol ga noče zagnat v shellu (nevem, zakaj)
bottle.run(host='localhost', port=8080, reloader=True)

#COMMITAMO IN ZAPREMO CURSOR IN BAZO
##baza.commit()
##cur.close()
##baza.close()   
