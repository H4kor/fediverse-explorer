import asyncio
import time
import aiohttp
import json
import sqlite3

START_INSTANCE = "chaos.social"
CONCURRENT_REQUESTS = 100
DB_NAME = "mastodon.db"

INSTANCE_CACHE = {}

SUBDOMAIN_SPAM = [
    ".hwl.li",
    ".skorpil.cz",
    ".cispa.saarland",
    ".glaceon.social",
    ".egirls.gay",
    ".monads.online",
    ".pixie.town",
    ".websec.saarland",
    ".gab.best",
]

def is_spam(instance):
    for spam in SUBDOMAIN_SPAM:
        if spam in instance:
            print("spam", instance)
            return True
    return False

async def get_instance_data(session, con, instance):
    peers = None
    error = None
    try:
        async with session.get("https://" + instance + "/api/v1/instance/peers") as r:
            peers = await r.json()
            success = True
        return instance, peers, error
    except Exception as e:
        error = e.__class__.__name__
        return instance, peers, error

def init(con):
    to_crawl = set()
    crawled_instances = set()

    cur = con.cursor()
    data = cur.execute("SELECT instance FROM broken_instances").fetchall()
    for row in data:
        crawled_instances.add(row[0])
    data = cur.execute("SELECT id, instance FROM instances WHERE last_checked IS NOT NULL").fetchall()
    for x in data:
        INSTANCE_CACHE[x[1]] = x[0]
        crawled_instances.add(x[1])
    data = cur.execute("SELECT id, instance FROM instances WHERE last_checked IS NULL").fetchall()
    for instance in data:
        INSTANCE_CACHE[instance[1]] = instance[0]
        if instance[1] not in crawled_instances and not is_spam(instance):
            to_crawl.add(instance[1])
    
    if not to_crawl:
        to_crawl.add(START_INSTANCE)

    return to_crawl, crawled_instances

def get_or_create_instance(con, instance_name):
    if is_spam(instance_name):
        return None
    if instance_name is None:
        return None
    if instance_name in INSTANCE_CACHE:
        return INSTANCE_CACHE[instance_name]

    row = con.execute("SELECT id FROM instances WHERE instance=?", (instance_name,)).fetchone()
    print(instance_name, row)
    if row is None:
        con.execute("INSERT INTO instances(instance) VALUES (?)", (instance_name,))
        con.commit()
        row = con.execute("SELECT id FROM instances WHERE instance=?", (instance_name,)).fetchone()
    INSTANCE_CACHE[instance_name] = row[0]
    return row[0]

def store_instance(con, instance_name, peers):
    instance = get_or_create_instance(con, instance_name)
    if instance is None:
        return
    con.execute("UPDATE instances SET last_checked=? WHERE id=?", (int(time.time()), instance))

    for peer_name in peers:
        peer = get_or_create_instance(con, peer_name)
        if peer is None:
            continue
        con.execute("INSERT OR IGNORE INTO peers(source_id, target_id) VALUES (?, ?)", (instance, peer))
    con.commit()

async def main(): 
    # DB
    con = sqlite3.connect(DB_NAME)
    con.execute("CREATE TABLE IF NOT EXISTS instances(id INTEGER primary key autoincrement, instance TEXT unique, last_checked INTEGER)")
    con.execute("CREATE TABLE IF NOT EXISTS peers(source_id INTEGER, target_id INTEGER, UNIQUE(source_id, target_id))")
    con.execute("CREATE TABLE IF NOT EXISTS broken_instances(instance TEXT primary key, reason TEXT)")
    to_crawl, crawled_instances = init(con)

    connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        while to_crawl:
            while to_crawl and len(tasks) < CONCURRENT_REQUESTS:
                instance = to_crawl.pop()
                tasks.append(asyncio.ensure_future(get_instance_data(session, con, instance)))

            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            tasks = list(pending)
            for task in done:
                instance, peers, error = await task
                crawled_instances.add(instance)
                if error is None and peers is not None and isinstance(peers, list):
                    store_instance(con, instance, peers)
                    for peer in peers:
                        if peer not in crawled_instances and not is_spam(peer):
                            to_crawl.add(peer)
                else:
                    con.execute("INSERT OR REPLACE INTO broken_instances(instance, reason) VALUES (?, ?)", (instance, error))
                    con.commit()
            print(f"done={len(done)}, running={len(tasks)}, remaining={len(to_crawl)}")

if __name__ == "__main__":
    asyncio.run(main())