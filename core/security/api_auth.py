from fastapi import Header, HTTPException


# H6 — HARDCODED API KEY REGISTRY (SAFE NOW)

# key → org mapping
API_KEYS = {
    "devsync_live_abc123": "devsync",
    # add more orgs later like:
    # "team_live_x82k2": "teamA"
}


# VALIDATE API KEY

def authenticate_request(x_api_key: str = Header(None)):
    """
    Validates incoming API key.
    Returns org name if valid.
    Blocks request if invalid.
    """

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key"
        )

    if x_api_key not in API_KEYS:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    org = API_KEYS[x_api_key]
    return org