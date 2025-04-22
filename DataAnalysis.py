import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_squared_error, accuracy_score, classification_report,
    precision_score, recall_score, f1_score
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA

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
    cols_to_normalize = percent_cols + numeric_cols
    cols_to_normalize = [col for col in cols_to_normalize if col in df.columns]

    scaler = StandardScaler()
    df[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])
    
    return df

def plot_correlation_heatmap(df):
    df_numeric = df.select_dtypes(include=['number'])
    correlation_matrix = df_numeric.corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title("Correlation Heatmap")
    plt.show()
    top_corr = correlation_matrix['PeakRank'].sort_values(ascending=False).head(10)
    print("Top Correlated Features with PeakRank:")
    print(top_corr)

def exploratory_plots(df):
    plt.scatter(df['Hld%'], df['PeakRank'])
    plt.title('Hld% vs PeakRank')
    plt.xlabel('Hld%')
    plt.ylabel('PeakRank')
    plt.show()

    plt.scatter(df['Brk%'], df['PeakRank'])
    plt.title('Brk% vs PeakRank')
    plt.xlabel('Brk%')
    plt.ylabel('PeakRank')
    plt.show()

def run_regression(df):
    scaler = StandardScaler()
    X = scaler.fit_transform(df.drop(columns=['Player', 'PeakRank']))
    y = df['PeakRank']
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    mse_scores = []
    
    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mse_scores.append(mse)

    print(f"Linear Regression MSE (5-fold CV): {np.mean(mse_scores):.4f}")

def classify_elite(df, elite_cutoff=10):
    scaler = StandardScaler()
    X = scaler.fit_transform(df.drop(columns=['Player', 'PeakRank']))
    y = (df['PeakRank'] <= elite_cutoff).astype(int)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    accuracy_scores = []
    precision_scores = []
    recall_scores = []
    f1_scores_list = []

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

        # Check class distribution in each fold
        print(f"Training set class distribution:\n{y_train.value_counts()}")
        print(f"Test set class distribution:\n{y_test.value_counts()}")

    print(f"Random Forest Accuracy (5-fold CV): {np.mean(accuracy_scores):.4f}")
    print(f"Precision: {np.mean(precision_scores):.4f}")
    print(f"Recall: {np.mean(recall_scores):.4f}")
    print(f"F1 Score: {np.mean(f1_scores_list):.4f}")

    importance = model.feature_importances_
    features = df.drop(columns=['Player', 'PeakRank']).columns
    imp_df = pd.DataFrame({'Feature': features, 'Importance': importance}).sort_values(by='Importance', ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=imp_df)
    plt.title("Feature Importance from Random Forest")
    plt.show()

def categorize_and_classify(df):
    # Define custom bins for PeakRank categories
    # These bins are more strict and should be more meaningful for your analysis
    bins = [0, 10, 30, 50, 75, df['PeakRank'].max() + 1]
    labels = ['Elite', 'Semi-Elite', 'Top 50', 'Top 75', 'Other']
    
    # Categorize PeakRank into new bins
    df['PeakRankCategory'] = pd.cut(df['PeakRank'], bins=bins, labels=labels, right=False)

    # Drop rows with missing PeakRankCategory or M (match count) values
    df = df.dropna(subset=['PeakRankCategory', 'M'])

    # Prepare features (X) and target (y)
    X = pd.get_dummies(df.drop(columns=['Player', 'PeakRank', 'PeakRankCategory']))
    y = df['PeakRankCategory']

    # Cross-validation setup
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    accuracy_scores = []

    # Perform cross-validation
    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        # Train Random Forest model
        model = RandomForestClassifier(random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        accuracy_scores.append(accuracy_score(y_test, y_pred))

        # Check class distribution in each fold
        print(f"Training set class distribution:\n{y_train.value_counts()}")
        print(f"Test set class distribution:\n{y_test.value_counts()}")

    print(f"Multiclass Accuracy (5-fold CV): {np.mean(accuracy_scores):.4f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # Feature importance plot
    importances = model.feature_importances_
    imp_df = pd.DataFrame({'Feature': X.columns, 'Importance': importances}).sort_values(by='Importance', ascending=False)
    print("Feature Importances:\n", imp_df)
    print("Player count per category:\n", df['PeakRankCategory'].value_counts().sort_index())

def run_pca(df, n_components=2):
    X = df.drop(columns=['Player', 'PeakRank', 'PeakRankCategoryQuantile'], errors='ignore')
    X = X.select_dtypes(include=[np.number])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    print(f"Explained variance by component: {pca.explained_variance_ratio_}")
    print(f"Cumulative explained variance: {np.cumsum(pca.explained_variance_ratio_)}")

    df_pca = pd.DataFrame(X_pca, columns=[f'PC{i+1}' for i in range(n_components)])
    df_pca['PeakRank'] = df['PeakRank'].values
    df_pca['PeakRankCategory'] = pd.cut(df['PeakRank'], bins=[0, 3, 20, 50, df['PeakRank'].max()+1],
                                        labels=['1-3', '4-20', '21-50', '51+'], right=False)

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_pca, x='PC1', y='PC2', hue='PeakRankCategory', palette='Set2', alpha=0.7)
    plt.title('PCA of Player Stats (colored by Rank Category)')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    loadings = pd.DataFrame(pca.components_.T, index=X.columns, columns=[f'PC{i+1}' for i in range(n_components)])
    return loadings

def main():
    filepath = 'aggregated_us_open_stats.csv'
    df = load_and_clean_data(filepath)

    plot_correlation_heatmap(df)
    exploratory_plots(df)

    print("\n--- Linear Regression ---")
    run_regression(df)

    print("\n--- Binary Classification: Elite vs Non-Elite ---")
    classify_elite(df)

    print("\n--- Multiclass Classification (Quantile Categories) ---")
    categorize_and_classify(df)

    print("\n--- PCA Analysis ---")
    pca_loadings = run_pca(df)
    print("\nTop contributing features to PC1:")
    print(pca_loadings['PC1'].sort_values(ascending=False).head(10))

if __name__ == "__main__":
    main()
