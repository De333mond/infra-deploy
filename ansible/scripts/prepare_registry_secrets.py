#!/usr/bin/env python3
"""Prepare local TLS and htpasswd files for the internal registry."""

import argparse
import ipaddress
import os
from pathlib import Path
import secrets
import subprocess
import tempfile

import bcrypt


REGISTRY_DNS = "registry.registry.svc.cluster.local"


def run(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def require_pair(first: Path, second: Path) -> bool:
    if first.exists() != second.exists():
        raise SystemExit(f"Restore or remove both {first.name} and {second.name}.")
    return first.exists()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("local_directory", type=Path)
    parser.add_argument("node_ip", type=ipaddress.ip_address)
    args = parser.parse_args()

    directory = args.local_directory.resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory.chmod(0o700)
    os.umask(0o077)

    ca_cert = directory / "ca.crt"
    ca_key = directory / "ca.key"
    if not require_pair(ca_cert, ca_key):
        raise SystemExit("Create the registry CA with playbooks/registry-mirror.yaml first.")

    server_cert = directory / "server.crt"
    server_key = directory / "server.key"
    created = False
    if require_pair(server_cert, server_key):
        run("openssl", "verify", "-CAfile", str(ca_cert), str(server_cert))
        run("openssl", "x509", "-in", str(server_cert), "-noout", "-checkend", "2592000")
        details = run("openssl", "x509", "-in", str(server_cert), "-noout", "-ext", "subjectAltName")
        if f"DNS:{REGISTRY_DNS}" not in details or f"IP Address:{args.node_ip}" not in details:
            raise SystemExit("Registry certificate SAN differs from the current node IP; renew server.crt and server.key.")
    else:
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            temp = Path(temporary)
            csr = temp / "server.csr"
            extensions = temp / "server.ext"
            extensions.write_text(
                "basicConstraints=critical,CA:FALSE\n"
                "keyUsage=critical,digitalSignature,keyEncipherment\n"
                "extendedKeyUsage=serverAuth\n"
                f"subjectAltName=DNS:{REGISTRY_DNS},IP:{args.node_ip}\n"
            )
            run(
                "openssl", "req", "-new", "-newkey", "rsa:3072", "-nodes",
                "-subj", f"/CN={REGISTRY_DNS}", "-keyout", str(temp / "server.key"),
                "-out", str(csr),
            )
            run(
                "openssl", "x509", "-req", "-in", str(csr), "-CA", str(ca_cert),
                "-CAkey", str(ca_key), "-CAcreateserial", "-days", "365", "-sha256",
                "-extfile", str(extensions), "-out", str(temp / "server.crt"),
            )
            os.replace(temp / "server.key", server_key)
            os.replace(temp / "server.crt", server_cert)
            created = True

    server_key.chmod(0o600)
    server_cert.chmod(0o600)

    password_file = directory / "password"
    if not password_file.exists():
        password_file.write_text(secrets.token_urlsafe(36) + "\n")
        created = True
    password_file.chmod(0o600)
    password = password_file.read_text().strip().encode()

    htpasswd_file = directory / "htpasswd"
    if htpasswd_file.exists():
        line = htpasswd_file.read_bytes().strip()
        if not line.startswith(b"registry:") or not bcrypt.checkpw(password, line.split(b":", 1)[1]):
            raise SystemExit("Existing htpasswd does not match local/registry/password.")
    else:
        htpasswd_file.write_bytes(b"registry:" + bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)) + b"\n")
        created = True
    htpasswd_file.chmod(0o600)
    print("created" if created else "unchanged")


if __name__ == "__main__":
    main()
