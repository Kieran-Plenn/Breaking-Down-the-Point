import json
import pandas as pd
from pathlib import Path

COLUMNS_TO_KEEP = [
    'Player', 'M', 'Hld%', 'Brk%', 'A', 'Ace%', 'DF', 'DF%', '1stIn', '1st%',
    '2nd%', 'SPW', 'BPFaced', 'BPSvd%', 'RPW', 'BPEarned', 'BPConv%', 'TPW', 'DR'
]

PERCENT_COLUMNS = ['Hld%', 'Brk%', 'Ace%', 'DF%', '1stIn', '1st%', '2nd%', 'SPW', 'BPSvd%', 'RPW', 'BPConv%', 'TPW']

def collect_stat_files(root_dir: str, filename: str = "stat-summaries.csv") -> list:
    """Recursively collects all stat summary CSV file paths from a given root directory."""
    return list(Path(root_dir).rglob(filename))

# Load peak ranks from rank_cache.json
def load_peak_ranks(json_path="rank_cache.json") -> pd.DataFrame:
    def safe_int(value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return None  # Or set to -1 or 9999 if you prefer a placeholder

    with open(json_path, "r") as f:
        rank_data = json.load(f)

    rank_df = pd.DataFrame(
        [{"Player": name, "PeakRank": safe_int(rank)} for name, rank in rank_data.items()]
    )
    return rank_df

def load_and_filter_stats(file_paths: list) -> pd.DataFrame:
    """Loads all relevant stat CSVs and keeps only the desired columns."""
    all_dfs = []
    for path in file_paths:
        try:
            df = pd.read_csv(path)
            df = df[COLUMNS_TO_KEEP].copy()
            # Drop any summary rows like "All Main Draw Players"
            df = df[df['Player'] != 'All Main Draw Players']
            # Convert all columns (except Player) to numeric
            for col in df.columns:
                if col == 'Player':
                    continue
                if col in PERCENT_COLUMNS:
                    # First, remove '%' and any stray whitespace
                    df[col] = df[col].astype(str).str.replace('%', '').str.strip()
                    # Now convert to float
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    # Then divide by 100 to convert to decimal
                    df[col] = df[col] / 100
                else:
                    # For non-percent columns, just convert directly
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Fill any NaNs with 0
                df[col] = df[col].fillna(0)
            all_dfs.append(df)
        except Exception as e:
            print(f"Skipping file {path} due to error: {e}")
    return pd.concat(all_dfs, ignore_index=True)


def aggregate_player_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Groups by player and averages all numerical columns (except matches, which are summed)."""
    aggregation_functions = {col: 'mean' for col in df.columns if col != 'Player' and col != 'M'}
    aggregation_functions['M'] = 'sum'
    return df.groupby('Player', as_index=False).agg(aggregation_functions)


def save_aggregated_stats(df: pd.DataFrame, output_path: str):
    """Saves the aggregated stats to a CSV."""
    df.to_csv(output_path, index=False)
    print(f"Aggregated player stats saved to {output_path}")


def main():
    root_folder = "tennis_data/us_open"
    output_csv = "aggregated_us_open_stats.csv"

    print("🔍 Searching for stat summaries...")
    stat_files = collect_stat_files(root_folder)
    print(f"📁 Found {len(stat_files)} files.")

    print("📊 Loading and filtering data...")
    raw_df = load_and_filter_stats(stat_files)

    print("🔄 Aggregating player stats...")
    aggregated_df = aggregate_player_stats(raw_df)

    print("📈 Merging peak rank data...")
    rank_df = load_peak_ranks("rank_cache.json")
    aggregated_df = aggregated_df.merge(rank_df, on="Player", how="left")
    aggregated_df["PeakRank"] = pd.to_numeric(aggregated_df["PeakRank"], errors="coerce")

    print("💾 Saving to output...")
    save_aggregated_stats(aggregated_df, output_csv)


if __name__ == "__main__":
    main()
