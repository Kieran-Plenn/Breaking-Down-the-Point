import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_squared_error, accuracy_score, classification_report,
    precision_score, recall_score, f1_score
)
from sklearn.ensemble import RandomForestClassifier


def load_and_clean_data(filepath):
    df = pd.read_csv(filepath)
    print(f"Initial data shape: {df.shape}")

    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=['PeakRank'])
    df = df.dropna(how='all')

    print(f"Missing values after cleaning:\n{df.isnull().sum()}")
    print(f"Data shape after dropping rows with missing PeakRank and empty rows: {df.shape}")

    df['weighted_peakrank'] = df['PeakRank'] / df['M']

    percent_cols = ['Hld%', 'Brk%', 'Ace%', 'DF%', '1stIn', '1st%', '2nd%', 'SPW', 'BPSvd%', 'RPW', 'BPConv%', 'TPW']
    numeric_cols = ['A', 'DF', 'BPFaced', 'BPEarned', 'DR']
    cols_to_normalize = [col for col in (percent_cols + numeric_cols) if col in df.columns]

    scaler = StandardScaler()
    df[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])

    df.attrs['exclude_cols'] = ['Player', 'PeakRank', 'weighted_peakrank', 'M']
    return df


def plot_correlation_heatmap(df):
    target = 'weighted_peakrank'  # or 'PeakRank' if you want the original

    df_numeric = df.select_dtypes(include=['number']).drop(columns=['M'], errors='ignore')
    correlation_matrix = df_numeric.corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title("Correlation Heatmap")
    plt.show()

    if target in correlation_matrix.columns:
        top_corr = correlation_matrix[target].sort_values(ascending=False).head(10)
        print(f"Top Correlated Features with {target}:")
        print(top_corr)
    else:
        print(f"'{target}' not found in correlation matrix columns. Available columns: {correlation_matrix.columns.tolist()}")


def exploratory_plots(df):
    plot_cols = ['Hld%', 'Brk%']
    for col in plot_cols:
        if col in df.columns:
            plt.scatter(df[col], df['PeakRank'])
            plt.title(f'{col} vs PeakRank')
            plt.xlabel(col)
            plt.ylabel('PeakRank')
            plt.show()


def run_regression(df):
    X = df.drop(columns=df.attrs['exclude_cols'])
    y = df['weighted_peakrank']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Linear Regression MSE: {mse:.4f}")


def classify_elite(df, elite_cutoff=10):
    X = df.drop(columns=df.attrs['exclude_cols'])
    y = (df['weighted_peakrank'] <= elite_cutoff).astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"Random Forest Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall: {recall_score(y_test, y_pred):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred):.4f}")

    importance = model.feature_importances_
    features = X.columns
    imp_df = pd.DataFrame({'Feature': features, 'Importance': importance}).sort_values(by='Importance', ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=imp_df)
    plt.title("Feature Importance from Random Forest")
    plt.show()


def categorize_and_classify(df):
    bins = [0, 3, 20, 50, df['weighted_peakrank'].max() + 1]
    labels = ['1-3', '4-20', '21-50', '51+']
    df['PeakRankCategory'] = pd.cut(df['weighted_peakrank'], bins=bins, labels=labels, right=False)
    df = df.dropna(subset=['PeakRankCategory', 'M'])

    exclude_cols = df.attrs['exclude_cols'] + ['PeakRankCategory']
    X = pd.get_dummies(df.drop(columns=exclude_cols))
    y = df['PeakRankCategory']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"Multiclass Accuracy: {model.score(X_test, y_test):.4f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    importances = model.feature_importances_
    imp_df = pd.DataFrame({'Feature': X.columns, 'Importance': importances}).sort_values(by='Importance', ascending=False)
    print("Feature Importances:\n", imp_df)
    print("Player count per category:\n", df['PeakRankCategory'].value_counts().sort_index())


def main():
    filepath = 'aggregated_us_open_stats.csv'
    df = load_and_clean_data(filepath)

    plot_correlation_heatmap(df)
    exploratory_plots(df)

    print("\n--- Linear Regression ---")
    run_regression(df)

    print("\n--- Binary Classification: Elite vs Non-Elite ---")
    classify_elite(df)

    print("\n--- Multiclass Classification (Custom Categories) ---")
    categorize_and_classify(df)


if __name__ == "__main__":
    main()
