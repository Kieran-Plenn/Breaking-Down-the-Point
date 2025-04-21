import pandas as pd
from pathlib import Path

COLUMNS_TO_KEEP = [
    'Player', 'M', 'Hld%', 'Brk%', 'A', 'Ace%', 'DF', 'DF%', '1stIn', '1st%',
    '2nd%', 'SPW', 'BPFaced', 'BPSvd%', 'RPW', 'BPEarned', 'BPConv%', 'TPW', 'DR'
]

def collect_stat_files(root_dir: str, filename: str = "stat-summaries.csv") -> list:
    """Recursively collects all stat summary CSV file paths from a given root directory."""
    return list(Path(root_dir).rglob(filename))


def load_and_filter_stats(file_paths: list) -> pd.DataFrame:
    """Loads all relevant stat CSVs and keeps only the desired columns."""
    all_dfs = []
    for path in file_paths:
        try:
            df = pd.read_csv(path)
            df = df[COLUMNS_TO_KEEP].copy()
            # Convert all columns (except Player) to numeric
            for col in df.columns:
                if col != 'Player':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
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

    print("💾 Saving to output...")
    save_aggregated_stats(aggregated_df, output_csv)


if __name__ == "__main__":
    main()
