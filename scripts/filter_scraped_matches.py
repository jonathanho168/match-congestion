import pandas as pd
import re

def normalize(name):
    # drop any parenthetical "(...)" tags
    name = re.sub(r'\s*\([^)]*\)', '', name)
    # # remove dots
    # name = name.replace('.', '')
    # # collapse whitespace & lowercase
    # name = re.sub(r'\s+', '', name).strip().lower()
    return name

# ── LOAD DATA ────────────────────────────────────────────────────────────────
matches = pd.read_csv('../results/all_spain_matches.csv')
teams   = pd.read_csv('../results/spain_flashscore_teams.csv')['Team'].astype(str).tolist()

# ── NORMALIZE CANONICAL TEAMS ────────────────────────────────────────────────
teams_norm = {normalize(t): t for t in teams}

# ── EXPLODE & FILTER ─────────────────────────────────────────────────────────
rows = []
for _, row in matches.iterrows():

    raw_name = row['team']
    iso_date = row['iso_date'] 
    norm     = normalize(raw_name)
    if norm in teams_norm:
        rows.append({
            'team': teams_norm[norm],   # original canonical spelling
            'date': iso_date
        })

# ── OUTPUT ─────────────────────────────────────────────────────────────────
out = pd.DataFrame(rows)
out.to_csv('../results/filtered_spain_matches.csv', index=False)

print(f"→ Found {len(out)} total entries.")
print(out.to_string(index=False))
