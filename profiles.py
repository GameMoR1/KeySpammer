import os
import json
from pathlib import Path

PROFILES_DIR = str(Path.home() / "KeySpammer")
PROFILES_FILE = os.path.join(PROFILES_DIR, "config.json")

def ensure_profiles_dir():
    os.makedirs(PROFILES_DIR, exist_ok=True)

def load_profiles():
    ensure_profiles_dir()
    if not os.path.exists(PROFILES_FILE):
        return {}
    with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_profiles(profiles):
    ensure_profiles_dir()
    with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=4)

def get_profile(name):
    profiles = load_profiles()
    return profiles.get(name)

def add_or_update_profile(name, key, speed, mode, target_title=None):
    profiles = load_profiles()
    profiles[name] = {
        "key": key,
        "speed": speed,
        "mode": mode,
        "target_title": target_title
    }
    save_profiles(profiles)

def delete_profile(name):
    profiles = load_profiles()
    if name in profiles:
        del profiles[name]
        save_profiles(profiles)
        return True
    return False
