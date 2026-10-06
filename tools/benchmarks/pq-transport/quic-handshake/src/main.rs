//! What does a hybrid key exchange cost a QUIC handshake?
//!
//! The measured numbers we have for X25519MLKEM768 come from TCP-TLS, where the
//! concern is the handshake outgrowing a packet. QUIC behaves differently and
//! the difference cuts both ways: a client's Initial is padded to at least 1200
//! bytes whatever it carries, so a larger ClientHello may cost nothing until it
//! spills into a second datagram — and once it does, the server's
//! anti-amplification allowance (3x what it has received) grows with it.
//!
//! So this measures, per handshake, on the real quinn/rustls stack:
//!
//!   * time to an established connection,
//!   * datagrams and bytes each way,
//!   * the size of the client's first flight.
//!
//! The only variable between the two arms is `kx_groups`. Everything else —
//! TLS 1.3, cipher suites, the self-signed certificate, ALPN — is held
//! identical, so the delta is attributable to the key exchange and nothing
//! else. The absolute numbers are shaped like libp2p's handshake (same suites,
//! same self-signed P-256 certificate carrying no CA chain) but this is not
//! libp2p: there is no peer-identity extension and no custom verifier. Those
//! cost the same in both arms.
//!
//! Loopback, so this is protocol and CPU cost with no network in the way.

use std::{
    net::{Ipv4Addr, SocketAddr, UdpSocket},
    sync::Arc,
    time::Instant,
};

use quinn::{ClientConfig, Endpoint, ServerConfig, TransportConfig};
use rustls::crypto::aws_lc_rs;

const ALPN: &[u8] = b"libp2p";

/// A self-signed certificate, as libp2p uses: no CA, verified out of band.
fn self_signed() -> (rustls::pki_types::CertificateDer<'static>, rustls::pki_types::PrivateKeyDer<'static>) {
    let cert = rcgen::generate_simple_self_signed(vec!["localhost".into()]).unwrap();
    let key = rustls::pki_types::PrivatePkcs8KeyDer::from(cert.key_pair.serialize_der());
    (cert.cert.into(), key.into())
}

/// Accept any certificate: libp2p authenticates by the identity extension, not
/// by a chain, and reproducing that here would add cost to both arms equally.
#[derive(Debug)]
struct AcceptAny(Arc<rustls::crypto::CryptoProvider>);

impl rustls::client::danger::ServerCertVerifier for AcceptAny {
    fn verify_server_cert(
        &self,
        _e: &rustls::pki_types::CertificateDer<'_>,
        _i: &[rustls::pki_types::CertificateDer<'_>],
        _s: &rustls::pki_types::ServerName<'_>,
        _o: &[u8],
        _n: rustls::pki_types::UnixTime,
    ) -> Result<rustls::client::danger::ServerCertVerified, rustls::Error> {
        Ok(rustls::client::danger::ServerCertVerified::assertion())
    }
    fn verify_tls12_signature(
        &self,
        _m: &[u8],
        _c: &rustls::pki_types::CertificateDer<'_>,
        _d: &rustls::DigitallySignedStruct,
    ) -> Result<rustls::client::danger::HandshakeSignatureValid, rustls::Error> {
        unreachable!("TLS 1.3 only")
    }
    fn verify_tls13_signature(
        &self,
        message: &[u8],
        cert: &rustls::pki_types::CertificateDer<'_>,
        dss: &rustls::DigitallySignedStruct,
    ) -> Result<rustls::client::danger::HandshakeSignatureValid, rustls::Error> {
        rustls::crypto::verify_tls13_signature(
            message,
            cert,
            dss,
            &self.0.signature_verification_algorithms,
        )
    }
    fn supported_verify_schemes(&self) -> Vec<rustls::SignatureScheme> {
        self.0.signature_verification_algorithms.supported_schemes()
    }
}

/// A provider offering exactly one key exchange group, so the negotiation has
/// no choice and the arm is unambiguous.
fn provider_with(group: &'static dyn rustls::crypto::SupportedKxGroup) -> Arc<rustls::crypto::CryptoProvider> {
    let mut p = aws_lc_rs::default_provider();
    p.kx_groups = vec![group];
    Arc::new(p)
}

fn endpoints(
    group: &'static dyn rustls::crypto::SupportedKxGroup,
) -> (Endpoint, Endpoint, SocketAddr) {
    let provider = provider_with(group);
    let (cert, key) = self_signed();

    let mut server_crypto = rustls::ServerConfig::builder_with_provider(provider.clone())
        .with_protocol_versions(&[&rustls::version::TLS13])
        .unwrap()
        .with_no_client_auth()
        .with_single_cert(vec![cert], key)
        .unwrap();
    server_crypto.alpn_protocols = vec![ALPN.to_vec()];

    let mut client_crypto = rustls::ClientConfig::builder_with_provider(provider.clone())
        .with_protocol_versions(&[&rustls::version::TLS13])
        .unwrap()
        .dangerous()
        .with_custom_certificate_verifier(Arc::new(AcceptAny(provider)))
        .with_no_client_auth();
    client_crypto.alpn_protocols = vec![ALPN.to_vec()];

    // No 0-RTT, no session resumption: every handshake is a full one.
    client_crypto.enable_early_data = false;

    let transport = Arc::new(TransportConfig::default());

    let mut server_cfg =
        ServerConfig::with_crypto(Arc::new(quinn::crypto::rustls::QuicServerConfig::try_from(server_crypto).unwrap()));
    server_cfg.transport_config(transport.clone());

    let mut client_cfg =
        ClientConfig::new(Arc::new(quinn::crypto::rustls::QuicClientConfig::try_from(client_crypto).unwrap()));
    client_cfg.transport_config(transport);

    let server_sock = UdpSocket::bind((Ipv4Addr::LOCALHOST, 0)).unwrap();
    let addr = server_sock.local_addr().unwrap();
    let server = Endpoint::new(Default::default(), Some(server_cfg), server_sock, Arc::new(quinn::TokioRuntime)).unwrap();

    let client_sock = UdpSocket::bind((Ipv4Addr::LOCALHOST, 0)).unwrap();
    let mut client = Endpoint::new(Default::default(), None, client_sock, Arc::new(quinn::TokioRuntime)).unwrap();
    client.set_default_client_config(client_cfg);

    (client, server, addr)
}

struct Sample {
    micros: u128,
    tx_datagrams: u64,
    tx_bytes: u64,
    rx_datagrams: u64,
    rx_bytes: u64,
}

async fn one_handshake(client: &Endpoint, server: &Endpoint, addr: SocketAddr) -> Sample {
    let accept = tokio::spawn({
        let server = server.clone();
        async move {
            let incoming = server.accept().await.unwrap();
            let conn = incoming.await.unwrap();
            // Hold it open until the client has measured.
            tokio::time::sleep(std::time::Duration::from_millis(50)).await;
            drop(conn);
        }
    });

    let t = Instant::now();
    let conn = client.connect(addr, "localhost").unwrap().await.unwrap();
    let micros = t.elapsed().as_micros();

    let s = conn.stats();
    let sample = Sample {
        micros,
        tx_datagrams: s.udp_tx.datagrams,
        tx_bytes: s.udp_tx.bytes,
        rx_datagrams: s.udp_rx.datagrams,
        rx_bytes: s.udp_rx.bytes,
    };
    conn.close(0u32.into(), b"done");
    let _ = accept.await;
    sample
}

fn median(mut v: Vec<u128>) -> u128 {
    v.sort_unstable();
    v[v.len() / 2]
}

async fn arm(
    label: &str,
    group: &'static dyn rustls::crypto::SupportedKxGroup,
    reps: usize,
) {
    let (client, server, addr) = endpoints(group);

    // Warm up: first handshake pays one-off allocation and page faults.
    for _ in 0..3 {
        one_handshake(&client, &server, addr).await;
    }

    let mut samples = Vec::with_capacity(reps);
    for _ in 0..reps {
        samples.push(one_handshake(&client, &server, addr).await);
    }

    let t = median(samples.iter().map(|s| s.micros).collect());
    let txd = median(samples.iter().map(|s| s.tx_datagrams as u128).collect());
    let txb = median(samples.iter().map(|s| s.tx_bytes as u128).collect());
    let rxd = median(samples.iter().map(|s| s.rx_datagrams as u128).collect());
    let rxb = median(samples.iter().map(|s| s.rx_bytes as u128).collect());

    println!(
        "  {label:<18} {:>8.3} ms   {txd:>3} / {txb:>6} B out   {rxd:>3} / {rxb:>6} B in   {:>6} B total",
        t as f64 / 1000.0,
        txb + rxb
    );

    client.wait_idle().await;
}

#[tokio::main]
async fn main() {
    let reps: usize = std::env::args()
        .nth(1)
        .and_then(|s| s.parse().ok())
        .unwrap_or(200);

    println!("QUIC handshake, quinn + rustls (aws-lc-rs), loopback, TLS 1.3");
    println!("median of {reps} full handshakes, no 0-RTT, no resumption\n");
    println!("  {:<18} {:>11}   {:>18}   {:>18}   {:>8}", "key exchange", "time", "datagrams/bytes out", "datagrams/bytes in", "total");

    arm("X25519", aws_lc_rs::kx_group::X25519, reps).await;
    arm("X25519MLKEM768", aws_lc_rs::kx_group::X25519MLKEM768, reps).await;

    println!("\n─── packet trace (one handshake each) ───");
    trace("X25519", aws_lc_rs::kx_group::X25519).await;
    trace("X25519MLKEM768", aws_lc_rs::kx_group::X25519MLKEM768).await;
}

// ---------------------------------------------------------------------------
// Packet trace: a UDP relay between client and server that records the size and
// direction of every datagram. This is what answers the questions the byte
// totals cannot -- whether the ClientHello spills into a second datagram, and
// whether the server is held back by QUIC's 3x anti-amplification limit before
// address validation.
// ---------------------------------------------------------------------------

async fn trace(label: &str, group: &'static dyn rustls::crypto::SupportedKxGroup) {
    use std::sync::Mutex;

    let (_c, server, server_addr) = endpoints(group);

    let relay = Arc::new(tokio::net::UdpSocket::bind((Ipv4Addr::LOCALHOST, 0)).await.unwrap());
    let relay_addr = relay.local_addr().unwrap();
    let log: Arc<Mutex<Vec<(char, usize)>>> = Arc::new(Mutex::new(Vec::new()));

    // Relay: first sender is the client; everything else comes from the server.
    let pump = tokio::spawn({
        let relay = relay.clone();
        let log = log.clone();
        async move {
            let up = tokio::net::UdpSocket::bind((Ipv4Addr::LOCALHOST, 0)).await.unwrap();
            let mut down = [0u8; 2048];
            let mut upb = [0u8; 2048];
            let mut client_addr = None;
            loop {
                tokio::select! {
                    Ok((n, from)) = relay.recv_from(&mut down) => {
                        client_addr = Some(from);
                        log.lock().unwrap().push(('>', n));
                        let _ = up.send_to(&down[..n], server_addr).await;
                    }
                    Ok((n, _)) = up.recv_from(&mut upb) => {
                        log.lock().unwrap().push(('<', n));
                        if let Some(c) = client_addr { let _ = relay.send_to(&upb[..n], c).await; }
                    }
                }
            }
        }
    });

    let provider = provider_with(group);
    let mut cc = rustls::ClientConfig::builder_with_provider(provider.clone())
        .with_protocol_versions(&[&rustls::version::TLS13]).unwrap()
        .dangerous()
        .with_custom_certificate_verifier(Arc::new(AcceptAny(provider)))
        .with_no_client_auth();
    cc.alpn_protocols = vec![ALPN.to_vec()];
    let cfg = ClientConfig::new(Arc::new(quinn::crypto::rustls::QuicClientConfig::try_from(cc).unwrap()));

    let sock = UdpSocket::bind((Ipv4Addr::LOCALHOST, 0)).unwrap();
    let mut client = Endpoint::new(Default::default(), None, sock, Arc::new(quinn::TokioRuntime)).unwrap();
    client.set_default_client_config(cfg);

    let acc = tokio::spawn(async move {
        if let Some(i) = server.accept().await { let _ = i.await; }
        tokio::time::sleep(std::time::Duration::from_millis(200)).await;
    });

    let conn = client.connect(relay_addr, "localhost").unwrap().await.unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(30)).await;
    conn.close(0u32.into(), b"done");
    pump.abort();
    let _ = acc.await;

    let l = log.lock().unwrap();
    let first_flight: usize = l.iter().take_while(|(d, _)| *d == '>').map(|(_, n)| n).sum();
    let ff_count = l.iter().take_while(|(d, _)| *d == '>').count();
    println!("\n  {label} — first {} datagrams", l.len().min(10));
    for (d, n) in l.iter().take(10) {
        let arrow = if *d == '>' { "client -> server" } else { "server -> client" };
        println!("      {arrow}  {n:>5} B");
    }
    println!("      first flight: {ff_count} datagram(s), {first_flight} B");
}
