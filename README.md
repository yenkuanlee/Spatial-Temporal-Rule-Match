# input
```
Rule (time, distance, counting)
Dataset (ID, 發生時間, 經度, 緯度)
	累積的data
	持續發生的event : Streaming data
Objective
	回傳累積data中符合rule的點集合pattern
	online 判斷新的event是否有match rule
Output
	所有符合rule的點集合
```

# 方法 (Sinlge)
- 0. 資料前處理
```
Dataset in postgresql
經緯度 to geom by postgis
```
- 1. STapriori rule match
```
A. 取得snapshot
	取得所有符合時間條件(time)的events
	
B. L2 from snapshot
	從snapshot events中算出符合距離條件(< distance)的任兩點為L2
	if counting==2 : then L2 set is 答案
	
C.From Ln-1 to Ln until n=counting
	http://140.116.247.115:10380/doku.php?id=spatial_temporal_rule_match:包含圓證明n個點中認兩點距離小於d, 則存在直徑d圓可包含n個點
	Ln-1 to Ln：比對Ln-1 set中任兩pattern(x,y) 是否可以長成 Ln       // n = 3 to counting
	U = union(x,y)
	if len(U==n) :
		I = intersection(x,y)
		if (U-I) in Ln-1 set :
			add U to Ln set
			return Lcounting set as answers  set
```
- 2. Streaming computing
```
不斷偵測是否有過期的點(不符合時間條件)要刪除
snapshot是持續再更新的
若snapshot中最old的點時間不再符合rule, 代表此點過期
若偵測到event e為過期點, 則更新index
for i = 2 to n ：
	for pattern in Li ：
		if pattern.contains(e) ：
			Li.remove(pattern)
發生新的event快速判斷是否match rule, 若符合則需更新index
若發生新的event e
// check
flag = False
NeighberOfNewNode ：從snapshot中抓出所有與e距離小於distance的event
for pattern in Ln-1：
	if pattern in NeighberOfNewNode：       // Ln-1中存在一pattern, 此pattern內所有點距離e小於distance
		flag = True
		return flag        // 此pattern存在則e符合rule, 立即回傳 True
// update
if flag：        // if true then update index
	for i = 2 to n：
		for pattern in Li：
			if pattern in NeighberOfNewNode：
				Li+1.add(union(pattern, e))
	return Ln        // 新的answers set
```

# 方法 (Multi)
- 0. 資料前處理
```
同single
```
- 1. STapriori rule match
```
A. 取得snapshot
	每條rule會有自己的snapshot
	每個snapshot是一個db中的materialized view, 以rule id 命名區分
	
B. L2 from snapshot
	所有rules的snapshot彙整成一個L2 index
	L2是HashMap的型態, key是two pattern, value是對應符合的rules
	
C. CountingTable (hashmap)
	一個lookup table, 紀錄每一階層要處理的rule
	例如某條rule是(3天, 100公尺, 3), 則L4不會有此條rule (是不需要紀錄在L4, 這裡觀念很容易搞錯)
	此rule會被紀錄到CountingTable[2], CountingTable[3]
	CountingTable用途是處理Ln時候快速pruning
	
D. From Ln-1 to Ln until n=counting
	Ln的型態與L2相同為HashMap, 紀錄n pattern以及對應符合的rules
	比對Ln-1 set中任兩pattern(x,y)        // n = 3 to max_count
	先比對Ln-1[x]和Ln-1[y]以及CountingTable[n] 是否有交集的rules
	沒有的話就結束比對(x,y)
	有的話才比對(x,y)pattern本身
	再比對Ln-1 set中任兩pattern(x,y) 是否可以長成 Ln
	可以的話, 令rule(x,y) = Intersection(Ln-1[x], Ln-1[y], L2[union(x,y)-intersection(x,y)])
	rule(x,y)非空才能加入Ln[union(x,y)] = rule(x,y)
	
	pseudo code (比對Ln-1中任兩pattern (x,y))
	RuleIntersection = Intersection(Ln-1[x],Ln-1[y],CountingTable[n])
	if len(RuleIntersection) is not 0：
		U = union(x,y)
		if len(U==n) :
			I = intersection(x,y)
			if (U-I) in Ln-1 set :
				RuleIntersection = intersection(RuleIntersection,L2[U-I])
				if len(RuleIntersection) is not 0 ：
					add U to Ln set
					Ln[U] = RuleIntersection

	回傳答案
	for n = 2 to max_count：
		for pattern in Ln ：
			for ruleID in Ln[pattern]：
				if rules[ruleID][counting] == n：
					print pattern,ruleID
```
- 2. Streaming computing
```
A. 偵測過期點並刪除
	偵測過期點
	所有snapshot中最old的點為觀察目標, 紀錄為 OldestCase
	當此點不符合任一條rule的時間條件, 代表過期
	刪除過期點並更新 index
	for n = 2 to max_count：
		for pattern in Ln：
			if OldestCase in pattern：
				Ln.remove(pattern)
	更新完index後要更新OldestCase, 繼續偵測
	
B. 偵測新event並回傳更新
	偵測新event
	所有snapshot中最new的點紀錄為NewestCase
	若更新snapshot前後NewestCase值有所改變, 代表有新event
	發生新event, 判斷此event有符合哪些rule, 有的話則更新index
	
	for each rule
	大致上同single
	與single不同的地方 :
		Ln的資料結構不同(是hashmap), 所以要加入rule作為value
		Li+1[(union(pattern, e))].add(rule)
```
