import re
from typing import Any, Dict, Iterable, Set, Tuple


EMAIL_DOMAIN_PATTERN = re.compile(r".+@(?P<domain>.+)$")


def get_email_domain(email: str) -> str | None:
    """Extract the domain portion from an email address."""
    match = EMAIL_DOMAIN_PATTERN.match(email)
    if match:
        return match.groupdict()["domain"]
    return None


def parse_user_map(user_map: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, str], Set[str]]:
    """Build speaker labels and participant email domains from a user map."""
    speaker_labels: Dict[str, str] = {}
    domains: Set[str] = set()

    for user_id, info in user_map.items():
        speaker_labels[user_id] = info["name"]
        email = info.get("email")
        if email:
            domain = get_email_domain(email)
            if domain:
                domains.add(domain)

    return speaker_labels, domains

