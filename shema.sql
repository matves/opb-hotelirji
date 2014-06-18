CREATE TABLE oseba (
	oid	SERIAL PRIMARY KEY,
	ime	TEXT NOT NULL,
	priimek	TEXT NOT NULL,
	naslov	TEXT,
	email	TEXT,
	tel_st	TEXT NOT NULL,
	uporabnisko_ime TEXT UNIQUE,
	geslo TEXT
);


CREATE TABLE soba (
	sid		INTEGER PRIMARY KEY,
	cena	INTEGER NOT NULL,
	kapaciteta 	INTEGER NOT NULL,
	tip		TEXT NOT NULL
);	


CREATE TABLE termin (
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



