# -*- coding: utf-8 -*-
import psycopg2
import time
import curses
now_date = "2015-09-10"
T = "3"
D = "100"
counting = 5

conn = psycopg2.connect(database="gis_test", user="postgres", password="123456", host="127.0.0.1", port="5432")
cursor = conn.cursor()
cursor.execute("drop materialized view IF EXISTS snapshot ;")
cursor.execute("drop table IF EXISTS L2 ;")

cursor.execute("create materialized view snapshot as (select * from dang where 確診日<='"+now_date+"' and 確診日+"+T+">'"+now_date+"');")
cursor.execute("create table L2 as (SELECT (array[p1.id,p2.id]) as pattern FROM snapshot AS p1, snapshot AS p2  where p1.id>p2.id and ST_DWithin(p1.geom::geography,p2.geom::geography,"+D+",false));")
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
#conn.commit()
#conn.close()

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
#	print x
	Pset = Pset.union(x)

print len(Pset)

############### done for STApriori ###############
cursor.execute("select * from snapshot order by cast(id as int) desc limit 1;")
for r in cursor:
	NewestCase = r[0]
	break

cursor.execute("select * from snapshot order by cast(id as int) limit 1;")
for r in cursor:
	OldestCase = r[0]
	break

while True:
	cursor.execute("REFRESH MATERIALIZED VIEW snapshot;")
	conn.commit()
	cursor.execute("select * from snapshot order by cast(id as int) desc limit 1;")
	for r in cursor:
		CheckPointNew = r[0]
		break
	cursor.execute("select * from snapshot order by cast(id as int) limit 1;")
	for r in cursor:
		CheckPointOld = r[0]
		break
		
	if NewestCase != CheckPointNew : # detect new point, rule match and update
		NeighberOfNewNode = set()
		cursor.execute("with N as (select id as Nid, geom as Ngeom from snapshot order by cast(id as int) desc limit 1) select id from snapshot cross join N where id!=Nid and ST_DWithin(geom::geography,Ngeom::geography,"+D+",false);")		
		for r in cursor:
			NeighberOfNewNode.add(r[0])
		
		# print set which match the rule
		for x in Llist[len(Llist)-1]:
			if x.issubset(NeighberOfNewNode):
				print x.union(set([CheckPointNew]))
		
		# update
		for i in range(len(Llist)-1):
			for x in Llist[i]:
				if x.issubset(NeighberOfNewNode):
					Llist[i+1].add(x.union(set([CheckPointNew])))
					
		print "ok"
		NewestCase = CheckPointNew
		
	else : # No new point, check if the oldest point expired
		if OldestCase != CheckPointOld:
			for x in Llist[0]: # remove from L2
				if OldestCase in x :
					Llist[0].remove(x)
			for i in range(1,len(Llist),1): # move from Ln to Ln-1
				for x in Llist[i]:
					if OldestCase in x :
						tmp = x - set([OldestCase])
						Llist[i].remove(x)
						Llist[i-1].add(tmp)

'''
stdscr = curses.initscr()
curses.cbreak()
stdscr.keypad(1)
stdscr.addstr(0,10,"Hit 'q' to quit\n")
stdscr.refresh()
key = ''
while key != ord('q'):
    if key ==  ord('a'):
        stdscr.clear()
        stdscr.addstr(0,10,"Hit 'q' to quit\n")
        stdscr.addstr(1, 20, detect_new())
    elif key ==  ord('b'):
        stdscr.clear()
        stdscr.addstr(0,10,"Hit 'q' to quit\n")
        stdscr.addstr(1, 20, " BCDEFGGG")
    key = stdscr.getch()
    stdscr.refresh()
curses.endwin()	
'''