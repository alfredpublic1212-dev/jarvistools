from pathlib import Path
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

POLICY_DIR = Path("core/org_policies")


def verify_policy_signature(org: str) -> bool:
    """
    Verifies org policy signature using PUBLIC KEY from ENV.
    Enterprise-grade verification.
    """

    policy_path = POLICY_DIR / f"{org}.json"
    sig_path = POLICY_DIR / f"{org}.sig"

    if not policy_path.exists():
        raise Exception(f"[SECURITY] Policy file missing: {policy_path}")

    if not sig_path.exists():
        raise Exception(f"[SECURITY] Signature missing for org: {org}")

    # 🔐 LOAD PUBLIC KEY FROM ENV (not file)
    public_key_pem = os.getenv("POLICY_PUBLIC_KEY")
    if not public_key_pem:
        raise Exception("[SECURITY] POLICY_PUBLIC_KEY not set on server")

    public_key = serialization.load_pem_public_key(
        public_key_pem.encode()
    )

    data = policy_path.read_bytes()
    signature = sig_path.read_bytes()

    try:
        public_key.verify(
            signature,
            data,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True

    except InvalidSignature:
        raise Exception(f"[SECURITY] INVALID POLICY SIGNATURE for org: {org}")