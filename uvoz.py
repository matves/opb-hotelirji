#POVEZEMO SE NA BAZO

import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki
conn = psycopg2.connect(database='seminarska_tadejd', host='audrey.fmf.uni-lj.si', user='tadejd', password='stormymonday')
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

#IZ .csv IMPORTAMO PODATKE IN JIH ZAPISEMO V BAZO

import csv

#IMPORTAMO OSEBE
with open('oseba.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    for row in spamreader:
        cur.execute("""INSERT INTO oseba (ime,priimek,email,tel_st)
                       VALUES (%s,%s,%s,%s)""", (row[1],row[2],row[3],row[4]))

#IMPORTAMO SOBE
with open('soba.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter='\t',quotechar='|')
    for row in spamreader:
        cur.execute("""INSERT INTO soba (sid,tip,kapaciteta,cena)
                       VALUES (%s,%s,%s,%s)""", (row[0],row[1],row[2],row[3]))

#IMPORTAMO TERMINE
with open('termini.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    for row in spamreader:
        cur.execute("""INSERT INTO termin (soba,zacetek,konec,oseba,popust)
                       VALUES (%s,%s,%s,%s,%s)""", (row[0],row[1],row[2],row[3],row[4]))

#COMMITAMO IN ZAPREMO CURSOR IN BAZO
conn.commit()
cur.close()
conn.close()     
        
