import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA
from sklearn.metrics import (
    accuracy_score, classification_report,
    precision_score, recall_score, f1_score
)

def load_and_clean_data(filepath):
    df = pd.read_csv(filepath)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=['PeakRank'])
    df = df.dropna(how='all')
    df['weighted_peakrank'] = df['PeakRank'] / df['M']

    percent_cols = ['Hld%', 'Brk%', 'Ace%', 'DF%', '1stIn', '1st%', '2nd%', 'SPW', 'BPSvd%', 'RPW', 'BPConv%', 'TPW']
    numeric_cols = ['A', 'DF', 'BPFaced', 'BPEarned', 'DR']
    cols_to_normalize = [col for col in (percent_cols + numeric_cols) if col in df.columns]

    scaler = StandardScaler()
    df[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])
    return df

def classify_elite(df, elite_cutoff=10):
    X = StandardScaler().fit_transform(df.drop(columns=['Player', 'PeakRank']))
    y = (df['PeakRank'] <= elite_cutoff).astype(int)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    accuracy_scores, precision_scores, recall_scores, f1_scores_list = [], [], [], []

    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        accuracy_scores.append(accuracy_score(y_test, y_pred))
        precision_scores.append(precision_score(y_test, y_pred))
        recall_scores.append(recall_score(y_test, y_pred))
        f1_scores_list.append(f1_score(y_test, y_pred))

    print("\n--- Binary Classification (Elite vs Non-Elite) ---")
    print(f"Accuracy: {np.mean(accuracy_scores):.4f}")
    print(f"Precision: {np.mean(precision_scores):.4f}")
    print(f"Recall: {np.mean(recall_scores):.4f}")
    print(f"F1 Score: {np.mean(f1_scores_list):.4f}")

def categorize_and_classify(df):
    bins = [0, 10, 30, 50, 75, df['PeakRank'].max() + 1]
    labels = ['Elite', 'Semi-Elite', 'Top 50', 'Top 100', 'Other']
    df['PeakRankCategory'] = pd.cut(df['PeakRank'], bins=bins, labels=labels, right=False)

    df = df.dropna(subset=['PeakRankCategory', 'M'])
    X = pd.get_dummies(df.drop(columns=['Player', 'PeakRank', 'PeakRankCategory']))
    y = df['PeakRankCategory']

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    accuracy_scores = []

    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = RandomForestClassifier(random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        accuracy_scores.append(accuracy_score(y_test, y_pred))

    print("\n--- Multiclass Classification (Rank Categories) ---")
    print(f"Multiclass Accuracy: {np.mean(accuracy_scores):.4f}")
    print("Classification Report:\n", classification_report(y_test, y_pred))

def run_pca(df, n_components=2):
    X = df.drop(columns=['Player', 'PeakRank', 'PeakRankCategory'], errors='ignore')
    X = X.select_dtypes(include=[np.number])
    X_scaled = StandardScaler().fit_transform(X)

    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    df_pca = pd.DataFrame(X_pca, columns=[f'PC{i+1}' for i in range(n_components)])
    df_pca['PeakRank'] = df['PeakRank'].values
    df_pca['PeakRankCategory'] = pd.cut(df['PeakRank'], bins=[0, 3, 20, 50, df['PeakRank'].max()+1],
                                        labels=['1-3', '4-20', '21-50', '51+'], right=False)

    print("\n--- PCA Analysis ---")
    print(f"Explained variance: {pca.explained_variance_ratio_}")
    print(f"Cumulative explained variance: {np.cumsum(pca.explained_variance_ratio_)}")

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_pca, x='PC1', y='PC2', hue='PeakRankCategory', palette='Set2', alpha=0.7)
    plt.title('PCA of Player Stats (colored by Rank Category)')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    loadings = pd.DataFrame(pca.components_.T, index=X.columns, columns=[f'PC{i+1}' for i in range(n_components)])
    print("\nTop contributing features to PC1:")
    print(loadings['PC1'].sort_values(ascending=False).head(10))

def main():
    filepath = 'aggregated_us_open_stats.csv'
    df = load_and_clean_data(filepath)
    classify_elite(df)
    categorize_and_classify(df)
    run_pca(df)

if __name__ == "__main__":
    main()
