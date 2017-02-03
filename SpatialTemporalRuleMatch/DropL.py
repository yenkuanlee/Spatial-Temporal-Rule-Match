# -*- coding: utf-8 -*-
import psycopg2
counting = 10

conn = psycopg2.connect(database="gis_test", user="postgres", password="123456", host="127.0.0.1", port="5432")
cursor = conn.cursor()

for n in range(3,counting+1,1):
	try:
		cursor.execute("drop table L"+str(n)+";")
	except:
		print "done"
		break
conn.commit()
conn.close()
