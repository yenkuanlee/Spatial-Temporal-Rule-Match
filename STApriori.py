# -*- coding: utf-8 -*-
import psycopg2

now_date = "2015-09-10"
T = "3"
D = "100"
counting = 12

conn = psycopg2.connect(database="gis_test", user="postgres", password="123456", host="127.0.0.1", port="5432")
cursor = conn.cursor()
try:
	cursor.execute("drop table L2 ;")
except:
	print "L2 not exist"
cursor.execute("create table L2 as (with snapshot as (select id,geom from dang where 確診日<='"+now_date+"' and 確診日+"+T+">'"+now_date+"') SELECT (array[p1.id,p2.id]) as pattern FROM snapshot AS p1, snapshot AS p2  where p1.id>p2.id and ST_DWithin(p1.geom::geography,p2.geom::geography,"+D+",false));")
#cursor.execute("create table L2 as (with snapshot as (select id,geom from dang where 確診日<='"+now_date+"' and 確診日+"+T+">'"+now_date+"') SELECT (array[p1.id,p2.id]) as pattern FROM snapshot AS p1, snapshot AS p2  where p1.id>p2.id and ST_Distance_Sphere(p1.geom,p2.geom) < "+D+");")
print "L2 is done"
conn.commit()
#for n in range(3,counting+1,1):
#	cursor.execute("create table L"+str(n)+" as (with C as (select distinct (select ARRAY(SELECT UNNEST(t1.pattern) UNION SELECT UNNEST(t2.pattern))) as pattern from L"+str(n-1)+" as t1 cross join L"+str(n-1)+" as t2) select * from c  where array_length(pattern,1)="+str(n)+");")
#	print "L"+str(n)+" is done"
#	conn.commit()


L2Set = set()
cursor.execute("select * from L2;")
for r in cursor:
	L2Set.add(frozenset(r[0]))
conn.commit()
conn.close()

Llist = list()
Llist.append(L2Set)

for n in range(3,counting+1,1):
	DoneList = set()
	Ln1Set = set()
	LnSet = Llist[len(Llist)-1]
	if len(LnSet)==0 : break
	for x in LnSet:
		for y in LnSet:
			U = x.union(y)
			if len(U)==n:
				if U in DoneList : continue
				else : DoneList.add(U)
				tmp = (x.difference(y)).union(y.difference(x))
				if tmp in L2Set:
					Ln1Set.add(U)
	Llist.append(Ln1Set)
	print "L"+str(n)+" is done"

	
Pset = set()
for x in Llist[counting-2]:
	print x
	Pset = Pset.union(x)

print len(Pset)