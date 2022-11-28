## [Enter the Fediverse Explorer](https://h4kor.github.io/fediverse-explorer/)

This is a small personal project to visualize the Fediverse.

The Viewer shows a point cloud of Mastodon instances. The embedding is done with a spring model, where peering instances are placed close to each other.


## How to use

1. `python pipeline/instance_scraper.py` to create the SQLite database with all instances and peers.
    * This will take a while, and can be interrupted and resumed.
2. `python pipeline/add_index.py` to add an index to the database. This will speed up the next steps
3. `python pipeline/embed_instances.py` to embed the instances in a 2D space. This will take a while (few hours on my machine).
    * creates a `graph.bin` file, which is a binary file containing the graph of the instances.
    * creates a `graph_mapping.json` file, which is a mapping from instance id to index in the graph.
    * creates an `embedding.json` file.