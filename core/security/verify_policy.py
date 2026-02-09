#security/verify_policy.py
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature


PUBLIC_KEY_PATH = Path("core/security/public.pem")
POLICY_DIR = Path("core/org_policies")


def verify_policy_signature(org: str) -> bool:
    """
    Verifies that org policy JSON has valid signature.
    Enterprise security check.
    """

    policy_path = POLICY_DIR / f"{org}.json"
    sig_path = POLICY_DIR / f"{org}.sig"

    if not policy_path.exists():
        raise Exception(f"[SECURITY] Policy file missing: {policy_path}")

    if not sig_path.exists():
        raise Exception(f"[SECURITY] Signature missing for org: {org}")

    public_key = serialization.load_pem_public_key(
        PUBLIC_KEY_PATH.read_bytes()
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