from pathlib import Path
import os
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

POLICY_DIR = Path("core/org_policies")

def verify_policy_signature(org: str) -> bool:
    """
    Verifies org policy signature using PUBLIC KEY from ENV.
    """

    print("\n====== POLICY VERIFY DEBUG ======")

    policy_path = POLICY_DIR / f"{org}.json"
    sig_path = POLICY_DIR / f"{org}.sig"

    print("ORG:", org)
    print("POLICY PATH:", policy_path.resolve())
    print("SIG PATH:", sig_path.resolve())
    print("POLICY EXISTS:", policy_path.exists())
    print("SIG EXISTS:", sig_path.exists())

    public_key_pem = os.getenv("POLICY_PUBLIC_KEY")

    if not public_key_pem:
        raise Exception("POLICY_PUBLIC_KEY missing in Render env")

    print("ENV PUBLIC KEY FOUND: YES")

    #  show first part of public key
    print("PUBLIC KEY FIRST 80 CHARS:")
    print(public_key_pem[:80])

    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode()
        )
        print("PUBLIC KEY LOADED SUCCESS")
    except Exception as e:
        raise Exception(f"PUBLIC KEY LOAD FAILED: {e}")

    if not policy_path.exists():
        raise Exception(f"[SECURITY] Policy file missing: {policy_path}")

    if not sig_path.exists():
        raise Exception(f"[SECURITY] Signature missing for org: {org}")

    data = policy_path.read_bytes()
    signature = sig_path.read_bytes()

    print("SIGNATURE SIZE:", len(signature))
    print("POLICY SHA256:", hashlib.sha256(data).hexdigest())
    print("SIG SHA256:", hashlib.sha256(signature).hexdigest())

    try:
        public_key.verify(
            signature,
            data,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        print("SIGNATURE VALID")
        print("=================================\n")
        return True

    except InvalidSignature:
        print("SIGNATURE INVALID")
        raise Exception(f"[SECURITY] INVALID POLICY SIGNATURE for org: {org}")