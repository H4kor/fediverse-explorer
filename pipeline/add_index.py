import json
import sqlite3

# DB
con = sqlite3.connect("mastodon.db")
cur = con.cursor()

cur.execute('create table instances(id integer primary key autoincrement, instance text unique, peers text)')
cur.execute('insert into instances(instance, peers) select instance, peers from peers')
con.commit()