# A P2P Group Messaging Service on Blockchain

## Overview
We present a decentralized peer-to-peer (P2P) group messaging network where messages are recorded in an immutable blockchain. Each user is a node that communicates directly with other nodes, validates data, and maintains their own copy of the blockchain. A lightweight tracker node is used only for the initial peer discovery.

## Node Types
### Tracker Node

The Tracker Node keeps track of an active users list. A user can register itself as a new node and query the active users list.

### User Node

A User Node connects to other User Nodes to broacast and receive messages, blocks, and peer information. It can operate on its local blockchain such as update, verify, and create new blocks.

## The Network
### Peer Discovery

A User Node starts up by querying the active users list from the Tracker Node.

### Peer-to-Peer Messaging

A User Node wishing to send a message would broadcast this to its peers, who would then broadcast to their peers and so on. Upon receiving a message, it is cached locally.

### Blockchain Operations

A timer with random countdown is maintained by each node. When the timer fires, it creates a block and broadcast that to its peers, who would then broadcast to their peers and so on. Upon receiving a block, a User Node must verify the hashes on the block.

TODO: strategy to resolve fork

TODO: strategy to catch up

## Work Partition

TODO


