# -*- coding: utf-8 -*-
import psycopg2
counting = 10

conn = psycopg2.connect(database="gis_test", user="postgres", password="123456", host="127.0.0.1", port="5432")
cursor = conn.cursor()
cursor.execute("select * from snapshot order by cast(id as int) desc limit 1;")

for r in cursor:
	print r[0]
	break

cursor.execute("select * from snapshot order by cast(id as int) limit 1;")
for r in cursor:
	print r[0]
	break
	
conn.commit()
conn.close()
