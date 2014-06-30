#!/usr/bin/env python3

import bottle
import hashlib # računanje MD5 kriptografski hash za gesla
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki
from datetime import date, datetime, timedelta
import random # za izbiro naključne reklame na login page-u

######################################################################
# Konfiguracija

# Vklopi debug, da se bodo predloge same osvežile in da bomo dobivali lepa sporočila o napakah.
bottle.debug(True)

# Mapa s statičnimi datotekami
static_dir = "./static"

# Skrivnost za kodiranje cookijev
secret = "to skrivnost je zelo tezko uganiti 1094107c907cw982982c42"


######################################################################
#Pomožne funkcije

def password_md5(s):
    """Vrni MD5 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    h = hashlib.md5()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

def reklama_login():
    """Reklama na levi strani: generiramo en naključen izpis"""
    c = baza.cursor()
    c.execute("""SELECT DISTINCT kapaciteta, tip, cena FROM soba""")
    reklamacena=tuple(c)
    c.close()
    maxjj=len(reklamacena)-1
    jj=random.randint(0,maxjj)

    rekkap=reklamacena[jj][0]
    rektip=reklamacena[jj][1]
    rekcena=reklamacena[jj][2]
    return (rekkap, rektip, rekcena)


def rezervacija_admin():
    """Vrne vse rezervacije, ki so trenutno na bazi---ta vpogled bo imel administrator. To je osnovna verzija, ki prikaže le številko sobe, ter začetek in konec rezervacije
    """
    c = baza.cursor()
    c.execute(
    """SELECT ime, priimek, tel_st, soba, zacetek, konec, znesek  FROM pregled_rezervacij
    """)
    # Rezultat predelamo v nabor.
    termin = tuple(c)
    c.close()
    # Vrnemo nabor, kot je opisano v dokumentaciji funkcije:
    return ((ime, priimek, tel_st, soba, zacetek, konec, cena)
            for (ime, priimek, tel_st, soba, zacetek, konec, cena) in termin)


def rezervacija(oid):
    """Vrne rezervacije navadnega uporabnika.
    """
    c = baza.cursor()
    c.execute(
    """SELECT soba, tip, kapaciteta, zacetek, konec, znesek FROM pregled_rezervacij WHERE  oid = %s AND konec >= now()
    """, [oid])
    # Rezultat predelamo v nabor.
    termin = tuple(c)
    c.close()
    # Vrnemo nabor, kot je opisano v dokumentaciji funkcije:
    return ((sid, tip, kapaciteta, zacetek, konec, cena)
            for (sid, tip, kapaciteta, zacetek, konec, cena) in termin)


def rezervacija_1(oid):#
    """Vrne rezervacije navadnega uporabnika pri pogledu administratorja.
    """
    c = baza.cursor()
    c.execute(
    """SELECT ime, priimek, tel_st, soba, zacetek, konec, znesek
       FROM pregled_rezervacij WHERE oid = %s
    """, [oid])
    # Rezultat predelamo v nabor.
    termin = tuple(c)
    c.close()
    # Vrnemo nabor, kot je opisano v dokumentaciji funkcije:
    return ((ime, priimek, tel_st, soba, zacetek, konec, cena)
            for (ime, priimek, tel_st, soba, zacetek, konec, cena) in termin)


def get_user(auto_login = True):
    """Poglej cookie in ugotovi, kdo je prijavljeni uporabnik,
       vrni njegov username in ime. Če ni prijavljen, presumeri
       na stran za prijavo ali vrni None (advisno od auto_login).
    """
    # Dobimo username iz piškotka
    uporabnisko_ime = bottle.request.get_cookie('uporabnisko_ime', secret=secret)
    # Preverimo, ali ta uporabnik obstaja
    if uporabnisko_ime is not None:
        c = baza.cursor()
        c.execute("SELECT uporabnisko_ime, ime, oid FROM oseba WHERE uporabnisko_ime = %s",[uporabnisko_ime])
        r = c.fetchone()
        c.close ()
        if r is not None:
            # uporabnik obstaja, vrnemo njegove podatke
            return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        bottle.redirect('/login/')
    else:
        return None

def st_rez():
    c = baza.cursor()
    c.execute(
    """SELECT count(*) FROM termin WHERE termin.zacetek <= now() AND termin.konec >= now() GROUP BY termin
    """)
    # Rezultat predelamo v nabor.
    st = tuple(c)
    c.close()
    # Vrnemo nabor, kot je opisano v dokumentaciji funkcije:
    return st


def informativni_izracun(zacetek, konec, postavka_soba, popust):
    """Izračuna ceno, ki jo bo moral gost plačati, če najame sobo - glede na sobo in čas, cena za nočitev vikend je 1.2*nočitev teden"""
    ##count dnevi prešteje tiste, ki niso vikend
    cur = baza.cursor()
    cur.execute("""SELECT (%s*(count(dnevi))+1.2*%s*(to_date(%s,'YYYY-MM-DD')-to_date(%s,'YYYY-MM-DD')-count(dnevi)))*(100-%s)*1./100. 
    FROM (SELECT generate_series(to_date(%s,'YYYY-MM-DD'), to_date(%s,'YYYY-MM-DD')-1, '1 day')  as dnevi) days
    WHERE extract('dow' from dnevi) not in (5,6)""",[postavka_soba, postavka_soba, str(konec),str(zacetek),popust,str(zacetek),str(konec)])
    ##print(round(tuple(cur)[0][0],2))
    cena=(round(tuple(cur)[0][0],2))
    cur.close()
    
    return cena

##########################################################################################################
# Funkcije, ki obdelajo zahteve odjemalcev.

@bottle.route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova /static/..."""
    return bottle.static_file(filename, root=static_dir)

#####================Glavna stran (odprtje, cookie-ji, prilagoditev glede na uporabnika)=================================
@bottle.route("/")
def main():
    """Glavna stran."""
    # Iz cookieja dobimo uporabnika (ali ga preusmerimo na login, če
    # nima cookija)
    (uporabnisko_ime, ime, oid) = get_user()
    #Seznam vseh sob v bazi
    if uporabnisko_ime == 'admin':
        termin = rezervacija_admin()
##        if potrdilo is None:
##            potrdilo = 0     #sicer pa se mu pripiše vrednost iz vrnjene funkcije
##        if napaka is None:
##            napaka = 0
        return bottle.template("main.html",
                            uporabnisko_ime = uporabnisko_ime,
                            oid=oid,
                            soba_tip=None,
                            kapaciteta=None,
                            st_postelj=None,
                            termin=termin,
                            rezervacija=None,
                            ime_gosta=None,
                            priimek_gosta=None,
                            tel_st_gosta=None,
                            napaka=None,
                            ime_izpis=None,
                            priimek_izpis=None,
                            cena=None,
                            sporocilo_o_prijavi_gosta=None,
                            zacetek=None,
                            konec=None,
                            zacetek1=None,
                            konec1=None,
                            ratio=round(len(st_rez())/60.,1),
                            ime_gosta_1=None,# Z 1 je označeno ime gosta, ki ga vnašamo na levi strani
                            priimek_gosta_1=None,
                            tel_st_gosta_1=None,
                            potrdilo=None,
                            napaka1=None)
    else:
        termin = rezervacija(oid)
        return bottle.template("main.html",
                            uporabnisko_ime = uporabnisko_ime,
                            oid=oid,
                            termin=termin,
                            soba_tip=None,
                            kapaciteta=None,
                            st_postelj=None,
                            ime_gosta=None,
                            priimek_gosta=None,
                            tel_st_gosta=None,
                            rezervacija=None,
                            napaka=None,
                            ime_izpis=None,
                            priimek_izpis=None,
                            cena=None,
                            sporocilo_o_prijavi_gosta=None,
                            zacetek=None,
                            konec=None,
                            zacetek1=None,
                            konec1=None,
                            potrdilo=None,
                            ratio=round(len(st_rez())/60.,1),
                            ime_gosta_1=None,
                            priimek_gosta_1=None,
                            tel_st_gosta_1=None,
                            napaka1=None)

##==================================LOGIN, LOGOUT==============================================
## ko pridemo prvic gor, nam samo odpre login:
@bottle.get("/login/")
def login_get():
    """Serviraj formo za login."""
    (rekkap, rektip, rekcena)=reklama_login()
    return bottle.template("login.html",
                    napaka=None,   #na zacetku ni username-a in ni napake
                    uporabnisko_ime=None,
                    rekkap=rekkap,
                    rektip=rektip,
                    rekcena=rekcena)


## ko začne vpisovat noter in preveriš, če je uporabnik že vpisan
@bottle.post("/login/")
def login_post():
    """Obdelaj izpolnjeno formo za prijavo"""
    # Uporabniško ime, ki ga je uporabnik vpisal v formo
    uporabnisko_ime = bottle.request.forms.uporabnisko_ime
    geslo = bottle.request.forms.geslo
    # Izračunamo MD5 hash gesla, ki ga bomo spravili
    geslo = password_md5(bottle.request.forms.geslo)
    (rekkap, rektip, rekcena)=reklama_login()

    # Preverimo, ali se je uporabnik pravilno prijavil: daj mi tega, ki ima ta username in password
    cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT 1 FROM oseba WHERE uporabnisko_ime=%s AND geslo=%s",[uporabnisko_ime, geslo])
    #mi da prvi rezultat, če je to none, se ni prijavil pravilno
    if cur.fetchone() is None:
        # Username in geslo se ne ujemata
        return bottle.template("login.html",
                               napaka="Nepravilna prijava.",
                               uporabnisko_ime=uporabnisko_ime,
                               rekkap=rekkap,
                               rektip=rektip,
                               rekcena=rekcena)
          #username mu vpišemo nazaj, gesla mu seveda ne bomo nazaj poslali
    else:
        # Vse je v redu, nastavimo cookie in preusmerimo na glavno stran
        ##cookie: ime cookieja, ime vrednosti, kje je veljaven, kako je zakodiran (nekaj naključnega)
        bottle.response.set_cookie('uporabnisko_ime', uporabnisko_ime, path='/', secret=secret)
        bottle.redirect("/")
        ##pošljemo ga na glavno stran in če bo rpavilno delovala, bo vidla njegov cookie
    cur.close()


#### =====logout====================
@bottle.get("/logout/")
def logout():
    """Pobriši cookie in preusmeri na login."""
    bottle.response.delete_cookie('uporabnisko_ime')
    bottle.redirect('/login/')

#==============================REGISTER=========
@bottle.get("/register/")
def register_get():
    """Prikaži formo za registracijo."""
    return bottle.template("register.html",
                           uporabnisko_ime=None,
                           ime=None,
                           priimek=None,
                           napaka=None,
                           naslov=None,
                           tel_st=None,
                           email=None)


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
        # Če dobimo takega userja: uporabnik že obstaja; pri nas nas zanima samo username, za ime nam je vseeno (nas ne briga,
        #če bi se isti človek prijavil 2x pri 2 različnih rezervacijah
        return bottle.template("register.html",
                               uporabnisko_ime=uporabnisko_ime,
                               ime=ime,
                               priimek=priimek,
                               email=email,
                               tel_st=tel_st,
                               geslo1=geslo1,
                               geslo2=geslo2,
                               naslov=naslov,
                               napaka='To uporabniško ime je že zasedeno.')
    elif not geslo1 == geslo2:
        # Gesli se ne ujemata, vrnemo vse prejšnje noter, da ni treba še enkrat pisat
        return bottle.template("register.html",
                               uporabnisko_ime=uporabnisko_ime,
                               ime=ime,
                               priimek=priimek,
                               email=email,
                               tel_st=tel_st,
                               naslov=naslov,
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

#=======================================REZERVACIJA==========================================
@bottle.post("/")
def vnos_gosta_in_informativni_izracun():
    """Vnese gosta v tabelo oseba, če ga še ni noter in izpise ceno informativnega izracuna."""
    (uporabnisko_ime, ime, oid) = get_user()
    soba_tip = bottle.request.forms.izbrana_soba
    st_postelj = bottle.request.forms.stevilo_postelj
    ime_gosta = bottle.request.forms.ime_gosta
    priimek_gosta = bottle.request.forms.priimek_gosta
    tel_st_gosta = bottle.request.forms.tel_st_gosta
    ime_gosta_1 = bottle.request.forms.ime_gosta_1
    priimek_gosta_1 = bottle.request.forms.priimek_gosta_1
    tel_st_gosta_1 = bottle.request.forms.tel_st_gosta_1
    sporocilo_o_prijavi_gosta=0

    print('postelj: ',st_postelj)
    if (st_postelj=="1"):
        kapaciteta=2
    elif (st_postelj=="3"):
        kapaciteta=4
    else:
        kapaciteta=st_postelj
    print('kap:',kapaciteta)

    # Če niso polno zasedene sobe:
    if st_postelj=="1":
        popust=30
    elif st_postelj=="3":
        popust=15
    else:
        popust=0

    """==========================Če smo na levi strani dokumenta==============================================="""
    if len(ime_gosta)==0:
        # Če gosta še ni v tabeli oseb, ga vnesemo
        if uporabnisko_ime == 'admin':
            if len(ime_gosta_1)!=0:  #Če vnesemo nekaj pod podatke gosta
                cur = baza.cursor()
                cur.execute("""SELECT 1 FROM oseba WHERE ime = %s AND priimek = %s AND tel_st=%s""", [ime_gosta_1,priimek_gosta_1,tel_st_gosta_1])
                if cur.fetchone()==None:#če ga ni ga vnesemo
                    cur.execute("INSERT INTO oseba (ime, priimek,tel_st) VALUES (%s,%s,%s)", [ime_gosta_1,priimek_gosta_1,tel_st_gosta_1])
                    sporocilo_o_prijavi_gosta=1
                else:
                    sporocilo_o_prijavi_gosta=0
            else:
                sporocilo_o_prijavi_gosta=2
                
        #FUNKCIJA, KI IZ PREDPISANEGA FORMATA RAZBERE DATUM:
        zacetek1=bottle.request.forms.zacetek
        konec1=bottle.request.forms.konec
        zacetek=datetime.strptime(bottle.request.forms.zacetek,'%d.%m.%Y').date()
        konec=datetime.strptime(bottle.request.forms.konec,'%d.%m.%Y').date()
        #še enkrat prikaz leve strani
        if uporabnisko_ime == 'admin':
            termin = rezervacija_admin()
        else:
            termin = rezervacija(oid)

        print (soba_tip, kapaciteta, zacetek, konec)

        if (zacetek < datetime.today().date() or konec <= zacetek):
            return bottle.template("main.html",
                                    uporabnisko_ime = uporabnisko_ime,
                                    oid=oid,
                                    soba_tip=soba_tip,
                                    kapaciteta=kapaciteta,
                                    st_postelj=st_postelj,
                                    zacetek1=zacetek1,
                                    konec1=konec1,
                                    zacetek=zacetek,
                                    konec=konec,
                                    termin=termin,
                                    popust=popust,
                                    napaka="Prosimo, vnesite veljaven datum.",
                                    cena=None,
                                    sporocilo_o_prijavi_gosta=sporocilo_o_prijavi_gosta,
                                    ime_gosta=None,
                                    priimek_gosta=None,
                                    tel_st_gosta=None,
                                    ime_izpis=None,
                                    priimek_izpis=None,
                                    potrdilo=None,
                                    ratio=round(len(st_rez())/60.,1),
                                    ime_gosta_1=ime_gosta_1,
                                    priimek_gosta_1=priimek_gosta_1,
                                    tel_st_gosta_1=tel_st_gosta_1,
                                    napaka1=None)

        else:
            """Pogledamo, koliko stane izbrani tip sobe"""
            cur = baza.cursor()
            cur.execute("SELECT cena FROM soba WHERE tip=%s AND kapaciteta=%s", [str(soba_tip),kapaciteta])
            postavka_soba=float(tuple(cur)[0][0])
            cur.close ()
            cena = informativni_izracun(zacetek, konec, postavka_soba, popust)
            print('cena=',cena)

            #Poiščemo v bazi izbrano prosto sobo
            cur = baza.cursor()
            cur.execute("""SELECT sid FROM soba LEFT JOIN termin ON soba.sid=termin.soba WHERE soba.tip=%s AND soba.kapaciteta=%s AND sid NOT IN
            (SELECT sid FROM soba LEFT JOIN termin ON soba.sid=termin.soba WHERE soba.tip=%s AND soba.kapaciteta=%s AND
            (((to_date(%s, 'YYYY-MM-DD') < to_date(to_char(termin.konec, 'YYYY-MM-DD'), 'YYYY-MM-DD')) AND
             (to_date(%s, 'YYYY-MM-DD')>= to_date(to_char(termin.zacetek, 'YYYY-MM-DD'), 'YYYY-MM-DD'))) OR
             ((to_date(%s, 'YYYY-MM-DD') <= to_date(to_char(termin.konec, 'YYYY-MM-DD'), 'YYYY-MM-DD')) AND
             (to_date(%s, 'YYYY-MM-DD')> to_date(to_char(termin.zacetek, 'YYYY-MM-DD'), 'YYYY-MM-DD')))))""",
                  [str(soba_tip),kapaciteta,str(soba_tip),kapaciteta,str(zacetek),str(zacetek),str(konec),str(konec)])
            tab_soba=cur.fetchone()
            if tab_soba != None:
                soba = tab_soba[0]
            else:
                soba = tab_soba

            cur.close()

            ## Če ne najde izbrane proste sobe, mu izpišemo, da ni ok:
            if soba is None:
                napaka='Ta termin je žal zaseden. Prosimo, izberite drugi termin ali drugi tip sobe.'
                potrdilo=None
                print('sobe ni')
            else:
                if (uporabnisko_ime == 'admin' and len(ime_gosta_1)==0):  #Splošna poizvedba admina
                    potrdilo='Izbrana soba je še prosta.'
                else:
                    potrdilo='Izbrana soba je še prosta. Kliknite spodaj, da potrdite rezervacijo.'
                napaka=None
            print(popust)    
            return bottle.template("main.html",
                        uporabnisko_ime = uporabnisko_ime,
                        oid=oid,
                        soba_tip=soba_tip,
                        cena=cena,
                        sporocilo_o_prijavi_gosta=sporocilo_o_prijavi_gosta,   #user itak nima tega not
                        kapaciteta=kapaciteta,
                        st_postelj=st_postelj,
                        termin=termin,
                        zacetek=zacetek,
                        zacetek1=zacetek1,
                        konec=konec,
                        konec1=konec1,
                        rezervacija=None,
                        ime_gosta=None,
                        priimek_gosta=None,
                        tel_st_gosta=None,
                        ime_izpis=None,
                        priimek_izpis=None,
                        ratio=round(len(st_rez())/60.,1),
                        ime_gosta_1=ime_gosta_1,
                        priimek_gosta_1=priimek_gosta_1,
                        tel_st_gosta_1=tel_st_gosta_1,
                        napaka=napaka,
                        potrdilo=potrdilo,
                        popust=popust,
                        napaka1=None)

                
        
    else:
        """=====================================Desna stran, vrne poizvedbo za gosta==============================================="""
        cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT 1 FROM pregled_rezervacij WHERE ime = %s AND priimek = %s AND tel_st = %s", [ime_gosta, priimek_gosta, tel_st_gosta])
        #mi da prvi rezultat, če je to none, se ni prijavil pravilno
        if cur.fetchone() is None:
            cur.close ()
            termin = rezervacija_admin()#za vrnit osnovno stran
            # Username in geslo se ne ujemata
            print("Podatki se ne ujemajo",ime_gosta, priimek_gosta, tel_st_gosta)
            return bottle.template("main.html",
                                    uporabnisko_ime = uporabnisko_ime,
                                    oid=oid,
                                    termin=termin,
                                    ime_gosta=None,
                                    priimek_gosta=None,
                                    tel_st_gosta=None,
                                    napaka1="Gosta z danimi podatki ni v bazi.",
                                    potrdilo=None,
                                    ime_izpis=None,
                                    priimek_izpis=None,
                                    cena=None,
                                    sporocilo_o_prijavi_gosta=None,
                                    zacetek=None,
                                    konec=None,
                                    soba_tip=None,
                                    kapaciteta=None,
                                    st_postelj=None,
                                    ratio=round(len(st_rez())/60.,1),
                                    ime_gosta_1=None,
                                    priimek_gosta_1=None,
                                    tel_st_gosta_1=None,
                                    napaka=None,
                                    zacetek1=None,
                                    konec1=None,
                                    popust=popust)
        #gremo na osnovno stran, in vse v okencih pobrišemo
        else:
            cur.execute("SELECT oid FROM pregled_rezervacij WHERE ime = %s AND priimek = %s AND tel_st = %s", [ime_gosta, priimek_gosta, tel_st_gosta])
            (goid) = tuple(cur)
            termin = rezervacija_1(goid[0][0])
            cur.close ()
            return bottle.template("main.html",
                                    uporabnisko_ime = uporabnisko_ime,
                                    oid=oid,
                                    termin=termin,
                                    ime_gosta=None,
                                    priimek_gosta=None,
                                    tel_st_gosta=None,
                                    napaka=None,
                                    potrdilo=None,
                                    ime_izpis=ime_gosta,
                                    priimek_izpis=priimek_gosta,
                                    cena=None,
                                    sporocilo_o_prijavi_gosta=None,
                                    zacetek=None,
                                    konec=None,
                                    soba_tip=None,
                                    kapaciteta=None,
                                    st_postelj=None,
                                    ratio=round(len(st_rez())/60.,1),
                                    ime_gosta_1=None,
                                    priimek_gosta_1=None,
                                    tel_st_gosta_1=None,
                                    napaka1=None,
                                    zacetek1=None,
                                    konec1=None,
                                    popust=popust)

@bottle.route("/<soba_tip:path>/<kapaciteta:int>/<zacetek:path>/<konec:path>/<ime_gosta_1:path>/<priimek_gosta_1:path>/<tel_st_gosta_1:path>/<cena:path>/<st_postelj:path>/rezerviraj_gostu_sobo/")
def rezervacija_sobe_gostu(soba_tip,kapaciteta,zacetek,konec,ime_gosta_1,priimek_gosta_1,tel_st_gosta_1,cena,st_postelj):
    """Preveri, če je izbrana soba prosta in jo rezervira"""
    (uporabnisko_ime, ime, oid) = get_user()
    napaka=0
    potrdilo=0

        # Če niso polno zasedene sobe:
    if st_postelj=="1":
        popust=30
    elif st_postelj=="3":
        popust=15
    else:
        popust=0
        
    cur = baza.cursor()
    #Poglejmo id osebe, ki ji rezerviramo sobo
    cur.execute("SELECT oid FROM oseba WHERE ime = %s AND priimek = %s AND tel_st = %s", [ime_gosta_1, priimek_gosta_1, tel_st_gosta_1])
    oid_1 = int(tuple(cur)[0][0])
    #Poiščemo v bazi izbrano prosto sobo
    cur.execute("""SELECT sid FROM soba LEFT JOIN termin ON soba.sid=termin.soba WHERE soba.tip=%s AND soba.kapaciteta=%s AND sid NOT IN
    (SELECT sid FROM soba LEFT JOIN termin ON soba.sid=termin.soba WHERE soba.tip=%s AND soba.kapaciteta=%s AND
    (((to_date(%s, 'YYYY-MM-DD') < to_date(to_char(termin.konec, 'YYYY-MM-DD'), 'YYYY-MM-DD')) AND
    (to_date(%s, 'YYYY-MM-DD')>= to_date(to_char(termin.zacetek, 'YYYY-MM-DD'), 'YYYY-MM-DD'))) OR
    ((to_date(%s, 'YYYY-MM-DD') <= to_date(to_char(termin.konec, 'YYYY-MM-DD'), 'YYYY-MM-DD')) AND
    (to_date(%s, 'YYYY-MM-DD')> to_date(to_char(termin.zacetek, 'YYYY-MM-DD'), 'YYYY-MM-DD')))))""",
    [str(soba_tip),kapaciteta,str(soba_tip),kapaciteta,str(zacetek),str(zacetek),str(konec),str(konec)])
   # print ("cur.fetchone()", cur.fetchone())
    tab_soba=cur.fetchone()
   # print ('tab_soba: ',tab_soba)
   # print ('tab_soba[0]: ',tab_soba[0])
    if tab_soba != None:
        soba = tab_soba[0]
    else:
        soba = tab_soba
    #(soba,)=cur.fetchone()
    ## Če ne najde izbrane proste sobe, mu izpišemo, da ni ok:
    #if cur.fetchone() is None:
    if soba is None:
        napaka='Ta termin je žal zaseden. Prosimo, izberite drugi termin ali drugi tip sobe.'
        bottle.template("main.html",
                        uporabnisko_ime = uporabnisko_ime,
                        oid=oid,
                        soba_tip=soba_tip,
                        cena=cena,
                        sporocilo_o_prijavi_gosta=None,
                        kapaciteta=kapaciteta,
                        st_postelj=st_postelj,
                        termin=rezervacija_admin(),
                        zacetek=zacetek,
                        popust=popust,
                        zacetek1=zacetek1,
                        konec=konec,
                        konec1=konec1,
                        rezervacija=None,
                        ime_gosta=None,
                        priimek_gosta=None,
                        tel_st_gosta=None,
                        ime_izpis=None,
                        priimek_izpis=None,
                        ratio=round(len(st_rez())/60.,1),
                        ime_gosta_1=ime_gosta_1,
                        priimek_gosta_1=priimek_gosta_1,
                        tel_st_gosta_1=tel_st_gosta_1,
                        napaka='Ta termin je žal zaseden. Prosimo, izberite drugi termin ali drugi tip sobe.',
                        potrdilo=potrdilo,
                        napaka1=None)

    # Če pa je izbrana soba prosta pa vnesemo rezervacijo v tabelo
    else:
        cur.execute("INSERT INTO termin (soba, zacetek, konec, oseba, popust) VALUES (%s, %s, %s, %s, %s)",
                                                                                #(cur.fetchone()[0], zacetek, konec, oid_1, 0))
                                                                                (soba, zacetek, konec, oid_1, popust))
        potrdilo='Rezervacija je bila uspešno opravljena.'
        bottle.template("main.html",
                        uporabnisko_ime = uporabnisko_ime,
                        oid=oid,
                        popust=None,
                        soba_tip=None,
                        cena=None,
                        sporocilo_o_prijavi_gosta=None,
                        kapaciteta=None,
                        st_postelj=None,
                        termin=rezervacija_admin(),
                        zacetek=None,
                        konec=None,
                        zacetek1=None,
                        konec1=None,
                        rezervacija=None,
                        ime_gosta=None,
                        priimek_gosta=None,
                        tel_st_gosta=None,
                        ime_izpis=None,
                        priimek_izpis=None,
                        ratio=round(len(st_rez())/60.,1),
                        ime_gosta_1=None,
                        priimek_gosta_1=None,
                        tel_st_gosta_1=None,
                        napaka=napaka,
                        potrdilo='Rezervacija je bila uspešno opravljena.',
                        napaka1=None)
    cur.close ()
    return bottle.redirect("/")

@bottle.route("/<soba_tip:path>/<kapaciteta:int>/<zacetek:path>/<konec:path>/<cena:path>/<st_postelj:path>/rezerviraj_si_sobo/")
def rezervacija_sobe(soba_tip,kapaciteta,zacetek,konec,cena,st_postelj):
    """Preveri, če je izbrana soba prosta in jo rezervira"""
    (uporabnisko_ime, ime, oid) = get_user()

        # Če niso polno zasedene sobe:
    if st_postelj=="1":
        popust=30
    elif st_postelj=="3":
        popust=15
    else:
        popust=0
    
    cur = baza.cursor()
    #Poiščemo v bazi izbrano prosto sobo
    cur.execute("""SELECT sid FROM soba LEFT JOIN termin ON soba.sid=termin.soba WHERE soba.tip=%s AND soba.kapaciteta=%s AND sid NOT IN
    (SELECT sid FROM soba LEFT JOIN termin ON soba.sid=termin.soba WHERE soba.tip=%s AND soba.kapaciteta=%s AND
    (((to_date(%s, 'YYYY-MM-DD') < to_date(to_char(termin.konec, 'YYYY-MM-DD'), 'YYYY-MM-DD')) AND
    (to_date(%s, 'YYYY-MM-DD')>= to_date(to_char(termin.zacetek, 'YYYY-MM-DD'), 'YYYY-MM-DD'))) OR
    ((to_date(%s, 'YYYY-MM-DD') <= to_date(to_char(termin.konec, 'YYYY-MM-DD'), 'YYYY-MM-DD')) AND
    (to_date(%s, 'YYYY-MM-DD')> to_date(to_char(termin.zacetek, 'YYYY-MM-DD'), 'YYYY-MM-DD')))))""",
    [str(soba_tip),kapaciteta,str(soba_tip),kapaciteta,str(zacetek),str(zacetek),str(konec),str(konec)])
    print ("cur.fetchone()", cur.fetchone())
    tab_soba=cur.fetchone()
    if tab_soba != None:
        soba = tab_soba[0]
    else:
        soba = tab_soba
    ## Če ne najde izbrane proste sobe, mu izpišemo, da ni ok:
    #if cur.fetchone() is None:
    if soba is None:
        bottle.template("main.html",
                        uporabnisko_ime = uporabnisko_ime,
                        oid=oid,
                        soba_tip=soba_tip,
                        cena=cena,
                        sporocilo_o_prijavi_gosta=None,
                        kapaciteta=kapaciteta,
                        st_postelj=st_postelj,
                        termin=rezervacija(oid),
                        popust=popust,
                        zacetek=None,
                        konec=None,
                        zacetek1=None,
                        konec1=None,
                        rezervacija=None,
                        ime_gosta=None,
                        priimek_gosta=None,
                        tel_st_gosta=None,
                        ime_izpis=None,
                        priimek_izpis=None,
                        ratio=round(len(st_rez())/60.,1),
                        ime_gosta_1=None,
                        priimek_gosta_1=None,
                        tel_st_gosta_1=None,
                        napaka='Ta termin je žal zaseden. Prosimo, izberite drugi termin ali drugi tip sobe.',
                        potrdilo=None,
                        napaka1=None)

    # Če pa je izbrana soba prosta pa vnesemo rezervacijo v tabelo
    else:
        cur.execute("INSERT INTO termin (soba, zacetek, konec, oseba, popust) VALUES (%s, %s, %s, %s, %s)",
                                                                                #(cur.fetchone()[0], zacetek, konec, oid, 0))
                                                                                (soba, zacetek, konec, oid, popust))
        bottle.template("main.html",
                        uporabnisko_ime = uporabnisko_ime,
                        oid=oid,
                        soba_tip=None,
                        cena=None,
                        sporocilo_o_prijavi_gosta=None,
                        kapaciteta=None,
                        st_postelj=None,
                        popust=None,
                        termin=rezervacija(oid),
                        zacetek=None,
                        konec=None,
                        zacetek1=None,
                        konec1=None,
                        rezervacija=None,
                        ime_gosta=None,
                        priimek_gosta=None,
                        tel_st_gosta=None,
                        ime_izpis=None,
                        priimek_izpis=None,
                        ratio=round(len(st_rez())/60.,1),
                        ime_gosta_1=None,
                        priimek_gosta_1=None,
                        tel_st_gosta_1=None,
                        napaka=None,
                        potrdilo='Rezervacija je bila uspešno opravljena. Pregled vseh svojih rezervacij najdete na desni strani.',
                        napaka1=None)
    cur.close ()
    return bottle.redirect("/")


#=======================================POGLED ADMINISTRATORJA===============

   ## za izbris rezervacij gosta --- to vidi administrator
@bottle.route("/<soba:int>/<zacetek:path>/<konec:path>/delete/")
def rezervacija_delete(soba,zacetek,konec):
    """Zbriši rezervacijo"""
    c = baza.cursor()
    #c.execute("DELETE FROM termin WHERE soba=%s", [soba])
    c.execute("DELETE FROM termin WHERE soba=%s AND zacetek=%s AND konec=%s", [soba,zacetek,konec])
    c.close ()
    return bottle.redirect("/")




######################################################################
# Glavni program

# priklopimo se na bazo
### priklopimo se na bazo postgresql; vnesi svoje up.ime in geslo:
#baza = psycopg2.connect(database='seminarska_tadejd', host='audrey.fmf.uni-lj.si', user='tadejd', password='stormymonday')
#baza = psycopg2.connect(database='seminarska_tilenb', host='audrey.fmf.uni-lj.si', user='tilenb', password='59q9yipw')
baza = psycopg2.connect(database='seminarska_matejav', host='audrey.fmf.uni-lj.si', user='matejav', password='onceuponatime')
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije

# poženemo strežnik na portu 8080, glej http://localhost:8080/
# bottle.run(host='localhost', port=8080, reloader=True)
bottle.run(host='localhost', port=8080)

