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

CREATE VIEW pregled_rezervacij AS
SELECT oseba.oid, oseba.ime, oseba.priimek, oseba.tel_st, termin.soba, soba.kapaciteta, soba.tip, termin.zacetek, termin.konec,  
round((soba.cena*(count(dnevi.serija))+1.2*soba.cena*(termin.konec-termin.zacetek-count(dnevi.serija)))*(100-termin.popust)*1./100.,2) as znesek 
FROM oseba LEFT JOIN termin ON termin.oseba=oseba.oid 
JOIN soba ON termin.soba=soba.sid
LEFT JOIN 
(SELECT oseba, zacetek, generate_series(zacetek::date, (konec-1)::date, '1 day') as serija FROM termin days) as dnevi
ON termin.zacetek=dnevi.zacetek AND termin.oseba=dnevi.oseba
WHERE extract('dow' from serija) not in (5,6)
GROUP BY oseba.oid,oseba.ime,oseba.priimek, oseba.tel_st,termin.soba, soba.kapaciteta, soba.tip,soba.cena,termin.zacetek,termin.popust, termin.konec
ORDER BY termin.zacetek;

