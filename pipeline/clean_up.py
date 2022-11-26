import json
import sqlite3

# DB
con = sqlite3.connect("mastodon.db")
cur = con.cursor()

cur.execute("CREATE INDEX IF NOT EXISTS peers_instance ON peers(instance)")

# remove instances withouth peers
cur.execute("DELETE FROM peers WHERE peers not like '[%'")

# remove duplicated
cur.execute("""
DELETE from peers 
where EXISTS (
	select 1 from peers p2
	where peers."instance" = p2."instance" 
	and peers.rowid > p2.rowid
)
""")

cur.execute("""
DELETE from edges
where source not in (select instance from peers)
or target not in (select instance from peers)
""")

cur.execute("""
DELETE from edges
where source = target
""")

# vacuum
con.commit()
cur.execute("VACUUM")
con.commit()