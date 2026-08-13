"""Inspect the MongoDB Atlas certificate chain to find OpenSSL 3.0 incompatibility."""
import ssl
import socket

host = "ac-jprcndz-shard-00-01.zw7q1a8.mongodb.net"
port = 27017

ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

s = socket.create_connection((host, port), timeout=10)
ss = ctx.wrap_socket(s, server_hostname=host)
leaf_cert_der = ss.getpeercert(binary_form=True)
print(f"TLS version: {ss.version()}")
print(f"Cipher: {ss.cipher()}")

try:
    chain = ss.get_verified_chain()
    print(f"\nFull chain ({len(chain)} certs):")
    chain_ders = [bytes(c) for c in chain]
except Exception as e:
    print(f"get_verified_chain: {e}")
    chain_ders = [leaf_cert_der]

ss.close()
s.close()

try:
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import rsa, ec

    for i, der in enumerate(chain_ders):
        cert = x509.load_der_x509_certificate(der)
        subj = cert.subject.rfc4514_string()
        issuer = cert.issuer.rfc4514_string()
        sig_alg = cert.signature_hash_algorithm
        sig_name = sig_alg.name if sig_alg else "unknown"

        key = cert.public_key()
        if isinstance(key, rsa.RSAPublicKey):
            key_info = f"RSA {key.key_size} bits"
        elif isinstance(key, ec.EllipticCurvePublicKey):
            key_info = f"EC {key.key_size} bits ({key.curve.name})"
        else:
            key_info = type(key).__name__

        print(f"\n  Cert[{i}]:")
        print(f"    Subject:    {subj}")
        print(f"    Issuer:     {issuer}")
        print(f"    Sig alg:    {sig_name}")
        print(f"    Public key: {key_info}")
        print(f"    Not before: {cert.not_valid_before_utc}")
        print(f"    Not after:  {cert.not_valid_after_utc}")

        # Warn about weak configurations
        if sig_name in ("sha1", "md5"):
            print(f"    *** WARNING: Weak signature algorithm: {sig_name}")
        if isinstance(key, rsa.RSAPublicKey) and key.key_size < 2048:
            print(f"    *** WARNING: RSA key < 2048 bits: {key.key_size}")
        if isinstance(key, ec.EllipticCurvePublicKey) and key.key_size < 256:
            print(f"    *** WARNING: EC key < 256 bits: {key.key_size}")

except ImportError:
    print("\ncryptography package not installed — installing...")
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography", "-q"])
    print("Installed cryptography. Please re-run this script.")
except Exception as e:
    print(f"\nCert inspection error: {e}")
