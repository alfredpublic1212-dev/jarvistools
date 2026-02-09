#security/sign_policy.py
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# YOUR REAL PATHS
PRIVATE_KEY_PATH = Path("keys/private.pem")
POLICY_PATH = Path("core/org_policies/devsync.json")
SIG_PATH = Path("core/org_policies/devsync.sig")

def main():
    print("Loading private key...")
    private_key = serialization.load_pem_private_key(
        PRIVATE_KEY_PATH.read_bytes(),
        password=None
    )

    print("Signing policy...")
    data = POLICY_PATH.read_bytes()

    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    SIG_PATH.write_bytes(signature)

    print("")
    print("SUCCESS")
    print("Policy signed.")
    print("File created:", SIG_PATH)

if __name__ == "__main__":
    main()