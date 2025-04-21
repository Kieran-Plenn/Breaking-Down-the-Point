import csv
import json
import os

# === CONFIG ===
csv_path = r"C:\Users\kiera\OneDrive\Desktop\Breaking Down the Point\player_data.csv"
json_cache_path = "rank_cache.json"  # Adjust if your JSON is elsewhere
player_name_column = 1  # Column B (zero-indexed as 1)
peak_rank_column = 3    # Column D (zero-indexed as 3)

# === LOAD EXISTING CACHE (IF ANY) ===
if os.path.exists(json_cache_path):
    with open(json_cache_path, "r", encoding="utf-8") as f:
        rank_cache = json.load(f)
else:
    rank_cache = {}

# === IMPORT FROM CSV ===
added_count = 0
skipped_count = 0

with open(csv_path, "r", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)  # Skip header

    for row in reader:
        if len(row) <= max(player_name_column, peak_rank_column):
            continue  # Skip incomplete rows

        name = row[player_name_column].strip()
        peak_rank = row[peak_rank_column].strip()

        if name and peak_rank and name not in rank_cache:
            if peak_rank.isdigit():  # Only accept numeric peak ranks
                rank_cache[name] = peak_rank
                added_count += 1
        else:
            skipped_count += 1

# === SAVE UPDATED CACHE ===
with open(json_cache_path, "w", encoding="utf-8") as f:
    json.dump(rank_cache, f, indent=4)

print(f"✅ Done! Added {added_count} new players to cache.")
print(f"⏩ Skipped {skipped_count} already existing or invalid entries.")
