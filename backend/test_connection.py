"""
MongoDB Atlas Connection Diagnostic Script
==========================================
Tests the connection to MongoDB Atlas step by step.
Never prints credentials.
"""
import os
import ssl
import socket
import sys

def check_dns():
    """Test DNS resolution for Atlas cluster."""
    host = "ac-jprcndz-shard-00-00.zw7q1a8.mongodb.net"
    print(f"\n[1] DNS resolution for {host}...")
    try:
        ip = socket.gethostbyname(host)
        print(f"    OK — resolved to {ip}")
        return True
    except socket.gaierror as e:
        print(f"    FAIL — DNS error: {e}")
        return False

def check_tcp():
    """Test raw TCP connectivity to Atlas port 27017."""
    host = "ac-jprcndz-shard-00-00.zw7q1a8.mongodb.net"
    port = 27017
    print(f"\n[2] TCP connection to {host}:{port}...")
    try:
        s = socket.create_connection((host, port), timeout=10)
        print(f"    OK — TCP connected")
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"    FAIL — TCP error: {e}")
        return False

def check_tls():
    """Test TLS handshake with Atlas."""
    host = "ac-jprcndz-shard-00-00.zw7q1a8.mongodb.net"
    port = 27017
    print(f"\n[3] TLS handshake with {host}:{port}...")
    try:
        ctx = ssl.create_default_context()
        s = socket.create_connection((host, port), timeout=10)
        ss = ctx.wrap_socket(s, server_hostname=host)
        version = ss.version()
        ss.close()
        s.close()
        print(f"    OK — TLS handshake succeeded (protocol: {version})")
        return True
    except ssl.SSLError as e:
        err_str = str(e)
        if "TLSV1_ALERT_INTERNAL_ERROR" in err_str or "tlsv1 alert internal error" in err_str.lower():
            print(f"    FAIL — TLS INTERNAL ERROR (server rejected connection)")
            print(f"    >>> This is the MongoDB Atlas IP allowlist rejecting your IP.")
            print(f"    >>> Your current public IP must be added to Atlas Network Access.")
            print(f"    >>> Go to: https://cloud.mongodb.com -> Network Access -> Add IP Address")
        elif "CERTIFICATE_VERIFY_FAILED" in err_str:
            print(f"    FAIL — Certificate verification failed: {e}")
        else:
            print(f"    FAIL — SSL error: {e}")
        return False
    except (socket.timeout, OSError) as e:
        print(f"    FAIL — Network error: {type(e).__name__}")
        return False

def check_pymongo_ping():
    """Test MongoDB Atlas via PyMongo ping."""
    print(f"\n[4] PyMongo ping to MongoDB Atlas...")
    
    # Load URI from .env without exposing it
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(backend_dir, ".env")
    
    uri = None
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("MONGODB_URI="):
                    uri = line[len("MONGODB_URI="):]
                    # Strip surrounding quotes if any
                    if (uri.startswith('"') and uri.endswith('"')) or \
                       (uri.startswith("'") and uri.endswith("'")):
                        uri = uri[1:-1]
                    break
    
    if not uri:
        uri = os.environ.get("MONGODB_URI", "")
    
    if not uri:
        print("    FAIL — MONGODB_URI is empty. Check your .env file.")
        return False
    
    if not uri.startswith("mongodb+srv://") and not uri.startswith("mongodb://"):
        print("    FAIL — MONGODB_URI does not start with mongodb+srv:// or mongodb://")
        return False
    
    has_at = "@" in uri
    print(f"    URI format: {'mongodb+srv://' if uri.startswith('mongodb+srv') else 'mongodb://'} ... (credentials hidden)")
    print(f"    URI contains @ (credentials present): {has_at}")
    print(f"    URI length: {len(uri)} chars")
    
    try:
        from pymongo import MongoClient
        import pymongo
        print(f"    PyMongo version: {pymongo.version}")
        
        client = MongoClient(uri, serverSelectionTimeoutMS=15000)
        client.admin.command("ping")
        client.close()
        print("    OK — MongoDB Atlas ping successful!")
        return True
    except Exception as e:
        err_str = str(e)
        err_type = type(e).__name__
        
        # Categorize the error without revealing credentials
        if "ServerSelectionTimeoutError" in err_type:
            if "SSL" in err_str or "TLS" in err_str or "tlsv1" in err_str.lower():
                print(f"    FAIL — TLS/SSL error during connection: Atlas IP allowlist likely blocking your IP")
            elif "timed out" in err_str.lower():
                print(f"    FAIL — Connection timed out: check network/firewall")
            elif "authentication" in err_str.lower():
                print(f"    FAIL — Authentication failed: check username/password in .env")
            else:
                print(f"    FAIL — Server selection timeout: {err_type}")
        elif "OperationFailure" in err_type:
            print(f"    FAIL — Authentication/authorization error")
        elif "ConfigurationError" in err_type:
            print(f"    FAIL — Invalid URI configuration: check MONGODB_URI format")
        else:
            print(f"    FAIL — {err_type}: (details hidden for security)")
        return False

def check_public_ip():
    """Show current public IP to help configure Atlas allowlist."""
    print(f"\n[5] Current public IP address...")
    try:
        import urllib.request
        ip = urllib.request.urlopen("https://api.ipify.org", timeout=10).read().decode()
        print(f"    Your public IP: {ip}")
        print(f"    >>> Add this IP to MongoDB Atlas Network Access:")
        print(f"    >>> https://cloud.mongodb.com -> Network Access -> Add IP Address -> {ip}/32")
        return ip
    except Exception:
        try:
            import urllib.request
            ip = urllib.request.urlopen("https://checkip.amazonaws.com", timeout=10).read().decode().strip()
            print(f"    Your public IP: {ip}")
            return ip
        except Exception as e:
            print(f"    Could not determine public IP: {type(e).__name__}")
            return None

def main():
    print("=" * 60)
    print("  MongoDB Atlas Connection Diagnostic")
    print("=" * 60)
    
    dns_ok = check_dns()
    tcp_ok = check_tcp() if dns_ok else False
    tls_ok = check_tls() if tcp_ok else False
    ip = check_public_ip()
    
    if tls_ok:
        pymongo_ok = check_pymongo_ping()
    else:
        print(f"\n[4] Skipping PyMongo ping — TLS handshake failed first")
        pymongo_ok = False
    
    print("\n" + "=" * 60)
    print("  DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print(f"  DNS resolution:    {'PASS' if dns_ok else 'FAIL'}")
    print(f"  TCP connection:    {'PASS' if tcp_ok else 'FAIL'}")
    print(f"  TLS handshake:     {'PASS' if tls_ok else 'FAIL'}")
    print(f"  PyMongo ping:      {'PASS' if pymongo_ok else 'FAIL' if tls_ok else 'SKIPPED'}")
    print("=" * 60)
    
    if not tls_ok:
        print("\n  ROOT CAUSE: MongoDB Atlas IP allowlist is blocking your connection.")
        print(f"  FIX REQUIRED: Add your public IP to Atlas Network Access.")
        if ip:
            print(f"\n  Steps:")
            print(f"  1. Go to: https://cloud.mongodb.com")
            print(f"  2. Select your project -> Network Access")
            print(f"  3. Click 'Add IP Address'")
            print(f"  4. Enter: {ip}/32")
            print(f"  5. Wait 30-60 seconds for changes to propagate")
            print(f"  6. Re-run this script to verify")
        sys.exit(1)
    elif pymongo_ok:
        print("\n  All checks passed. MongoDB Atlas connection is working.")
        sys.exit(0)
    else:
        print("\n  TLS is OK but PyMongo ping failed. Check credentials in .env.")
        sys.exit(1)

if __name__ == "__main__":
    main()
