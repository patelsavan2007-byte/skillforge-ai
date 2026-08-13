"""Compare certificates across all 3 Atlas shards."""
import ssl, socket

shards = [
    'ac-jprcndz-shard-00-00.zw7q1a8.mongodb.net',
    'ac-jprcndz-shard-00-01.zw7q1a8.mongodb.net',
    'ac-jprcndz-shard-00-02.zw7q1a8.mongodb.net',
]

for shard in shards:
    print(f"\n=== {shard} ===")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        s = socket.create_connection((shard, 27017), timeout=10)
        try:
            ss = ctx.wrap_socket(s, server_hostname=shard)
            der = ss.getpeercert(binary_form=True)
            cipher = ss.cipher()
            tls_ver = ss.version()
            ss.close()
            
            from cryptography import x509
            from cryptography.hazmat.primitives.asymmetric import rsa, ec
            cert = x509.load_der_x509_certificate(der)
            subj = cert.subject.rfc4514_string()
            issuer = cert.issuer.rfc4514_string()
            sig = cert.signature_hash_algorithm
            key = cert.public_key()
            
            if isinstance(key, rsa.RSAPublicKey):
                key_info = f"RSA {key.key_size}b"
            elif isinstance(key, ec.EllipticCurvePublicKey):
                key_info = f"EC {key.key_size}b {key.curve.name}"
            else:
                key_info = type(key).__name__
            
            try:
                sans = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
                san_vals = [v.value for v in sans.value]
            except:
                san_vals = []
            
            print(f"  TLS: {tls_ver}, Cipher: {cipher[0]}")
            print(f"  Subject: {subj}")
            print(f"  Issuer:  {issuer}")
            print(f"  Sig: {sig.name if sig else 'unknown'}, Key: {key_info}")
            print(f"  SANs: {san_vals}")
            print(f"  Valid: {cert.not_valid_before_utc} → {cert.not_valid_after_utc}")
            
            # Check for RFC 5280 violations
            serial = cert.serial_number
            if serial <= 0:
                print(f"  *** RFC 5280 VIOLATION: non-positive serial number: {serial}")
            else:
                print(f"  Serial OK: {serial}")
        except ssl.SSLError as e:
            print(f"  TLS FAIL: {e}")
        finally:
            s.close()
    except Exception as e:
        print(f"  Connection error: {type(e).__name__}: {e}")
