#!/usr/bin/env python3

import bottle
import hashlib # računanje MD5 kriptografski hash za gesla
# from datetime import datetime  #to nevemo še če bomo rabili
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki
from datetime import date, datetime


######################################################################
# Konfiguracija

# Vklopi debug, da se bodo predloge same osvežile in da bomo dobivali
# lepa sporočila o napakah.
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

def rezervacija_admin():
	"""Vrne vse rezervacije, ki so trenutno na bazi---ta vpogled bo imel administrator. To je osnovna verzija, ki prikaže le številko sobe, ter začetek in konec rezervacije
	"""
	c = baza.cursor()
	c.execute(
	"""SELECT ime, priimek, tel_st, soba, zacetek, konec
	   FROM oseba JOIN termin ON oseba.oid = termin.oseba
	""")
	# Rezultat predelamo v nabor.
	termin = tuple(c)
	c.close()
	# Vrnemo nabor, kot je opisano v dokumentaciji funkcije:
	return ((ime, priimek, tel_st, soba, zacetek, konec)
			for (ime, priimek, tel_st, soba, zacetek, konec) in termin)

def rezervacija(oid):
	"""Vrne rezervacije navadnega uporabnika. 
	"""
	c = baza.cursor()
	c.execute(
	"""SELECT sid, tip, kapaciteta, zacetek, konec, cena FROM soba JOIN termin ON termin.soba = soba.sid WHERE  termin.oseba = %s AND konec >= now()
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
	"""SELECT ime, priimek, tel_st, soba, zacetek, konec
	   FROM oseba JOIN termin ON oseba.oid = termin.oseba WHERE termin.oseba = %s
	""", [oid])
	# Rezultat predelamo v nabor.
	termin = tuple(c)
	c.close()
	# Vrnemo nabor, kot je opisano v dokumentaciji funkcije:
	return ((sid, tip, kapaciteta, zacetek, konec, cena)
			for (sid, tip, kapaciteta, zacetek, konec, cena) in termin)


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

######################################################################
# Funkcije, ki obdelajo zahteve odjemalcev.

@bottle.route("/static/<filename:path>")
def static(filename):
	"""Splošna funkcija, ki servira vse statične datoteke iz naslova
	   /static/..."""
	return bottle.static_file(filename, root=static_dir)

#####================Glavna stran (odprtje, cookie-ji)=================================
@bottle.route("/")
def main():
	"""Glavna stran."""
	# Iz cookieja dobimo uporabnika (ali ga preusmerimo na login, če
	# nima cookija)
	(uporabnisko_ime, ime, oid) = get_user()
	#Seznam vseh sob v bazi
	if uporabnisko_ime == 'admin':
		termin = rezervacija_admin()
		return bottle.template("main.html",
							uporabnisko_ime = uporabnisko_ime,
							oid=oid,
							soba_tip=None,
							kapaciteta=None,
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
							ratio=round(len(st_rez())/60.,1),
							ime_gosta_1=None,# Z 1 je označeno ime gosta, ki ga vnašamo na levi strani
							priimek_gosta_1=None,
							tel_st_gosta_1=None,
							napaka1=None)
	else:
		termin = rezervacija(oid)
		return bottle.template("main.html",
							uporabnisko_ime = uporabnisko_ime,
							oid=oid,
							termin=termin,
							soba_tip=None,
							kapaciteta=None,
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


#### to bo implementirano v glavno stran:
@bottle.get("/logout/")
def logout():
	"""Pobriši cookie in preusmeri na login."""
	bottle.response.delete_cookie('uporabnisko_ime')
	bottle.redirect('/login/')

#==============================REGISTER=========
@bottle.get("/register/")
def register_get():	#zakaj je tuki pisal login get?
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

#=======================================REZERVACIJA==========================================
@bottle.post("/")  
def vnos_gosta_in_informativni_izracun():
	"""V nese gosta v tabelo oseba, če ga še ni noter in izpise ceno informativnega izracuna."""
	(uporabnisko_ime, ime, oid) = get_user()
	soba_tip = bottle.request.forms.izbrana_soba
	kapaciteta = bottle.request.forms.stevilo_postelj
	ime_gosta = bottle.request.forms.ime_gosta
	priimek_gosta = bottle.request.forms.priimek_gosta
	tel_st_gosta = bottle.request.forms.tel_st_gosta
	ime_gosta_1 = bottle.request.forms.ime_gosta_1
	priimek_gosta_1 = bottle.request.forms.priimek_gosta_1
	tel_st_gosta_1 = bottle.request.forms.tel_st_gosta_1
	sporocilo_o_prijavi_gosta=0
	if len(ime_gosta)==0:#ce smo na levi
		# Če gosta še ni v tabeli oseb, ga vnesemo
		if uporabnisko_ime == 'admin':
			cur = baza.cursor()
			cur.execute("""SELECT 1 FROM oseba WHERE ime = %s AND priimek = %s AND tel_st=%s""", [ime_gosta_1,priimek_gosta_1,tel_st_gosta_1])
			if cur.fetchone()==None:#če ga ni ga vnesemo
				cur.execute("INSERT INTO oseba (ime, priimek,tel_st) VALUES (%s,%s,%s)", [ime_gosta_1,priimek_gosta_1,tel_st_gosta_1])
				sporocilo_o_prijavi_gosta=1   
		#FUNKCIJA, KI IZ PREDPISANEGA FORMATA RAZBERE DATUM:		
		zacetek=datetime.strptime(bottle.request.forms.zacetek,'%d.%m.%Y').date()
		konec=datetime.strptime(bottle.request.forms.konec,'%d.%m.%Y').date()
		#še enkrat prikaz leve strani
		if uporabnisko_ime == 'admin':
			termin = rezervacija_admin()
		else:
			termin = rezervacija(oid)
		
		print (soba_tip, kapaciteta,zacetek, konec)

		if (zacetek < datetime.today().date() or konec <= zacetek):
			return bottle.template("main.html",
									uporabnisko_ime = uporabnisko_ime, 
									oid=oid,
									soba_tip=soba_tip,
									kapaciteta=kapaciteta,
									zacetek=zacetek,
									konec=konec,
									termin=termin,
									napaka="Prosimo, vnesite veljaven datum.",
									cena=None,
									sporocilo_o_prijavi_gosta=sporocilo_o_prijavi_gosta,
									ime_gosta=None,
									priimek_gosta=None,
									tel_st_gosta=None,
									ime_izpis=None,
									priimek_izpis=None,
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
			cena = informativni_izracun(zacetek, konec, postavka_soba)
			return bottle.template("main.html",
									uporabnisko_ime = uporabnisko_ime,
									oid=oid,
									cena=cena,
									sporocilo_o_prijavi_gosta=sporocilo_o_prijavi_gosta,
									soba_tip=soba_tip,
									kapaciteta=kapaciteta,
									termin=termin,
									zacetek=zacetek,
									konec=konec,
									napaka=None,
									ime_gosta=None,
									priimek_gosta=None,
									tel_st_gosta=None,
									ime_izpis=None,
									priimek_izpis=None,
									ratio=round(len(st_rez())/60.,1),
									ime_gosta_1=ime_gosta_1,
									priimek_gosta_1=priimek_gosta_1,
									tel_st_gosta_1=tel_st_gosta_1,
									napaka1=None)
	else:
		"""Desna stran, vrne poizvedbo za gosta"""
		cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute("SELECT 1 FROM termin JOIN oseba ON termin.oseba=oseba.oid WHERE ime = %s AND priimek = %s AND tel_st = %s", [ime_gosta, priimek_gosta, tel_st_gosta])
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
									napaka1="Nepravilen vnos",
									ime_izpis=None,
									priimek_izpis=None,
									cena=None,
									sporocilo_o_prijavi_gosta=None,
									zacetek=None,
									konec=None,
									soba_tip=None,
									kapaciteta=None,
									ratio=round(len(st_rez())/60.,1),
									ime_gosta_1=None,
									priimek_gosta_1=None,
									tel_st_gosta_1=None,
									napaka=None)
		#gremo na osnovno stran, in vse v okencih pobrišemo
		else:
			cur.execute("SELECT oid FROM oseba WHERE ime = %s AND priimek = %s AND tel_st = %s", [ime_gosta, priimek_gosta, tel_st_gosta])
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
									ime_izpis=ime_gosta,
									priimek_izpis=priimek_gosta,
									cena=None,
									sporocilo_o_prijavi_gosta=None,
									zacetek=None,
									konec=None,
									soba_tip=None,
									kapaciteta=None,
									ratio=round(len(st_rez())/60.,1),
									ime_gosta_1=None,
									priimek_gosta_1=None,
									tel_st_gosta_1=None,
									napaka1=None)
							   
@bottle.route("/<soba_tip:path>/<kapaciteta:int>/<zacetek:path>/<konec:path>/<ime_gosta_1:path>/<priimek_gosta_1:path>/<tel_st_gosta_1:path>/<cena:path>/rezerviraj_gostu_sobo/")
def rezervacija_sobe_gostu(soba_tip,kapaciteta,zacetek,konec,ime_gosta_1,priimek_gosta_1,tel_st_gosta_1,cena):
	"""Preveri, če je izbrana soba prosta in jo rezervira"""
	(uporabnisko_ime, ime, oid) = get_user()
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
	(soba,)=cur.fetchone()
	## Če ne najde izbrane proste sobe, mu izpišemo, da ni ok:
	if cur.fetchone() is None:  
		bottle.template("main.html",
						uporabnisko_ime = uporabnisko_ime,
						oid=oid,
						soba_tip=soba_tip,
						cena=cena,
						sporocilo_o_prijavi_gosta=None,
						kapaciteta=kapaciteta,
						termin=rezervacija_admin(),
						zacetek=zacetek,
						konec=konec,
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
						napaka1=None)
	
	# Če pa je izbrana soba prosta pa vnesemo rezervacijo v tabelo
	else:
		cur.execute("INSERT INTO termin (soba, zacetek, konec, oseba, popust) VALUES (%s, %s, %s, %s, %s)",
																				(cur.fetchone()[0], zacetek, konec, oid_1, 0))
		bottle.template("main.html",
						uporabnisko_ime = uporabnisko_ime,
						oid=oid,
						soba_tip=None,
						cena=None,
						sporocilo_o_prijavi_gosta=None,
						kapaciteta=None,
						termin=rezervacija_admin(),
						zacetek=None,
						konec=None,
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
						napaka1=None)	   
	cur.close ()
	return bottle.redirect("/")
	
@bottle.route("/<soba_tip:path>/<kapaciteta:int>/<zacetek:path>/<konec:path>/<cena:path>/rezerviraj_si_sobo/")
def rezervacija_sobe(soba_tip,kapaciteta,zacetek,konec,cena):
	"""Preveri, če je izbrana soba prosta in jo rezervira"""
	(uporabnisko_ime, ime, oid) = get_user()
	cur = baza.cursor()
	#Poiščemo v bazi izbrano prosto sobo
	cur.execute("""SELECT sid FROM soba LEFT JOIN termin ON soba.sid=termin.soba WHERE soba.tip=%s AND soba.kapaciteta=%s AND sid NOT IN 
	(SELECT sid FROM soba LEFT JOIN termin ON soba.sid=termin.soba WHERE soba.tip=%s AND soba.kapaciteta=%s AND 
	(((to_date(%s, 'YYYY-MM-DD') < to_date(to_char(termin.konec, 'YYYY-MM-DD'), 'YYYY-MM-DD')) AND 
	(to_date(%s, 'YYYY-MM-DD')>= to_date(to_char(termin.zacetek, 'YYYY-MM-DD'), 'YYYY-MM-DD'))) OR
	((to_date(%s, 'YYYY-MM-DD') <= to_date(to_char(termin.konec, 'YYYY-MM-DD'), 'YYYY-MM-DD')) AND 
	(to_date(%s, 'YYYY-MM-DD')> to_date(to_char(termin.zacetek, 'YYYY-MM-DD'), 'YYYY-MM-DD')))))""",
	[str(soba_tip),kapaciteta,str(soba_tip),kapaciteta,str(zacetek),str(zacetek),str(konec),str(konec)])
	(soba,)=cur.fetchone()
	## Če ne najde izbrane proste sobe, mu izpišemo, da ni ok:
	if cur.fetchone() is None:  
		bottle.template("main.html",
						uporabnisko_ime = uporabnisko_ime,
						oid=oid,
						soba_tip=soba_tip,
						cena=cena,
						sporocilo_o_prijavi_gosta=None,
						kapaciteta=kapaciteta,
						termin=rezervacija(oid),
						zacetek=None,
						konec=None,
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
						napaka1=None)
	
	# Če pa je izbrana soba prosta pa vnesemo rezervacijo v tabelo
	else:
		cur.execute("INSERT INTO termin (soba, zacetek, konec, oseba, popust) VALUES (%s, %s, %s, %s, %s)",
																				(cur.fetchone()[0], zacetek, konec, oid, 0))
		bottle.template("main.html",
						uporabnisko_ime = uporabnisko_ime,
						oid=oid,
						soba_tip=None,
						cena=None,
						sporocilo_o_prijavi_gosta=None,
						kapaciteta=None,
						termin=rezervacija_admin(),
						zacetek=None,
						konec=None,
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
						napaka1=None)	   
	cur.close ()
	return bottle.redirect("/")

#==============================Izračun cene===============================================

def informativni_izracun(zacetek, konec, postavka_soba):
	"""Izračuna ceno, ki jo bo moral gost plačati, če najame sobo - glede na sobo in čas."""
	cas_bivanja=(konec-zacetek).days
	cena=postavka_soba*cas_bivanja
	#predelujem tako, da bojo vikendi šteti

	return cena


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


## za prikaz posameznih rezervacij gosta --- to vidi administrator

	
######################################################################
# Glavni program

# priklopimo se na bazo
### priklopimo se na bazo postgresql; vnesi svoje up.ime in geslo:
#baza = psycopg2.connect(database='seminarska_tadejd', host='audrey.fmf.uni-lj.si', user='tadejd', password='stormymonday')
baza = psycopg2.connect(database='seminarska_tilenb', host='audrey.fmf.uni-lj.si', user='tilenb', password='59q9yipw')
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije

# poženemo strežnik na portu 8080, glej http://localhost:8080/
bottle.run(host='localhost', port=8080, reloader=True)

