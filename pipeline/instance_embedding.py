import json
import sqlite3
from tqdm import tqdm
import struct
import graph_force
from utils import is_spam

MAPPING_JSON = "graph_mapping.json"
DATABASE = "mastodon.db"
GRAPH = "graph.bin"

# DB
con = sqlite3.connect("mastodon.db")
cur = con.cursor()

mapping = {}
i = 0
with open(GRAPH, "wb") as f:
    # create mapping
    for x in cur.execute("SELECT distinct(id), instance FROM instances WHERE last_checked IS NOT NULL"):
        if not is_spam(x[1]):
            mapping[x[0]] = i
            i += 1

    n = len(mapping)
    print("Embedding", n, "instances")
    ids = list(mapping.keys())

    f.write(struct.pack("i", n))
    for x in tqdm(cur.execute(f"""
        SELECT DISTINCT min(source_id, target_id), max(source_id, target_id)
        FROM peers
        WHERE source_id IN ({",".join(str(id) for id in ids)}) AND target_id IN ({",".join(str(id) for id in ids)})
    """)):
        if x[0] not in mapping or x[1] not in mapping:
            continue
        f.write(struct.pack("iif", mapping[x[0]], mapping[x[1]], 1))
json.dump(mapping, open(MAPPING_JSON, "w"))

print("Starting graph embedding. This may take a while...")
pos = graph_force.layout_from_edge_file(GRAPH, iter=20000, model="networkx_model")
json.dump(pos, open("positions_20000.json", "w"))