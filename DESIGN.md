# A P2P Decentralized Voting System on Blockchain

## Problem Statement

Voting systems have a fundamental trust problem. Centralized systems require voters to trust a single authority to count votes honestly, prevent double-voting, and protect the integrity of the ballot. These systems are vulnerable to insider manipulation, single points of failure, and lack of public auditability. Voters have no way to independently verify that their vote was counted correctly or that the final tally is accurate.

## How Our System Solves It

We present a decentralized peer-to-peer (P2P) voting network where votes are recorded in an immutable blockchain. Each participant is a node that communicates directly with other nodes, validates transactions, and maintains their own copy of the blockchain. No single party controls the vote count — the chain is the ground truth, and anyone can audit it.

The system solves the core problems as follows:

- **Double-voting prevention** — each voter has a unique public key identity. Nodes reject any vote transaction from a public key that already appears in the confirmed chain.
- **Voter eligibility** — only voters registered by the Tracker (the election authority) can cast valid votes. Unregistered votes are rejected by all nodes.
- **Auditability** — anyone can replay the chain from genesis and independently compute the tally. There is no black box.
- **Tamper resistance** — altering any past vote requires re-mining all subsequent blocks and outpacing the rest of the network, which is computationally infeasible.

A lightweight tracker node is used only for peer discovery, membership management, and voter registration authority.

## Node Types

### Tracker Node

The Tracker Node maintains the list of active peers and serves as the voter registration authority. It supports four operations:

1. **Registration** — a peer announces itself on startup, providing its address and public key. The tracker adds it to the active list and pushes the updated list to all existing peers.
2. **Querying** — the tracker provides the peer list when a peer requests the current active list.
3. **Deregistration** — a peer announces a clean exit. The tracker removes it from the active list and pushes the updated list to all remaining peers.
4. **Voter Registration** — the tracker issues a signed `RegistrationTx` that certifies a voter's public key as eligible to vote. Only `RegistrationTx` transactions signed by the Tracker are accepted by the network.

### User Node

A User Node connects to other User Nodes to broadcast and receive transactions, blocks, and peer information. It maintains a local copy of the blockchain, a pending transaction pool (mempool), and a local RSA key pair for identity.

## The Network

### Peer Discovery

On startup, a User Node registers itself with the Tracker and receives the current active peer list in the response. It then establishes TCP connections to each peer in that list.

### Peer List Updates

Whenever a peer joins or deregisters, the Tracker pushes an updated peer list to all currently active peers. This ensures every peer always has an up-to-date view of the network.

### P2P Communication

All P2P communication uses TCP. When a peer has something to broadcast (a transaction or a block), it sends it directly to all known peers. Each receiving peer forwards it to their own peers, propagating the data through the network via flooding.

### Clean Exit

When a peer shuts down cleanly, it sends a Deregister message to the Tracker. The Tracker removes it and pushes the updated peer list to all remaining peers.

## User Identity

Each User Node generates an RSA public/private key pair on startup. The public key is the node's cryptographic identity on the network.

Transactions are signed with the sender's private key. Recipients verify the signature using the sender's public key, which is included in every transaction.

## Transaction Types

### RegistrationTx

Records that a voter is eligible to participate in the election.

- `voter_pubkey` — the public key of the eligible voter
- `voter_id` — a human-readable identifier for the voter
- `timestamp` — when the registration was issued
- `tracker_signature` — signature over all fields above, signed by the Tracker's private key

Only a `RegistrationTx` bearing a valid Tracker signature is accepted into the mempool or onto the chain. All nodes know the Tracker's public key and use it to verify this signature.

### VoteTx

Records a vote cast by a registered voter.

- `voter_pubkey` — the public key of the voter casting the ballot
- `candidate_id` — the identifier of the candidate being voted for
- `timestamp` — when the vote was cast
- `signature` — signature over all fields above, signed by the voter's private key

Before a `VoteTx` is accepted into the mempool, a node checks:
1. A valid `RegistrationTx` for `voter_pubkey` exists in the confirmed chain.
2. No confirmed `VoteTx` for `voter_pubkey` already exists in the chain.

If either check fails, the transaction is rejected.

## Blockchain Design

### Block Structure

Each block contains the following fields:

1. `index` — position of the block in the chain (0 for genesis block)
2. `timestamp` — Unix timestamp of when the block was mined
3. `transactions` — list of `RegistrationTx` and `VoteTx` transactions included in this block
4. `previous_hash` — SHA-256 hash of the preceding block
5. `nonce` — value iterated during mining to satisfy the difficulty target
6. `hash` — SHA-256 hash of all fields above

### Mining

Mining is a proof-of-work process. A valid block's SHA-256 hash must begin with a fixed number of leading zeros (the difficulty). This is satisfied by iterating the nonce field. The difficulty is a fixed constant shared by all peers.

Mining is **time-based**. Each node runs on fixed epochs (e.g., every 30 seconds). At the end of each epoch, if the mempool contains any pending transactions, the node bundles them into a block and begins mining. This ensures votes are not held up waiting for a transaction count threshold to be reached.

### Block Verification

A received block is accepted if and only if it passes the following requirements:

1. **Hash consistency** — the hash is recomputed from the block's contents and checked against the provided hash.
2. **Chain continuity** — the `previous_hash` matches the hash of the local chain's last block.
3. **Proof of work** — the hash begins with the required number of leading zeros.
4. **Transaction validity** — every transaction in the block passes the same validation rules applied at mempool insertion (valid signatures, no double-votes, registrations signed by Tracker).

A block that fails any of these requirements is discarded.

### Fork Resolution

To resolve forks, we use the longest chain wins rule. When a peer receives a block that conflicts with its current chain, it compares lengths and switches to the longer one.

When switching chains, any transactions in the discarded branch that are not present in the winning branch are returned to the mempool for re-inclusion in a future block.

### Catch-Up (Joining a Live Network)

On join, a peer requests the full chain from one known peer, verifies it block by block from genesis, then adopts it as its local chain.

## Data Structures

### Tracker Messages

- **Register** — sent by a peer to announce itself; includes `type`, `address`, and `pubkey`
- **Peer list** — sent by the Tracker in response; includes `type` and a list of known peers, each with an `address` and `pubkey`
- **Deregister** — sent by a peer on departure; includes `type` and `address`
- **RegistrationTx issuance** — sent by the Tracker to certify a voter; includes the full signed `RegistrationTx`

### RegistrationTx

- `voter_pubkey` — voter's public key
- `voter_id` — human-readable voter identifier
- `timestamp` — time of issuance
- `tracker_signature` — Tracker's signature over the above fields

### VoteTx

- `voter_pubkey` — voter's public key
- `candidate_id` — candidate being voted for
- `timestamp` — time the vote was cast
- `signature` — voter's signature over the above fields

### Block

- `index` — position in the chain
- `timestamp` — time the block was mined
- `transactions` — list of `RegistrationTx` and `VoteTx`
- `previous_hash` — SHA-256 hash of the preceding block
- `nonce` — iterated during mining to satisfy difficulty
- `hash` — SHA-256 hash of all fields above

## Demo Application

The demo application simulates a complete election. The Tracker registers eligible voters by issuing signed `RegistrationTx` transactions. Registered voters cast votes via the command line. Each vote is signed, broadcast to all peers, and added to their mempools. At the end of each epoch, nodes mine a block containing all pending transactions and broadcast it to the network.

Reading the current vote tally is equivalent to scanning all `VoteTx` transactions across all blocks in the chain and counting votes per candidate. Reading the voter roll is equivalent to scanning all `RegistrationTx` transactions.

## Challenges

See `challenges.md` for a running record of the design and implementation challenges we encountered while building this system, along with the solutions we arrived at.
