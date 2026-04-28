# Design Challenges and Solutions

## 1. Voter Registration Authority

**Challenge:** In a decentralized network with no central server, any node could claim to register voters. There is no inherent way to distinguish a legitimate voter registration from a fraudulent one injected by a malicious peer.

**Solution:** The Tracker node doubles as the election authority. Only `RegistrationTx` transactions bearing a valid signature from the Tracker's private key are accepted by the network. All nodes know the Tracker's public key at startup and use it to verify every `RegistrationTx` before adding it to the mempool or accepting it in a block. This creates a single, auditable root of trust for voter eligibility without requiring a centralized vote-counting server.

---

## 2. Preventing Double Voting

**Challenge:** A voter could attempt to cast more than one vote by broadcasting multiple `VoteTx` transactions before any of them are mined into a block. With flooding-based propagation, multiple votes from the same voter could appear in different nodes' mempools simultaneously.

**Solution:** Before accepting a `VoteTx` into the mempool, each node scans the confirmed chain for any existing `VoteTx` from the same `voter_pubkey`. If one is found, the new transaction is rejected. Additionally, block verification enforces the same rule — a block containing a duplicate vote is rejected by all peers. Because the chain is the canonical record, the first vote to be mined is the only one that counts.

---

## 3. Mining Trigger: Threshold vs. Time

**Challenge:** If mining is triggered by a mempool transaction count threshold, votes may be delayed indefinitely during low-activity periods (e.g., near the start or end of an election). Voters would have no guarantee of when their vote gets confirmed.

**Solution:** Mining uses fixed time-based epochs instead of a count threshold. At the end of each epoch, any node with pending transactions in its mempool mines a block. This ensures votes are processed on a predictable schedule regardless of network activity level.

---

## 4. Sybil Attacks (One Person, Many Identities)

**Challenge:** Since node identity is just a public/private key pair generated locally, nothing stops a malicious actor from generating many key pairs and registering many "voters," each casting a separate vote.

**Solution:** Voter registration is gated by the Tracker. The Tracker issues `RegistrationTx` transactions manually, binding a real-world `voter_id` to a public key. Since only the Tracker can produce a valid `RegistrationTx`, an attacker cannot self-register new identities. The voter roll (all `RegistrationTx` on the chain) is publicly auditable, so duplicate `voter_id` entries are detectable.

---

## 5. Fork Resolution with Votes

**Challenge:** When a chain fork is resolved and the shorter branch is discarded, transactions in the orphaned branch are lost unless handled explicitly. In a voting system, a voter whose `VoteTx` was in the discarded branch would effectively lose their vote silently.

**Solution:** When switching to a longer chain, any transactions from the discarded branch that are not present in the winning branch are returned to the mempool. They will be re-broadcast and included in the next mined block. Because double-vote validation checks the confirmed chain (not the mempool), a voter's original vote re-entering the mempool after a fork is treated as a fresh, valid vote.

---

## 6. Late-Joining Nodes

**Challenge:** A node that joins after the election has already started has no blocks and cannot validate incoming transactions against the chain (e.g., it cannot check if a voter is registered).

**Solution:** On startup, a joining node requests the full chain from one known peer and verifies it block by block from genesis before participating. Only after this catch-up is complete does the node begin accepting transactions and joining the mining process.
