import json
import sqlite3

# DB
con = sqlite3.connect("mastodon.db")

con.execute('create index if not exists instances_instance_index on instances(instance)')
con.commit()
con.execute('create index if not exists instance_id_index on instances(id)')
con.commit()
con.execute('create index if not exists peers_source_target_index on peers(source_id, target_id)')
con.commit()