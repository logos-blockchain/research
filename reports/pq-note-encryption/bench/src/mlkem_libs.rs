//! ML-KEM-768 alone, two implementations, to explain the X-Wing numbers.
use std::time::Instant;

fn rand<const N: usize>() -> [u8; N] {
    let mut b = [0u8; N];
    getrandom::fill(&mut b).unwrap();
    b
}

fn bench<F: FnMut()>(label: &str, iters: usize, mut f: F) {
    let t = Instant::now();
    for _ in 0..iters {
        f();
    }
    println!("{label:<44} {:>9.2} us/op", t.elapsed().as_secs_f64() * 1e6 / iters as f64);
}

fn main() {
    let n = 5_000;
    {
        use libcrux_ml_kem::mlkem768::{decapsulate, encapsulate, generate_key_pair};
        let kp = generate_key_pair(rand::<64>());
        let (ct, _ss) = encapsulate(kp.public_key(), rand::<32>());
        bench("libcrux ML-KEM-768 keygen", n, || { let _ = generate_key_pair(rand::<64>()); });
        bench("libcrux ML-KEM-768 encapsulate", n, || { let _ = encapsulate(kp.public_key(), rand::<32>()); });
        bench("libcrux ML-KEM-768 decapsulate", n, || { let _ = decapsulate(kp.private_key(), &ct); });
    }
    {
        use ml_kem::{Decapsulate, Encapsulate, Kem, MlKem768};
        type Dk = ml_kem::DecapsulationKey<MlKem768>;
        type Ek = ml_kem::EncapsulationKey<MlKem768>;
        let (dk, ek): (Dk, Ek) = MlKem768::generate_keypair();
        let (ct, _ss) = ek.encapsulate();
        bench("RustCrypto ML-KEM-768 keygen", n, || { let _ = MlKem768::generate_keypair(); });
        bench("RustCrypto ML-KEM-768 encapsulate", n, || { let _ = ek.encapsulate(); });
        bench("RustCrypto ML-KEM-768 decapsulate", n, || { let _ = dk.decapsulate(&ct); });
    }
}
