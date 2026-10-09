# Post-quantum note encryption for the Logos shielded ledger

Status: draft for review, 2026-10-09.

Recommendation: encrypt note outputs under a post-quantum/traditional hybrid KEM from the first mainnet block. The ciphertexts are the one part of a shielded ledger that an adversary can record today and read later, and Logos is still on testnet, so there is no history to carry over.

## 1. How shielded ledgers encrypt notes

A shielded (private UTXO) ledger keeps the same objects as a transparent one, a note is still `(value, owner key, randomness)`, but the chain never sees them in clear. Three roles are enough to describe it:

- The **sender** builds the transaction. It knows the recipient's address, the amounts and the randomness it chose.
- The **recipient** learns about the note only from the chain. It has to find the note among all outputs, learn its contents, and later prove ownership to spend it.
- The **validator** sees only what is public: a commitment `cm` per output, a nullifier `nf` per spent input, a zero-knowledge proof that the transaction balances and that the spent notes exist, and the fee.

What is hidden is the amount, who received it, and the link between the inputs and the outputs of a transaction. What makes the hidden note usable by the recipient is a ciphertext published next to `cm`: the sender encrypts the note contents under the recipient's public encryption key. The recipient tries to decrypt every output on the chain with its secret key; when one decrypts, it recomputes `cm` from the plaintext and its own spending key and, if it matches, it owns that note. The same secret key is the recipient's viewing key, and because it is derived from the wallet seed, the wallet can rebuild its notes from the seed and the chain alone.

This is the design every deployed shielded ledger uses, with small variations in what the plaintext carries and how the symmetric key is derived:

| Project | Note encryption today | Post-quantum status |
| --- | --- | --- |
| Zcash (Sapling, Orchard) | ephemeral Jubjub/Pallas Diffie-Hellman, BLAKE2b KDF, ChaCha20-Poly1305; per output 580 B `enc_ciphertext` + 80 B `out_ciphertext` + 32 B ephemeral key | Roadmap announced May 2026: ZIP 2005 quantum recoverability (testnet), ML-KEM note encryption with Tachyon in 12 to 18 months, a post-quantum pool after. Tachyon also moves ciphertexts off chain (oblivious synchronisation). Nothing shipped. |
| Monero | ECDH with view tags (Carrot, with FCMP++) | Jamtis-PQ research with CSIDH-1024, chosen over lattices because of address size (lattice addresses over 1300 characters, pruned transaction size up to 6x). Not deployed; CSIDH is unstandardised and slow. |
| Penumbra | decaf377 key agreement, 160 B note plaintext, 176 B ciphertext, 32 B ephemeral key | None. |
| Aztec | Grumpkin ECDH; encrypted logs carry a sender/recipient tag (`poseidon2(secret, index)`) so recipients query by tag instead of trial-decrypting | None. |
| Abelian | lattice ring signatures and Kyber-based one-time key exchange, mainnet | Post-quantum by construction, but a ring-signature coin, not a SNARK shielded pool. |
| Qumbra | one STARK per transaction, "ML-KEM note encryption" | Testnet, single developer, source private. |

Two observations. No SNARK-based shielded ledger ships post-quantum note encryption today, and the two largest privacy projects have both decided they need it. The only reason anyone hesitates is size: about 1.1 KB of KEM ciphertext per output and 1.2 KB of KEM public key per address. Section 4 shows that both are manageable.

## 2. Note encryption in the Logos design

The private UTXO ledger is specified in lips PR #480 (Mantle 2.0.0). A note is `(value, nonce, public_key)`, stored only as its commitment; every note lives in one note set (the ledger set, the SDP set, or one set per channel), each set keeping a commitment MMR and a nullifier indexed Merkle tree:

```
cm = zkhash(NOTE_CM_V1 || value || nonce || public_key)
nf = zkhash(NOTE_NF_V1 || cm || secret_key)
```

A Transfer publishes nullifiers, output commitments, a recent commitment root and a ZkTransfer proof (4 inputs, 8 outputs). The PR leaves one thing explicitly out of scope: how a recipient learns the value and nonce of a note it receives. This document fills that gap. The proposal adds to every output of a Transfer, a channel deposit, a channel withdrawal and a channel step a ciphertext of `value || nonce` under the recipient's encryption key, and defines the address as the pair of keys a sender needs:

```
address = (pk_zk, pk_enc)
output  = (cm, Enc_{pk_enc}(value || nonce))
```

The recipient decrypts, recomputes `cm` with its `pk_zk`, and knows the note is its own. Nothing about the encryption enters the circuit: the ZkTransfer covers `cm`, `nf`, membership and balance, and the ciphertext is checked only by the recipient, as in Zcash. A sender that publishes a wrong ciphertext burns the recipient's note and nothing else.

Facts of the surrounding design that the encryption has to live with:

- Notes the ledger creates itself carry no ciphertext: the leader reward note, the proof-of-work reward note and the service note derive their nonce from the operation (`derive_note_nonce`) and their value is public, so the owner recomputes `cm` without help. Only user-created outputs need a ciphertext.
- Channel steps put all their data on chain (nullifiers, commitments, proof), so a step output needs its ciphertext like a ledger output, and it adds to the size of the sequencer's inscription.
- A ZkTransfer proves its inputs against a commitment root from the last 1024 blocks, and a note created in a block can be spent only from the next block, so a recipient cannot be told about a note by a chained transaction; the ciphertext is the only channel.
- The wallet standard (1.2.0 in the PR) already assumes a wallet follows every commitment appended and every nullifier inserted in the sets it holds notes in, to maintain its Merkle paths locally, since asking a server for a path reveals which notes it owns. The ciphertext stream comes on top of that.
- Genesis notes are published as preimages: the value and public key of every initial output are in an inscription to the null channel. This does not change what later outputs must hide.
- An ephemeral, prunable data-availability layer is under discussion for channel data. Note ciphertexts cannot live there: a wallet recovering from its seed needs every ciphertext ever addressed to it, so the ciphertexts are permanent ledger data, or recovery is bounded by the retention window.
- Common Cryptographic Components becomes 1.3.0 with the PR (ZkSignature removed); the note encryption section proposed here would be the next revision.

## 3. The reason to do it now

Every note ciphertext is on chain for the life of the chain. A record of the chain taken today can be decrypted the day a cryptographically relevant quantum computer exists. The plaintext `value || nonce`, together with a candidate `pk_zk`, lets the attacker recompute `cm`, attribute every note to its owner and unwind the transaction graph. Changing the encryption later protects later notes only. The proof system and the signatures do not have this property: when they break, the fix is a migration, and nothing already on chain becomes readable.

Logos is on testnet. Starting mainnet with post-quantum note encryption means the chain never carries a classically encrypted history, and it would be the first SNARK-based shielded ledger to do so, ahead of the 2027 target the largest privacy project has set for itself.

## 4. Recommended scheme

The X-Wing hybrid KEM, as specified, with a BLAKE2b key derivation and ChaCha20-Poly1305:

- KEM: X-Wing (`draft-connolly-cfrg-xwing-kem-11`, September 2026): ML-KEM-768 and X25519, the two shared secrets combined as `SHA3-256(ss_M || ss_X || ct_X || pk_X || label)`. 1216 B public key, 1120 B ciphertext, 32 B secret seed. IND-CCA secure as long as either component holds, with the MAL-BIND-K-PK and MAL-BIND-K-CT binding properties. The same construction is registered for HPKE in `draft-ietf-hpke-pq-05` as `MLKEM768-X25519`, KEM id `0x647a`, so its sizes and test vectors are fixed by a registry.
- KDF: domain-separated BLAKE2b-256, `key = BLAKE2b-256(DST || ss || ct)` with `DST = LOGOS_NOTE_ENC_V1`, following the Common Cryptographic Components convention for domain separation. Zcash derives its note-encryption key the same way (`BLAKE2b-256("Zcash_SaplingKDF", shared_secret || epk)`).
- AEAD: ChaCha20-Poly1305 (Zcash's choice; AES-256-GCM is equivalent, whichever the node already links), nonce fixed to zero since every key is used once, `aad = cm` so a ciphertext cannot be moved to another output.

Plaintext `value (8 B) || nonce (32 B)`, 40 B; ciphertext 56 B with the tag. The plaintext layout is versioned so an `asset_id` or a memo can be added without touching the KEM.

This is the HPKE base-mode shape (KEM, KDF, AEAD, one-shot) with the KDF swapped, and it is specified here as its own composition rather than as HPKE, because HPKE registers no BLAKE2 KDF. The KEM itself is left exactly as X-Wing: changing its SHA3-256 combiner for BLAKE2b would turn it into a construction with no registry entry, no published test vectors and no implementation to reuse, and its security argument, which models the combiner hash as a random oracle, would hold but nobody would have written it for us. SHA-3 is in the dependency set regardless, since FIPS 203 uses SHA3-256, SHA3-512, SHAKE128 and SHAKE256 inside ML-KEM; it enters the component list with ML-KEM, not with the combiner.

Why hybrid rather than pure ML-KEM: the same reasoning as the transport RFC (lips #429). If ML-KEM-768 is found weak, X25519 keeps classical security; if X25519 falls, ML-KEM holds. The X25519 half costs 32 B and one scalar multiplication. Why not ML-KEM-512: 768 B instead of 1088 B is not worth dropping from NIST level 3 to level 1 on data that lives forever, and #429 already chose level 3 for the network. Why a standard KEM rather than a hand-rolled one: one specification to cite, published test vectors, sizes and identifiers fixed by a registry. The Blend message encryption (a BLAKE2b-seeded ChaCha20 keystream XOR with integrity from the signed headers) is not an AEAD and cannot give a wallet a reliable "this output is mine" answer, so it is not reused here even though its key agreement could be.

Properties needed and obtained:

- Detection. Trial decryption fails cleanly on the AEAD tag. As a second check the wallet recomputes `cm` from the plaintext and its own `pk_zk`; a ciphertext that decrypts but does not match `cm` is dropped.
- Unlinkability of outputs. ML-KEM ciphertexts are anonymous (Maram and Xagawa, PKC 2023) and X25519 ephemeral keys are uniform, so two outputs to the same address cannot be linked on chain. Diversified addresses are not needed for on-chain unlinkability, only against senders correlating a recipient across payments, which the first version does not try to solve.
- Recovery from seed. The X-Wing decapsulation key is a 32 B seed, so `pk_enc` is derived deterministically from the wallet master key. This secret is the viewing key: it reveals incoming values, not spends and not spend authority. If the nullifier used a key separate from the spending key (`nk = H(sk)`), the same viewing key could also see spends; that is a circuit-side choice.
- Forward secrecy is not a goal: a viewing key is meant to decrypt the whole history of the account.
- No circuit cost, as described in section 2.

## 5. Cost

Measured with the prototype in `bench/` (Apple M3, release build, 5000 iterations, `x-wing` 0.1.1 on RustCrypto `ml-kem` 0.3.2, `x25519-dalek` 3.0, `chacha20poly1305` 0.11, `blake2` 0.11):

| Operation | µs |
| --- | ---: |
| X-Wing keygen from a 32 B seed | 51 |
| X-Wing encapsulate | 96 |
| X-Wing decapsulate | 134 |
| note encrypt, X-Wing (encapsulate, KDF, AEAD) | 99 |
| note trial-decrypt, X-Wing, matching or not | 135 to 137 |
| note encrypt, X25519 baseline | 68 |
| note trial-decrypt, X25519 baseline | 47 |
| ML-KEM-768 decapsulate alone, RustCrypto `ml-kem` | 39 |
| ML-KEM-768 decapsulate alone, `libcrux-ml-kem` 0.0.11 | 19 |

The X-Wing decapsulation is slower than the sum of its parts because the `x-wing` crate keeps only the 32 B seed and re-expands the ML-KEM key on every call (about 38 µs of the 134). A wallet keeps the expanded key, so the achievable cost is one ML-KEM decapsulation plus one X25519 operation: about 85 µs with RustCrypto, about 65 µs with libcrux, on this machine. For comparison the reference Raspberry Pi 5 measured ML-KEM-768 at 32 µs encapsulate and 37 µs decapsulate with liboqs in the #429 work; the Pi 5 run of this prototype is still to do.

Per output, ciphertext bytes:

| Scheme | KEM part | note part | total |
| --- | ---: | ---: | ---: |
| X25519 ECIES (classical baseline) | 32 | 56 | 88 |
| ML-KEM-512 | 768 | 56 | 824 |
| ML-KEM-768 | 1088 | 56 | 1144 |
| X-Wing, MLKEM768-X25519 (recommended) | 1120 | 56 | 1176 |

Per transaction: one Groth16 proof (128 B compressed), an anchor (32 B), a nullifier per input (32 B), `cm` plus ciphertext per output. Change outputs need no KEM: the wallet encrypts them under a key derived from its own seed and the `cm` (56 B) and recovers them by the same derivation. A typical payment has one external output and one change output.

| Transaction | classical | hybrid |
| --- | ---: | ---: |
| 2 in, 2 out, one external + change | ~430 B | ~1.5 KB |
| 2 in, 2 out, both external | ~460 B | ~2.6 KB |
| 4 in, 8 out, all external (circuit maximum) | ~1.2 KB | ~10 KB |

A transparent transfer today is about 300 B, so the shielded design alone costs 1.5x and the hybrid KEM takes a common payment to 5x. `MAX_BLOCK_TRANSACTIONS_SIZE` is 2 MiB for 1024 transactions, an average of 2 KB per transaction, so a block of ordinary hybrid payments fits; a block of 8-output transactions holds about 200. The ZkTransfer bound of 8 outputs caps the ciphertext bytes of one transaction at about 9.4 KB. Storage gas already prices bytes, so the cost lands on the sender.

Scanning: a wallet decapsulates every external output once. The prototype scans 100,000 outputs in 13.7 s on the M3 (137 µs per output as the crate stands, 4.7 s for the X25519 baseline), so one million outputs take about two minutes as is and around one and a half with an expanded key; a Pi 5 should be assumed several times slower until measured. The KEM dominates, so a Monero-style view tag would not help; Aztec's tag-based discovery avoids scanning but needs shared sender/recipient state.

Address size: `pk_zk` (32 B) plus `pk_enc` (1216 B) is 1248 B, about 2000 characters in bech32m, within a QR code but unfriendly. Options, not exclusive:

1. The full address in payment requests and URIs, which the wallet standard already hands out per payment. Machine to machine this is a non-issue.
2. A short address `(pk_zk, H(pk_enc))` with `pk_enc` published once by an inscription on a key-directory channel. Logos has the primitive; Zcash discussed the same "address registration" idea for lattice keys in 2016 and has no channel to do it with. One-time 1.2 KB per user.
3. A compact post-quantum KEM such as CSIDH, Monero's direction. Rejected: unstandardised, seconds per operation, contested security.

The address should be defined as the full key bundle, with the directory as a later convenience. There should be no classical-only fallback for a sender without `pk_enc`; a downgrade path defeats the purpose.

## 6. Where it binds: permanent data and the wallet scan

The block and the network are not where the hybrid KEM hurts. The block budget is 2 MiB for 1024 transactions and an ordinary payment is 1.5 KB; Blend carries transactions in fixed-size messages, so a 10 KB transaction still costs one message; validators never touch the ciphertext.

It binds in two places that grow with history. Every external output leaves 1176 B on the chain for good, and a wallet recovering from its seed, or scanning after being offline, has to download every one of them and try it: trial decryption needs the whole KEM ciphertext, and no server can filter them without the viewing key. The wallet standard already has a wallet follow every commitment and nullifier of its sets (32 B each); the ciphertext stream is 37 times the commitment stream.

| Sustained load, one external output per transaction | permanent data, X25519 | permanent data, X-Wing | one year scanned, M3 |
| --- | ---: | ---: | ---: |
| 1 transaction/s | 2.8 GB/year | 37 GB/year | 1.2 h (X25519: 25 min) |
| 10 transactions/s | 28 GB/year | 370 GB/year | 12 h (X25519: 4 h) |

At one transaction per second this is acceptable. At ten, a light client cannot recover from its seed, and a node adds hundreds of gigabytes a year. The classical scheme has the same shape at one thirteenth of the size, so the hybrid KEM widens an existing problem rather than creating one, and the solution is the same for both.

Three directions, to be researched before the proposal is frozen:

1. **Detection tags.** The sender puts next to the output a short tag that only it and the recipient can compute, and the wallet asks a node for the outputs matching its tags and downloads the KEM ciphertext only for those. Aztec does this with `poseidon2(secret, index)` over a per-pair shared secret and counter, and its nodes index logs by tag. The cost is state shared between sender and recipient (a secret and a counter), which a first payment has to establish; the first version could use the recipient's address alone at the price of linking the recipient's outputs to anyone who knows the address.
2. **Oblivious synchronisation.** Zcash's Tachyon takes the ciphertexts off the chain entirely: wallets fetch what they need from untrusted servers without revealing what they look for, and the chain keeps only commitments and proofs. This removes the permanent data and, incidentally, the harvest-now-decrypt-later exposure, at the price of a new piece of infrastructure between wallets and nodes.
3. **A retention window.** The KEM ciphertexts go to the prunable layer under discussion for channel data, with a defined retention, and recovery from seed covers that window; a wallet that has decrypted its notes keeps them locally. Cheapest to build, and it changes the recovery guarantee of the wallet standard, which has to say so.

The first is the one that composes with the current design without new infrastructure, and it needs numbers: tag size, node-side index cost, and what the tag leaks.

## 7. Notes, to be tried or settled

- Prototype in `bench/`: the composition end to end (seed, `pk_enc`, encrypt, trial-decrypt, `cm` as `aad`), with checks that a wrong key and a moved ciphertext both fail, and the timings above. Done on the M3; the reference Pi 5 run is pending.
- Library choice: `libcrux-ml-kem` is formally verified and twice as fast as RustCrypto `ml-kem` here; `libcrux-kem` ships X-Wing but at draft 06, so the combiner has to be checked against draft 11 or composed by hand on top of `libcrux-ml-kem` and `x25519-dalek`. `aws-lc-rs` (used in the #429 benches) is the third option. Whichever is chosen must keep the expanded decapsulation key in memory.
- Test vectors fixed from the chosen library, for the whole path.
- A transaction-size calculator, and a check of whether transactions traverse Blend and what its payload bound allows.
- Where ciphertexts are stored and served: permanent ledger data, not the prunable layer; what a light client downloads to scan.
- Change-output derivation: key from the seed and `cm`, no KEM; confirm it does not weaken anything when the same wallet is both sender and recipient.
- Circuit-side asks: a nullifier key separate from the spending key; an `asset_id` slot in the `cm` preimage; `cm` uniqueness enforced by the ledger.
- Address encoding and the inscription-based key directory.
- Later: an outgoing viewing key for sender-side recovery (Zcash `ovk`), off-chain ciphertext delivery as in Tachyon, multi-recipient KEMs (mKyber, academic), and the post-quantum migration of the proof system, which is a separate document.

## References

- Logos lips PR #480, Mantle: Private UTXO ledger. https://github.com/logos-co/logos-lips/pull/480
- X-Wing: draft-connolly-cfrg-xwing-kem-11, 2026-09-23. https://datatracker.ietf.org/doc/html/draft-connolly-cfrg-xwing-kem-11
- Post-quantum KEMs for HPKE: draft-ietf-hpke-pq-05, 2026-07-06. https://datatracker.ietf.org/doc/html/draft-ietf-hpke-pq
- HPKE: RFC 9180. ML-KEM: FIPS 203.
- Maram, Xagawa. Post-Quantum Anonymity of Kyber. PKC 2023. https://eprint.iacr.org/2022/1696
- Grubbs, Maram, Paterson. Anonymous, Robust Post-Quantum Public Key Encryption. EUROCRYPT 2022.
- Zcash protocol specification, note encryption. https://zips.z.cash/protocol/protocol.pdf
- ZIP 212. https://zips.z.cash/zip-0212
- ZIP 2005, Ironwood quantum recoverability. https://zips.z.cash/zip-2005
- Zcash post-quantum roadmap, May 2026. https://www.blockhead.co/2026/05/12/zcash-shares-post-quantum-roadmap-as-zec-extends-75-monthly-rally/
- Monero Research Lab, post-quantum encryption (Jamtis-PQ). https://github.com/monero-project/research-lab/issues/151
- Penumbra shielded pool note format. https://github.com/penumbra-zone/penumbra/blob/main/crates/core/component/shielded-pool/src/note.rs
- Aztec note discovery. https://docs.aztec.network/developers/docs/concepts/advanced/storage/note_discovery
- Mikic, Srbakoski, Praska. Post-Quantum Stealth Address Protocols. 2025. https://arxiv.org/abs/2501.13733
- Multi-recipient Kyber. https://arxiv.org/abs/2504.17185
- libcrux ML-KEM, formally verified. https://github.com/pq-code-package/rust-libcrux
- Logos post-quantum transport phase 0 (lips #429) and its measurements, `reports/pqc/`.
