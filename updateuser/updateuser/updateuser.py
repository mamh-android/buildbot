#!/usr/bin/python2.6
#1.connect the database
#2.set a cursor
#3.delete all the information in the database
#4.read users information from the file uses.txt 
#5.split the users information(string) into oneuser information
#6.insert the user into the database
#7.close cursor
#8.close database
###because the string end with semicolon,so the last one is blank
###so we should not insert the last one
#
import sqlite3 as sqlite
conn = sqlite.connect('/home/buildfarm/buildbot/sandbox/master/state.sqlite')
#conn.text_factory = str
curr = conn.cursor()
curr.execute("delete from user_real")
f = open('users.txt','r')
allusers = f.read()
allusers = allusers.split(';')
for user in allusers[0 : -1]:
    oneuser = user.split(',')
    print oneuser[1],oneuser[0]
    curr.execute("insert into user_real values(?,?,?)", [oneuser[1],oneuser[0], oneuser[1] + '@marvell.com'])
conn.commit()
curr.close()
conn.close()
