import asyncio
import aiohttp
import json
import sqlite3

start_instance = "chaos.social"

async def get_peers(session, con, instance):
    peers = None
    success = False
    reason = "unknown"
    try:
        async with session.get("https://" + instance + "/api/v1/instance/peers") as r:
            peers = await r.json()
            success = True
        return instance, peers, success, reason
    except Exception as e:
        reason = e.__class__.__name__
        return instance, peers, success, reason

def store_peers(con, instance, peers):
    cur = con.cursor()
    cur.execute("INSERT INTO peers VALUES (?, ?)", (instance, json.dumps(peers)))
    con.commit()
    
def init(con):
    to_crawl = set()
    crawled_instances = set()

    cur = con.cursor()
    data = cur.execute("SELECT instance FROM broken_instances").fetchall()
    for row in data:
        crawled_instances.add(row[0])
    data = cur.execute("SELECT instance, peers FROM peers").fetchall()
    for x in data:
        crawled_instances.add(x[0])
    for instance, peers in data:
        peers_data = json.loads(peers)
        if peers_data:
            for peer in peers_data:
                if peer not in crawled_instances:
                    to_crawl.add(peer)
    
    if not to_crawl:
        to_crawl.add(start_instance)

    return to_crawl, crawled_instances


async def main(): 

    # DB
    con = sqlite3.connect("mastodon.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS peers(instance TEXT, peers TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS broken_instances(instance TEXT, reason TEXT)")

    to_crawl, crawled_instances = init(con)


    n = 100
    connector = aiohttp.TCPConnector(limit=n)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i in range(n):
            if to_crawl:
                instance = to_crawl.pop()
                tasks.append(asyncio.ensure_future(get_peers(session, con, instance)))
            else:
                break

        while to_crawl:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            tasks = list(pending)
            for task in done:
                instance, peers, success, reason = await task
                crawled_instances.add(instance)
                if success:
                    store_peers(con, instance, peers)
                    if peers:
                        for peer in peers:
                            if peer not in crawled_instances:
                                to_crawl.add(peer)
                else:
                    cur = con.cursor()
                    cur.execute("INSERT INTO broken_instances VALUES (?, ?)", (instance, reason))
                    con.commit()
                if to_crawl:
                    tasks.append(asyncio.create_task(get_peers(session, con, to_crawl.pop())))
            print(f"done={len(done)}, running={len(tasks)}, remaining={len(to_crawl)}")

asyncio.run(main())