import json
import pandas as pd
import re
import os
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

# --- New Singles Results Processing --- #

def collect_singles_results(root_dir: str, filename: str = "singles-results.csv") -> list:
    """Recursively collects all singles results CSV file paths from a given root directory."""
    return list(Path(root_dir).rglob(filename))

def load_singles_results(file_paths: list) -> pd.DataFrame:
    print("HERE")
    """Load and clean all singles results CSVs."""
    all_results = []
    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path)
            print("BROKEN?")
            # Proceed with cleaning logic as before
            cleaned_data = []  # Empty list to store cleaned data for each match
            for index, row in df.iterrows():
                print("ROW: ", row)
                # Check if the value in the specific column is NaN
                if pd.isna(row[df.columns[2]]):
                    print(f"Warning: NaN value found in {file_path} at index {index}, skipping row.")
                    continue  # Skip this row or handle it as needed
                print("NAME: ", row[df.columns[2]])
                winner_name = clean_name(row[df.columns[2]])  # Winner's name from column C (index 2)
                print("NAME: ", winner_name)
                winner_peak_rank = row[df.columns[19]]  # Winner's peak rank from column T (index 19)
                print("RANK: ", winner_peak_rank)

                # Extracting loser stats from columns N-R (indices 13-17)
                loser_stats = []
                for i in range(13, 18):
                    loser_stats.append(row[df.columns[i]])

                # Append cleaned data for this match
                cleaned_data.append({
                    'Winner Name': winner_name,
                    'Winner Peak Rank': winner_peak_rank,
                    'Loser Ace%': loser_stats[0],
                    'Loser 1st%': loser_stats[1],
                    'Loser 2nd%': loser_stats[2],
                    'Loser BPSvd': loser_stats[3],
                    'Loser Time': loser_stats[4] if len(loser_stats) > 4 else 'N/A'
                })
            all_results.append(pd.DataFrame(cleaned_data))
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    return pd.concat(all_results, ignore_index=True)

# Function to clean up player name format
def clean_name(name):
    """Remove extra information like "[RUS]" or "[yr|ev]" and trim spaces."""
    name = re.sub(r'\[.*?\]', '', name)  # Remove content inside brackets
    name = name.strip()  # Remove leading/trailing spaces
    return name

# Function to extract loser stats from the score string
def extract_loser_stats(loser_data):
    """Extract relevant loser stats from the 'Score' column."""
    loser_stats = []
    if 'L:' in loser_data:
        # Split the string after 'L:' to extract stats
        loser_stats_raw = loser_data.split('L:')[1].split(',')
        loser_stats = [stat.strip() for stat in loser_stats_raw]

    # Ensure exactly 5 stats are extracted: Ace%, 1st%, 2nd%, BPSvd, Time
    if len(loser_stats) >= 5:
        loser_stats = loser_stats[:5]  # First 5 values are relevant
    
    return loser_stats

# Function to process the singles results
def process_singles_results(df):
    # List to store cleaned data
    cleaned_data = []

    # Iterate through the rows of the dataframe
    for index, row in df.iterrows():
        winner_name = clean_name(row[df.columns[2]])  # Winner's name in column C (index 2)
        winner_peak_rank = row[df.columns[19]]  # Winner's peak rank in column T (index 19)

        # Extracting loser stats from columns N to R (indices 13-17)
        loser_stats = [
            row[df.columns[13]],  # Ace%
            row[df.columns[14]],  # 1st%
            row[df.columns[15]],  # 2nd%
            row[df.columns[16]],  # BPSvd
            row[df.columns[17]]   # Time
        ]
        
        # Append the cleaned data for this match
        cleaned_data.append({
            'Winner Name': winner_name,
            'Winner Peak Rank': winner_peak_rank,
            'Loser Ace%': loser_stats[0],
            'Loser 1st%': loser_stats[1],
            'Loser 2nd%': loser_stats[2],
            'Loser BPSvd': loser_stats[3],
            'Loser Time': loser_stats[4] if len(loser_stats) > 4 else 'N/A'
        })
        
    # Create a DataFrame from the cleaned data
    cleaned_df = pd.DataFrame(cleaned_data)
    
    return cleaned_df

# Function to save the cleaned data to a CSV file
def save_cleaned_data(df, output_file):
    """Save the cleaned data to a new CSV file."""
    df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")

def main():
    root_folder = "tennis_data/us_open"
    stat_output_csv = "aggregated_us_open_stats.csv"
    singles_output_csv = "processed_singles_results.csv"

    print("🔍 Searching for stat summaries...")
    stat_files = collect_stat_files(root_folder)
    print(f"📁 Found {len(stat_files)} stat files.")

    print("📊 Loading and filtering data for stat summaries...")
    raw_df = load_and_filter_stats(stat_files)

    print("🔄 Aggregating player stats...")
    aggregated_df = aggregate_player_stats(raw_df)

    print("📈 Merging peak rank data for stat summaries...")
    rank_df = load_peak_ranks("rank_cache.json")
    aggregated_df = aggregated_df.merge(rank_df, on="Player", how="left")
    aggregated_df["PeakRank"] = pd.to_numeric(aggregated_df["PeakRank"], errors="coerce")

    print("💾 Saving aggregated stat summaries to output...")
    save_aggregated_stats(aggregated_df, stat_output_csv)

    # --- Process singles results ---
    print("🔍 Searching for singles results files...")
    singles_files = collect_singles_results(root_folder)
    print(f"📁 Found {len(singles_files)} singles result files.")

    print("📊 Loading and cleaning singles results data...")
    singles_results_df = load_singles_results(singles_files)

    print("💾 Saving cleaned singles results data...")
    singles_results_df.to_csv(singles_output_csv, index=False)
    print("Cleaned singles results saved to cleaned_singles_results.csv")



if __name__ == "__main__":
    main()
