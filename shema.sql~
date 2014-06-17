CREATE TABLE IF NOT EXISTS oseba (
	oid	INTEGER PRIMARY KEY AUTOINCREMENT,	
	ime	TEXT NOT NULL,
	priimek	TEXT NOT NULL,
	naslov	TEXT,
	email	TEXT NOT NULL,
	tel_st	TEXT NOT NULL,
	uporabnisko_ime TEXT NOT NULL UNIQUE,
	geslo TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS soba (
	sid		INTEGER PRIMARY KEY,
	cena	INTEGER NOT NULL,
	kapaciteta 	INTEGER NOT NULL,
	tip		TEXT NOT NULL
);	


CREATE TABLE IF NOT EXISTS termin (
soba	INTEGER NOT NULL
	REFERENCES soba(sid)
	ON UPDATE CASCADE
	ON DELETE RESTRICT,
zacetek DATE NOT NULL,
konec	DATE NOT NULL
        CHECK(zacetek < konec),
oseba	INTEGER NOT NULL
	REFERENCES oseba(oid),
popust INTEGER,
PRIMARY KEY (soba, zacetek, konec)
);

CREATE VIEW rezervirane_sobe AS 
SELECT sid, oseba, cena AS cena_teden_brez_popusta, kapaciteta, tip, zacetek, konec FROM soba JOIN termin ON soba.sid=termin.soba



