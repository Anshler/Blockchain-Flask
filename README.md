# Blockchain With Flask

A simple project about Blockchain using Flask server

There are 2 servers, the ['server_default'](default/server_default.py) and the ['server'](server.py)

* Run the route ['/nodes/register']() of default first, then do the same for the 2nd server.
* Run ['/nodes']() to view all distributed urls
* Run ['/nodes/resolve']() to sync up chain
* Run ['/mine']() to add new blocks and save transactions to blockchain
* Run ['/transactions/new']() to add new transaction (POST request)

Reason for 2 servers: simulate real world situation, a blockchain is copied to every computer that runs it, every server contains the nodes (urls) of every other server so it can broadcast changes and sync up. 

So when you initialize a new server, you need a point of reference (seed) to initialize nodes and chain, which would be selected at random from a list of [known servers](server_info.yaml) (at the assumption that all blockchains are in sync, and thus, the same)

P/S: I still don't understand this thing so most codes are made up, not based on any actual principle