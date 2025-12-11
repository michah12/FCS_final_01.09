"""
Data Persistence Module
Functions for loading and saving user data to JSON files
"""
import json
import os
from typing import List, Dict


def load_user_interactions(file_path: str) -> List[Dict]:
    """
    Loads the user's interaction history from a JSON file.
    We track every click, view, favorite action - basically everything they do.
    The ML model uses this to learn what they like.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_user_interactions(interactions: List[Dict], file_path: str):
    """
    Saves the interaction history back to the JSON file.
    Creates the data folder if it doesn't exist yet.
    """
    os.makedirs('data', exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(interactions, f, indent=2)


def load_user_inventory(file_path: str) -> List[Dict]:
    """
    Loads the user's saved perfume collection.
    This persists between sessions so they don't lose their stuff.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_user_inventory(inventory: List[Dict], file_path: str):
    """
    Saves the user's perfume collection to disk.
    Gets called whenever they add or remove a perfume.
    """
    os.makedirs('data', exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(inventory, f, indent=2)


def load_perfume_rankings(file_path: str) -> Dict:
    """
    Loads the popularity rankings for perfumes.
    Higher score = more people have interacted with it.
    Used to break ties in recommendations.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_perfume_rankings(rankings: Dict, file_path: str):
    """
    Saves the popularity rankings back to disk.
    Gets updated every time someone clicks on a perfume.
    """
    os.makedirs('data', exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(rankings, f, indent=2)

