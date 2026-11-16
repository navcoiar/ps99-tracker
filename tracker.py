import json
import os
import hashlib
from pathlib import Path

import requests

STATE_FILE = Path("state.json")
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
ROLE_ID = os.getenv("DISCORD_ROLE_ID", "").strip()

FFLAG_URL = "https://clientsettingscdn.roblox.com/v2/settings/application/PCDesktopClient"
PS99_EGGS_URL = "https://ps99.biggamesapi.io/api/collection/Eggs"
PS99_PETS_URL = "https://ps99.biggamesapi.io/api/collection/Pets"

HEADERS = {"User-Agent": "PS99-Community-Change-Tracker/1.0"}
TIMEOUT = 30


def get_json(url):
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and payload.get("status") == "error":
        raise RuntimeError(payload.get("error", {}).get("message", "API returned an error"))
    return payload


def stable_hash(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_fflags(payload):
    # Roblox's public settings endpoint normally returns a dictionary of flag values.
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        payload = payload["data"]
    if not isinstance(payload, dict):
        raise ValueError("Unexpected Roblox FFlags response format")
    return payload


def normalize_ps99_collection(payload, collection_name):
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError(f"Unexpected PS99 {collection_name} response format")
    result = {}
    for item in payload["data"]:
        if not isinstance(item, dict):
            continue
        name = item.get("configName")
        if name:
            result[str(name)] = item
    return result


def load_state():
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def compare(old, new):
    old_keys, new_keys = set(old), set(new)
    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    changed = sorted(k for k in old_keys & new_keys if stable_hash(old[k]) != stable_hash(new[k]))
    return added, changed, removed


def clip(value, limit=850):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= limit else text[:limit - 3] + "..."


def make_embed(title, added, changed, removed, old_data, new_data):
    lines = [
        f"🆕 **{len(added)} added**  |  🔄 **{len(changed)} changed**  |  ❌ **{len(removed)} removed**"
    ]
    for name in added[:8]:
        lines.append(f"🟢 Added: `{name}`")
        lines.append(f"New: `{clip(new_data.get(name), 300)}`")
    for name in changed[:8]:
        lines.append(f"🔄 Changed: `{name}`")
        lines.append(f"Old: `{clip(old_data.get(name), 260)}`")
        lines.append(f"New: `{clip(new_data.get(name), 260)}`")
    for name in removed[:8]:
        lines.append(f"🔴 Removed: `{name}`")
        lines.append(f"Old: `{clip(old_data.get(name), 300)}`")
    if len(added) + len(changed) + len(removed) > 8:
        lines.append("_Showing up to 8 entries per category._")
    description = "\n".join(lines)
    return {
        "title": title,
        "description": description[:4000],
        "color": 0x8B5CF6,
    }


def send_discord(embeds):
    if not embeds:
        return
    content = f"<@&{ROLE_ID}>" if ROLE_ID else ""
    payload = {
        "content": content,
        "embeds": embeds[:10],
        "allowed_mentions": {"parse": [], "roles": [ROLE_ID] if ROLE_ID else []},
    }
    response = requests.post(WEBHOOK_URL, json=payload, timeout=TIMEOUT)
    response.raise_for_status()


def main():
    previous = load_state()
    current = {}

    # Source 1: Roblox public desktop-client FastFlags.
    current["fflags"] = normalize_fflags(get_json(FFLAG_URL))

    # Source 2: PS99 configuration collections. Egg configs can contain
    # hatch/drop-table settings when the public API exposes them.
    current["ps99_eggs"] = normalize_ps99_collection(get_json(PS99_EGGS_URL), "Eggs")
    current["ps99_pets"] = normalize_ps99_collection(get_json(PS99_PETS_URL), "Pets")

    # First successful run establishes a baseline and does not spam Discord.
    if not previous:
        save_state(current)
        print("Initial baseline saved. No notification sent.")
        return

    labels = {
        "fflags": "Roblox FFlags Updated",
        "ps99_eggs": "PS99 Egg / Hatch Configuration Updated",
        "ps99_pets": "PS99 Pet Configuration Updated",
    }

    embeds = []
    for section, title in labels.items():
        old_data = previous.get(section, {})
        new_data = current[section]
        added, changed, removed = compare(old_data, new_data)
        if added or changed or removed:
            embeds.append(make_embed(title, added, changed, removed, old_data, new_data))

    if embeds:
        send_discord(embeds)
        print(f"Sent {len(embeds)} update embed(s).")
    else:
        print("No changes found.")

    save_state(current)


if __name__ == "__main__":
    main()
