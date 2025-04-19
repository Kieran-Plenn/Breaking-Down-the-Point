# Breaking Down the Point
# Author: Kieran Plenn

import pandas as pd
import numpy as np

# Load your dataframe
df = pd.read_csv('player_data_m.csv')

# Select only relevant columns
selected_prefixes = ['mcp-tactics', 'mcp-serve', 'mcp-return', 'mcp-rally']
selected_columns = ['peak_rank'] + [col for col in df.columns if any(prefix in col for prefix in selected_prefixes)]
subset_df = df[selected_columns].copy()

# Clean column names
subset_df.columns = (
    subset_df.columns
    .str.replace(r'[^\w\s]', '', regex=True)
    .str.replace(r'\s+', '_', regex=True)
    .str.lower()
)

# Replace dash with NaN and convert strings to float
subset_df.replace('-', np.nan, inplace=True)
for col in subset_df.columns:
    if subset_df[col].dtype == 'object':
        subset_df[col] = subset_df[col].str.replace('%', '', regex=False)
        subset_df[col] = pd.to_numeric(subset_df[col], errors='coerce')

# Drop rows with missing values
cleaned_df = subset_df.dropna()

# Correlation with peak_rank
correlation = cleaned_df.corr(numeric_only=True)['peak_rank'].sort_values()
print(correlation)

