# -*- coding: utf-8 -*-
import psycopg2
import time

now_date = "2015-08-31"
RuleList = list()
RuleList.append(['2','30',5])
RuleList.append(['3','60',3])
RuleList.append(['5','50',3])

def MaxCount(input):
	max = 0
	for x in input:
		if x[2] > max:
			max = x[2]
	return max
	
def MaxTime(input):
	max = 0
	rid = ""
	for i in range(len(input)):
		if int(input[i][0]) > max:
			max = int(input[i][0])
			rid = "r"+str(i+1)
	return rid
	
def LookUpRuleTable(input):
	tmp = dict()
	for i in range(len(input)):
		rid = "r"+str(i+1)
		for j in range(2,input[i][2]+1,1):
			try:
				tmp[j].add(rid)
			except:
				s = set()
				s.add(rid)
				tmp[j] = s
	return tmp

def RL2(rid,input,L2Dict):
	T = input[0]
	D = input[1]
	conn = psycopg2.connect(database="dang", user="postgres", password="123456", host="127.0.0.1", port="5432")
	cursor = conn.cursor()
	cursor.execute("drop materialized view IF EXISTS snapshot_"+rid+" ;")
	cursor.execute("drop table IF EXISTS L2 ;")
	cursor.execute("create materialized view snapshot_"+rid+" as (select * from dang where 確診日<='"+now_date+"' and 確診日+"+T+">'"+now_date+"');")
	cursor.execute("create table L2 as (SELECT (array[p1.id,p2.id]) as pattern FROM snapshot_"+rid+" AS p1, snapshot_"+rid+" AS p2  where p1.id>p2.id and ST_DWithin(p1.geom::geography,p2.geom::geography,"+D+",false));")
	conn.commit()
	cursor.execute("select * from L2;")
	for r in cursor:
		l = list()
		for w in r[0]:
			l.append(str(w))
		try:
			L2Dict[frozenset(l)].add(rid)
		except:
			tmp = set()
			tmp.add(rid)
			L2Dict[frozenset(l)] = tmp
	conn.close()
	return L2Dict
	
def GetNeighbor(Rlist):
	Neighbor = dict()
	for i in range(len(Rlist)):
		D = Rlist[i][1]
		rid = "r"+str(i+1)
		NeighberOfNewNode = set()
		conn = psycopg2.connect(database="dang", user="postgres", password="123456", host="127.0.0.1", port="5432")
		cursor = conn.cursor()
		#cursor.execute("REFRESH MATERIALIZED VIEW snapshot_"+rid+";")
		cursor.execute("with N as (select id as Nid, geom as Ngeom from snapshot_"+rid+" order by cast(id as int) desc limit 1) select id from snapshot_"+rid+" cross join N where id!=Nid and ST_DWithin(geom::geography,Ngeom::geography,"+D+",false);")	
		conn.commit()
		for r in cursor:
			NeighberOfNewNode.add(r[0])
		Neighbor[i+1] = frozenset(NeighberOfNewNode)
		conn.close()
	return Neighbor

def Refresh(length):
	conn = psycopg2.connect(database="dang", user="postgres", password="123456", host="127.0.0.1", port="5432")
	cursor = conn.cursor()
	for i in range(length):
		cursor.execute("REFRESH MATERIALIZED VIEW snapshot_r"+str(i+1)+";")
	conn.commit()
	conn.close()
	
def IfPointIn(newest):
	conn = psycopg2.connect(database="dang", user="postgres", password="123456", host="127.0.0.1", port="5432")
	cursor = conn.cursor()
	cursor.execute("REFRESH MATERIALIZED VIEW snapshot_r1;")
	conn.commit()
	cursor.execute("select * from snapshot_r1 order by cast(id as int) desc limit 1;")
	for r in cursor:
		CheckPointNew = r[0]
		break
	conn.close()
	if CheckPointNew == newest:
		return False
	return True
	
def IfPointOut(oldest):
	Orid = MaxTime(RuleList)
	conn = psycopg2.connect(database="dang", user="postgres", password="123456", host="127.0.0.1", port="5432")
	cursor = conn.cursor()
	cursor.execute("REFRESH MATERIALIZED VIEW snapshot_"+Orid+";")
	conn.commit()
	cursor.execute("select * from snapshot_"+Orid+" order by cast(id as int) limit 1;")
	for r in cursor:
		CheckPointOld = r[0]
		break
	conn.close()
	if CheckPointOld == oldest:
		return False
	return True

def GetNewestCase():
	conn = psycopg2.connect(database="dang", user="postgres", password="123456", host="127.0.0.1", port="5432")
	cursor = conn.cursor()
	cursor.execute("select * from snapshot_r1 order by cast(id as int) desc limit 1;")
	for r in cursor:
		NewestCase = r[0]
		break
	conn.close()
	return NewestCase
	
def GetOldestCase():
	Orid = MaxTime(RuleList)
	conn = psycopg2.connect(database="dang", user="postgres", password="123456", host="127.0.0.1", port="5432")
	cursor = conn.cursor()
	cursor.execute("select * from snapshot_"+Orid+" order by cast(id as int) limit 1;")
	for r in cursor:
		OldestCase = r[0]
		break
	conn.close()
	return OldestCase

def AddNewPoint(Llist,Neighber,new_point,rindex,counting):
	rid = 'r'+str(rindex+1)
	for i in range(counting-2) : # add to Ln
		for x in Llist[i]:
				if x.issubset(Neighber):
					tmp = x.union(set([new_point]))
					if tmp in Llist[i+1] :
						Llist[i+1][tmp] = frozenset(set(Llist[i+1][tmp]).union(set([rid])))
					else:
						Llist[i+1][tmp] = frozenset([rid])
	for x in Neighber: # add to L2
		tmp = frozenset([x,new_point])
		if tmp in Llist[0]:
			Llist[0][tmp] = frozenset(set(Llist[0][tmp]).union(set([rid])))
		else :
			Llist[0][tmp] = frozenset([rid])
	return Llist
			
L2Dict = dict()
for i in range(len(RuleList)):
	rid = "r"+str(i+1)
	L2Dict = RL2(rid,RuleList[i],L2Dict)

Llist = list()
Llist.append(L2Dict)
CountingTable = LookUpRuleTable(RuleList)
print CountingTable
# from L3 to Ln
for n in range(3,MaxCount(RuleList)+1,1):
	DoneList = set()
	Ln1Dict = dict()
	LnDict = Llist[len(Llist)-1]
	if len(LnDict.keys())==0 : break
	for x in LnDict.keys():
		for y in LnDict.keys():
			RuleIntersection = LnDict[x].intersection(LnDict[y]).intersection(CountingTable[n])
			if len(RuleIntersection) == 0 :
				continue
			U = x.union(y)
			if len(U)==n:
				if U in DoneList : continue
				else : DoneList.add(U)
				tmp = (x.difference(y)).union(y.difference(x))
				if tmp in L2Dict.keys():
					RuleIntersection = RuleIntersection.intersection(L2Dict[tmp])
					if len(RuleIntersection) == 0 :
						continue
					Ln1Dict[frozenset(U)] = RuleIntersection
	Llist.append(Ln1Dict)

################################################################################
print "start listen"
NewestCase = GetNewestCase()
OldestCase = GetOldestCase()

flag = False
while True:
	#if flag : break
	if IfPointIn(NewestCase) :
		print 'find new point'
		Refresh(len(RuleList))
		NewestCase = GetNewestCase()
		Neighber = GetNeighbor(RuleList)
		for i in range(len(RuleList)):
			if flag : break
			rid = "r"+str(i+1)
			index = RuleList[i][2]-2
			Nset = Neighber[i+1]
			for x in Llist[index] :
				if flag : break
				if rid not in Llist[index][x]:
					continue
				if x.issubset(Nset):
					print 'match'
					for j in range(i,(len(RuleList)),1):
						Nei = Neighber[j+1]
						Llist = AddNewPoint(Llist,Nei,NewestCase,j,RuleList[j][2])
						
					#for x in Llist[1]:
					#	if set([NewestCase]).issubset(x):
					#		print x,Llist[1][x]
							
					flag = True
					break
					
	if IfPointOut(OldestCase):
		print 'find old point'
		DelDict = dict()
		for i in range(len(Llist)):
			for y in Llist[i] :
				if OldestCase in y:
					DelDict[y] = i
		for x in DelDict:
			del Llist[DelDict[x]][x]
		print len(Llist[1])
		Refresh(len(RuleList)) # have to ???
		OldestCase = GetOldestCase()
		print OldestCase