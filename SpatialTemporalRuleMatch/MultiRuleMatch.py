# -*- coding: utf-8 -*-
import psycopg2
import time

now_date = "2015-08-31"
RuleList = list()
RuleList.append(['3','30',5])
RuleList.append(['1','100',4])
RuleList.append(['2','50',3])

def MaxCount(input):
	max = 0
	for x in input:
		if x[2] > max:
			max = x[2]
	return max
	
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
	cursor.execute("drop materialized view IF EXISTS snapshot ;")
	cursor.execute("drop table IF EXISTS L2 ;")
	cursor.execute("create materialized view snapshot as (select * from dang where 確診日<='"+now_date+"' and 確診日+"+T+">'"+now_date+"');")
	cursor.execute("create table L2 as (SELECT (array[p1.id,p2.id]) as pattern FROM snapshot AS p1, snapshot AS p2  where p1.id>p2.id and ST_DWithin(p1.geom::geography,p2.geom::geography,"+D+",false));")
	conn.commit()
	#L2Dict = dict()
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
	return L2Dict
	
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

for x in Llist[len(Llist)-1].keys():
	print x,Llist[len(Llist)-1][x]