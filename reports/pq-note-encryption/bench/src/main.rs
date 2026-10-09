//! Prototype of the note-encryption composition from the report:
//! X-Wing (ML-KEM-768 + X25519) as specified, BLAKE2b-256 KDF with a DST,
//! ChaCha20-Poly1305 with aad = cm. Baseline: X25519 ECIES with the same KDF/AEAD.
use blake2::{Blake2b256, Digest};
use chacha20poly1305::{
    aead::{Aead, KeyInit, Payload},
    ChaCha20Poly1305, Key, Nonce,
};
use std::time::Instant;
use x25519_dalek::{PublicKey as XPublic, StaticSecret as XSecret};
use x_wing::{Decapsulate, Decapsulator, DecapsulationKey, Encapsulate, EncapsulationKey, KeyExport};

const DST: &[u8] = b"LOGOS_NOTE_ENC_V1";
const PLAINTEXT_LEN: usize = 40; // value (8) || nonce (32)

fn kdf(ss: &[u8], ct: &[u8]) -> Key {
    let mut h = Blake2b256::new();
    h.update(DST);
    h.update(ss);
    h.update(ct);
    Key::from(<[u8; 32]>::from(h.finalize()))
}

fn seal(key: &Key, cm: &[u8; 32], pt: &[u8; PLAINTEXT_LEN]) -> Vec<u8> {
    ChaCha20Poly1305::new(key)
        .encrypt(&Nonce::default(), Payload { msg: pt, aad: cm })
        .expect("encrypt")
}

fn open(key: &Key, cm: &[u8; 32], ct: &[u8]) -> Option<[u8; PLAINTEXT_LEN]> {
    ChaCha20Poly1305::new(key)
        .decrypt(&Nonce::default(), Payload { msg: ct, aad: cm })
        .ok()
        .and_then(|v| v.try_into().ok())
}

/// One output on chain: cm, the KEM ciphertext, the AEAD ciphertext.
struct Output {
    cm: [u8; 32],
    kem_ct: Vec<u8>,
    note_ct: Vec<u8>,
}

fn rand32() -> [u8; 32] {
    let mut b = [0u8; 32];
    getrandom::fill(&mut b).unwrap();
    b
}

// ---------- X-Wing path ----------
fn xw_encrypt(ek: &EncapsulationKey, cm: &[u8; 32], pt: &[u8; PLAINTEXT_LEN]) -> Output {
    let (kem_ct, ss) = ek.encapsulate();
    let key = kdf(ss.as_slice(), kem_ct.as_slice());
    Output { cm: *cm, kem_ct: kem_ct.as_slice().to_vec(), note_ct: seal(&key, cm, pt) }
}

fn xw_try_decrypt(dk: &DecapsulationKey, o: &Output) -> Option<[u8; PLAINTEXT_LEN]> {
    let ss = dk.decapsulate_slice(&o.kem_ct).ok()?;
    let key = kdf(ss.as_slice(), &o.kem_ct);
    open(&key, &o.cm, &o.note_ct)
}

// ---------- X25519 ECIES baseline ----------
fn x_encrypt(pk: &XPublic, cm: &[u8; 32], pt: &[u8; PLAINTEXT_LEN]) -> Output {
    let esk = XSecret::from(rand32());
    let epk = XPublic::from(&esk);
    let ss = esk.diffie_hellman(pk);
    let key = kdf(ss.as_bytes(), epk.as_bytes());
    Output { cm: *cm, kem_ct: epk.as_bytes().to_vec(), note_ct: seal(&key, cm, pt) }
}

fn x_try_decrypt(sk: &XSecret, o: &Output) -> Option<[u8; PLAINTEXT_LEN]> {
    let epk = XPublic::from(<[u8; 32]>::try_from(o.kem_ct.as_slice()).ok()?);
    let ss = sk.diffie_hellman(&epk);
    let key = kdf(ss.as_bytes(), epk.as_bytes());
    open(&key, &o.cm, &o.note_ct)
}

fn bench<F: FnMut()>(label: &str, iters: usize, mut f: F) -> f64 {
    let t = Instant::now();
    for _ in 0..iters {
        f();
    }
    let us = t.elapsed().as_secs_f64() * 1e6 / iters as f64;
    println!("{label:<44} {us:>9.2} us/op");
    us
}

fn main() {
    // Recipient keys from a 32-byte wallet seed (deterministic, recoverable).
    let seed = rand32();
    let dk = DecapsulationKey::from(seed);
    let ek = dk.encapsulation_key().clone();
    let ek_bytes = ek.to_bytes();
    let xsk = XSecret::from(seed);
    let xpk = XPublic::from(&xsk);

    let cm = rand32();
    let mut pt = [0u8; PLAINTEXT_LEN];
    pt[..8].copy_from_slice(&1_000_000u64.to_le_bytes());
    pt[8..].copy_from_slice(&rand32());

    let o = xw_encrypt(&ek, &cm, &pt);
    assert_eq!(xw_try_decrypt(&dk, &o), Some(pt));
    let other = DecapsulationKey::from(rand32());
    assert_eq!(xw_try_decrypt(&other, &o), None, "wrong key must fail on the tag");
    let mut o2 = xw_encrypt(&ek, &cm, &pt);
    o2.cm = rand32();
    assert_eq!(xw_try_decrypt(&dk, &o2), None, "moved ciphertext must fail on aad");
    let b = x_encrypt(&xpk, &cm, &pt);
    assert_eq!(x_try_decrypt(&xsk, &b), Some(pt));

    println!("sizes (bytes)");
    println!("  X-Wing encapsulation key {:>6}", ek_bytes.len());
    println!("  X-Wing decapsulation key {:>6}", dk.as_bytes().len());
    println!("  X-Wing KEM ciphertext    {:>6}", o.kem_ct.len());
    println!("  note ciphertext (AEAD)   {:>6}", o.note_ct.len());
    println!("  per output, X-Wing       {:>6}", o.kem_ct.len() + o.note_ct.len());
    println!("  per output, X25519       {:>6}", b.kem_ct.len() + b.note_ct.len());
    println!();

    let n = 5_000;
    bench("X-Wing keygen from seed", n, || { let _ = DecapsulationKey::from(seed); });
    bench("X-Wing encapsulate", n, || { let _ = ek.encapsulate(); });
    bench("X-Wing decapsulate", n, || { let _ = dk.decapsulate_slice(&o.kem_ct); });
    bench("X-Wing note encrypt (encaps+kdf+aead)", n, || { let _ = xw_encrypt(&ek, &cm, &pt); });
    bench("X-Wing note trial-decrypt, match", n, || { let _ = xw_try_decrypt(&dk, &o); });
    bench("X-Wing note trial-decrypt, no match", n, || { let _ = xw_try_decrypt(&other, &o); });
    bench("X25519 note encrypt", n, || { let _ = x_encrypt(&xpk, &cm, &pt); });
    bench("X25519 note trial-decrypt", n, || { let _ = x_try_decrypt(&xsk, &b); });
    println!();

    // Scan: 100k outputs for other recipients, one for us.
    let m = 100_000;
    let others: Vec<EncapsulationKey> = (0..16).map(|_| DecapsulationKey::from(rand32()).encapsulation_key().clone()).collect();
    let mut chain: Vec<Output> = (0..m).map(|i| xw_encrypt(&others[i % 16], &rand32(), &pt)).collect();
    chain[m / 2] = xw_encrypt(&ek, &cm, &pt);
    let t = Instant::now();
    let found = chain.iter().filter(|o| xw_try_decrypt(&dk, o).is_some()).count();
    let el = t.elapsed();
    println!("scan {m} outputs (X-Wing): {:.2} s, {:.1} us/output, found {found}",
        el.as_secs_f64(), el.as_secs_f64() * 1e6 / m as f64);
    let xothers: Vec<XPublic> = (0..16).map(|_| XPublic::from(&XSecret::from(rand32()))).collect();
    let mut xchain: Vec<Output> = (0..m).map(|i| x_encrypt(&xothers[i % 16], &rand32(), &pt)).collect();
    xchain[m / 2] = x_encrypt(&xpk, &cm, &pt);
    let t = Instant::now();
    let found = xchain.iter().filter(|o| x_try_decrypt(&xsk, o).is_some()).count();
    let el = t.elapsed();
    println!("scan {m} outputs (X25519): {:.2} s, {:.1} us/output, found {found}",
        el.as_secs_f64(), el.as_secs_f64() * 1e6 / m as f64);
}
