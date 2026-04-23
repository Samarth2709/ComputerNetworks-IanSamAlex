# A P2P Group Messaging Service on Blockchain

## Overview
We present a decentralized peer-to-peer (P2P) group messaging network where messages are recorded in an immutable blockchain. Each user is a node that communicates directly with other nodes, validates data, and maintains their own copy of the blockchain. A lightweight tracker node is used only for peer discovery and membership management.

## Node Types

### Tracker Node

The Tracker Node maintains the list of active peers. It supports three operations:

1) Registeration — a peer announces itself on startup, providing its address. The tracker adds it to the active list and pushes the updated list to all existing peers.
2) Querying— tracker provides the peer list when a peer requests the current active list.
3) Deregisteration — a peer announces a clean exit. The tracker removes it from the active list and pushes the updated list to all remaining peers.

### User Node

A User Node connects to other User Nodes to broadcast and receive messages, blocks, and peer information. It maintains a local copy of the blockchain, a pending message pool (mempool), and a local key pair for identity.

## The Network

### Peer Discovery

On startup, a User Node registers itself with the Tracker and receives the current active peer list in the response. It then establishes TCP connections to each peer in that list.

### Peer List Updates

Whenever a peer joins or deregisters, the Tracker pushes an updated peer list to all currently active peers. This ensures every peer always has an up-to-date view of the network.

### P2P Communication

All p2p communication uses TCP. When a peer has something to broadcast (a message or a block), it sends it directly to all known peers. Each receiving peer forwards it to their own peers, propagating the data through the network via flooding.

### Clean Exit

When a peer shuts down cleanly, it sends a Deregister message to the Tracker, and then the Tracker removes it and pushes the updated peer list to all remaining peers.

## User Identity

Each User Node generates an RSA public/private key pair on startup. The public key will be the node's cryptographic identity for the network.

Messages are signed with the sender's private key. Recipients verify the signature using the sender's public key, which is included in every message.

## Blockchain Design

### Block Structure

Each block contains the following fields:

1. `index` — Position of the block in the chain (0 for genesis block)
2. `timestamp` — Unix timestamp of when the block was mined
3. `messages` — List of messages included in this block
4. `previous_hash` — SHA-256 hash of the preceding block
5. `nonce` — Value iterated during mining to satisfy the difficulty target
6. `hash` — SHA-256 hash of all fields above

### Mining

Mining is a proof-of-work process. A valid block's SHA-256 hash must begin with a fixed number of leading zeros (the difficulty). This will be satisfied by iterating the nonce field. The difficulty will be determined by a fixed constant (e.g. 4 leading zeros), shared by all peers.

Mining is triggered by message count. A peer will begin mining once its mempool reaches a threshold number of pending messages

### Block Verification

A received block is accepted only if and only if it passes the following requirmenets

1. Hash is consistent with the blocks components. The hash is recomputed by hashing the contents of the block and its checked if it matches the block's provided hash.
2. Chain contiues fromt the previous block. This is check by checkign if the previous hash matches the hash of the local chain's last block.
3. Proof of work/ difficulty verification. The hash must starts with the required number of leading zeros.

A block that fails any of these requirements is discarded.

### Fork Resolution

To resolve forks we will use the the longest chain wins resolution rule. When a peer receives a block that conflicts with its current chain, it compares lengths and switches to the longer one.

When switching chains, the senders of orphaned messages (in the discarded branch but not the winning branch) are notified to rebroadcast into the mempool.

### Catch-Up (Joining a Live Network)

On join, a peer requests the full chain from one known peer, verifies it block by block from genesis, then adopts it as its local chain.

## Data Structures

### Tracker Messages

- On registration — sent by a peer to announce itself to tracker; includes its `type`, `address`, and `pubkey`
- Peer list sent — sent by the tracker in response; includes its `type` and a list of known peers, each with an `address` and `pubkey`
- On deregistration of peer — sent by a peer on departure; includes its `type` and `address`

### Message

- sender_username — the display name of the sender
- sender_pubkey — the sender's public key, used to verify authenticity
- content — the plaintext body of the message
- timestamp — when the message was created
- signature — covers sender_username + sender_pubkey + content + timestamp

### Block

- index — position of the block in the chain (0 for genesis)
- timestamp — when the block was mined
- messages — the list of messages bundled into this block
- previous_hash — SHA-256 hash of the preceding block
- nonce — iterated during mining to satisfy the difficulty target
- hash — SHA-256 hash of all fields above

## Demo Application

The demo application is a group chat interface where every sent message is eventually recorded on the blockchain. Users type messages at the command line. On send, the message is signed, broadcast to all peers, and added to their mempools. Once a peer's mempool threshold is reached, it mines a block containing those messages and broadcasts the block. All peers then display confirmed messages in chain order.

Reading the chat history is equivalent to reading all message fields from every block in the chain, in block order.

