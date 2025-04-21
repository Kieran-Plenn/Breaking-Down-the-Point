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
    # Load the CSV file
    df = pd.read_csv(filepath)
    
    # Print initial shape to check columns and rows
    print(f"Initial data shape: {df.shape}")
    
    # Remove columns with 'Unnamed' in their name (these are likely irrelevant)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Drop rows where 'PeakRank' is missing (ignores other columns)
    df = df.dropna(subset=['PeakRank'])
    
    # Remove completely empty rows (if any remain after cleaning)
    df = df.dropna(how='all')
    
    # Check for missing values and print the cleaned shape
    missing_values_after = df.isnull().sum()
    print(f"Missing values after cleaning:\n{missing_values_after}")
    print(f"Data shape after dropping rows with missing PeakRank and empty rows: {df.shape}")
    
    # Optional: Recalculate any features or cleanup here
    df['weighted_peakrank'] = df['PeakRank'] / df['M']
    
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
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Linear Regression MSE: {mse:.4f}")

def classify_elite(df, elite_cutoff=10):
    scaler = StandardScaler()
    X = scaler.fit_transform(df.drop(columns=['Player', 'PeakRank']))
    y = (df['PeakRank'] <= elite_cutoff).astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"Random Forest Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall: {recall_score(y_test, y_pred):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred):.4f}")

    importance = model.feature_importances_
    features = df.drop(columns=['Player', 'PeakRank']).columns
    imp_df = pd.DataFrame({'Feature': features, 'Importance': importance}).sort_values(by='Importance', ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=imp_df)
    plt.title("Feature Importance from Random Forest")
    plt.show()

def categorize_and_classify(df):
    # Custom bins as per your request
    bins = [0, 3, 20, 50, df['PeakRank'].max() + 1]
    labels = ['1-3', '4-20', '21-50', '51+']
    df['PeakRankCategory'] = pd.cut(df['PeakRank'], bins=bins, labels=labels, right=False)
    df = df.dropna(subset=['PeakRankCategory', 'M'])  # Drop rows with missing categories or M value

    X = pd.get_dummies(df.drop(columns=['Player', 'PeakRank', 'PeakRankCategory']))
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
    print(df.shape)

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
