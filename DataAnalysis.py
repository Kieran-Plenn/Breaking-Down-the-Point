import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import (
    accuracy_score, classification_report,
    precision_score, recall_score, f1_score,
    confusion_matrix, ConfusionMatrixDisplay
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

    feature_importances = np.zeros(X.shape[1])
    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        feature_importances += model.feature_importances_

        accuracy_scores.append(accuracy_score(y_test, y_pred))
        precision_scores.append(precision_score(y_test, y_pred))
        recall_scores.append(recall_score(y_test, y_pred))
        f1_scores_list.append(f1_score(y_test, y_pred))

    print("\n--- Binary Classification (Elite vs Non-Elite) ---")
    print(f"Accuracy: {np.mean(accuracy_scores):.4f}")
    print(f"Precision: {np.mean(precision_scores):.4f}")
    print(f"Recall: {np.mean(recall_scores):.4f}")
    print(f"F1 Score: {np.mean(f1_scores_list):.4f}")

    feature_cols = df.drop(columns=['Player', 'PeakRank']).columns
    avg_importance = feature_importances / 5
    fi_df = pd.DataFrame({'Feature': feature_cols, 'Importance': avg_importance})

    # Drop unwanted features from the importance plot
    fi_df = fi_df[~fi_df['Feature'].isin(['weighted_peakrank', 'M'])]
    fi_df = fi_df.sort_values(by='Importance', ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=fi_df.head(15), x='Importance', y='Feature', palette='viridis')
    plt.title('Top 15 Feature Importances (Elite Classification)')
    plt.tight_layout()
    plt.show()

def categorize_and_classify(df):
    bins = [0, 15, 40, 75, df['PeakRank'].max() + 1]
    labels = ['Top 15', 'Top 40', 'Top 75', 'Other']
    df['PeakRankCategory'] = pd.cut(df['PeakRank'], bins=bins, labels=labels, right=False)

    df = df.dropna(subset=['PeakRankCategory', 'M'])
    X = pd.get_dummies(df.drop(columns=['Player', 'PeakRank', 'PeakRankCategory']))
    y = df['PeakRankCategory']

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    accuracy_scores = []
    final_y_test = final_y_pred = None

    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = RandomForestClassifier(random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        accuracy_scores.append(accuracy_score(y_test, y_pred))
        final_y_test, final_y_pred = y_test, y_pred

    print("\n--- Multiclass Classification (Rank Categories) ---")
    print(f"Multiclass Accuracy: {np.mean(accuracy_scores):.4f}")
    print("Classification Report:\n", classification_report(final_y_test, final_y_pred))

    cm = confusion_matrix(final_y_test, final_y_pred, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)

    plt.figure(figsize=(8, 6))
    disp.plot(cmap='Blues', xticks_rotation=45, values_format='d')
    plt.title("Confusion Matrix - Multiclass Rank Prediction")
    plt.tight_layout()
    plt.show()

def run_pca(df, n_components=2):
    X = df.drop(columns=['Player', 'PeakRank', 'PeakRankCategory'], errors='ignore')
    X = X.select_dtypes(include=[np.number])
    X_scaled = StandardScaler().fit_transform(X)

    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    df_pca = pd.DataFrame(X_pca, columns=[f'PC{i+1}' for i in range(n_components)])
    df_pca['PeakRank'] = df['PeakRank'].values
    bins = [0, 15, 40, 75, df['PeakRank'].max() + 1]
    labels = ['Top 15', 'Top 40', 'Top 75', 'Other']
    df_pca['PeakRankCategory'] = pd.cut(df['PeakRank'], bins=bins, labels=labels, right=False)

    print("\n--- PCA Analysis ---")
    print(f"Explained variance: {pca.explained_variance_ratio_}")
    print(f"Cumulative explained variance: {np.cumsum(pca.explained_variance_ratio_)}")

    # PCA scatterplot
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_pca, x='PC1', y='PC2', hue='PeakRankCategory', palette='Set2', alpha=0.7)
    plt.title('PCA of Player Stats (colored by Rank Category)')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Loadings
    loadings = pd.DataFrame(pca.components_.T, index=X.columns, columns=[f'PC{i+1}' for i in range(n_components)])

    print("\nTop contributing features to PC1:")
    print(loadings['PC1'].sort_values(ascending=False).head(10))

    # Barplot of PC1 loadings (excluding 'weighted_peakrank' and 'M')
    filtered_loadings = loadings.drop(index=[col for col in ['weighted_peakrank', 'M'] if col in loadings.index])
    sorted_pc1 = filtered_loadings['PC1'].sort_values(ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(x=sorted_pc1.values[:15], y=sorted_pc1.index[:15], palette='coolwarm')
    plt.title('Top 15 Feature Contributions to PC1 (excluding weighted_peakrank and M)')
    plt.xlabel('Loading Value')
    plt.ylabel('Feature')
    plt.tight_layout()
    plt.show()
    
def run_clustering_and_pca(df, n_clusters=4, n_components=2):
    # Selecting numeric columns for clustering and PCA
    X = df.drop(columns=['Player', 'PeakRank', 'PeakRankCategory'], errors='ignore')
    X = X.select_dtypes(include=[np.number])
    X_scaled = StandardScaler().fit_transform(X)

    # K-Means Clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)
    
    # PCA for dimensionality reduction
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    # Create a new DataFrame with PCA and cluster labels
    df_pca = pd.DataFrame(X_pca, columns=[f'PC{i+1}' for i in range(n_components)])
    df_pca['Cluster'] = clusters
    df_pca['PeakRank'] = df['PeakRank'].values
    bins = [0, 15, 40, 75, df['PeakRank'].max() + 1]
    labels = ['Top 15', 'Top 40', 'Top 75', 'Other']
    df_pca['PeakRankCategory'] = pd.cut(df['PeakRank'], bins=bins, labels=labels, right=False)

    # Plot the clusters on the PCA scatter plot
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_pca, x='PC1', y='PC2', hue='Cluster', palette='Set1', alpha=0.7, s=100)
    plt.title(f'PCA with K-Means Clustering (n_clusters={n_clusters})')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Optional: Plot the cluster centers in PCA space
    cluster_centers_pca = pca.transform(kmeans.cluster_centers_)
    plt.scatter(cluster_centers_pca[:, 0], cluster_centers_pca[:, 1], s=300, c='red', marker='X', label="Cluster Centers")
    plt.legend()
    plt.show()
    
def analyze_clusters(df, n_clusters=4):
    # Create a new column for the cluster assignments
    X = df.drop(columns=['Player', 'PeakRank', 'PeakRankCategory'], errors='ignore')
    X = X.select_dtypes(include=[np.number])  # Select only numeric columns

    # Handle missing values: You can choose to fill NaNs or drop them
    X.fillna(X.mean(), inplace=True)  # Filling NaNs with the mean of the respective column
    
    # Standardize the data
    X_scaled = StandardScaler().fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)
    
    df['Cluster'] = clusters  # Add cluster labels to the DataFrame

    # Ensure that only numeric columns are selected for calculating the means
    numeric_columns = df.select_dtypes(include=['number']).columns
    
    # Calculate and display the average stats per cluster
    cluster_means = df[numeric_columns].groupby(df['Cluster']).mean()  # Calculate mean for each cluster
    print("\n--- Average Stats per Cluster ---")
    print(cluster_means)

    # Display the most important stats for each cluster
    for i in range(n_clusters):
        print(f"\nCluster {i} Stats:")
        cluster_stats = cluster_means.iloc[i]
        top_stats = cluster_stats.sort_values(ascending=False).head(5)
        print(top_stats)

def main():
    filepath = 'aggregated_us_open_stats.csv'
    df = load_and_clean_data(filepath)

    print("\n[1] Binary Elite Classification")
    classify_elite(df)

    print("\n[2] Multiclass Rank Category Classification")
    categorize_and_classify(df)

    print("\n[3] PCA Visualization")
    run_pca(df)
    
    print("\n[4] PCA with Clustering")
    run_clustering_and_pca(df)
    
    print("\n[5] Cluster Analysis (Average Stats per Cluster)")
    analyze_clusters(df)

if __name__ == "__main__":
    main()
