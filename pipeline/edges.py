import json
import sqlite3

# DB
con = sqlite3.connect("mastodon.db")
cur = con.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS edges (source integer, target integer, UNIQUE(source, target))")

instances = {
    x[1]: x[0] for x in cur.execute("SELECT id, instance FROM instances").fetchall()
}

for id, instance, peer in cur.execute("SELECT id, instance, peers FROM instances").fetchall():
    peers = json.loads(peer)
    try:
        cur.executemany(
            "INSERT INTO edges (source, target) VALUES (?, ?)",
            [(id, instances[p]) for p in peers if p in instances])
    except sqlite3.IntegrityError:
        pass
    con.commit()

