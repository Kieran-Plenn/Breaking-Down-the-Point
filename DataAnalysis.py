import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score

# Load data
df = pd.read_csv('aggregated_us_open_stats.csv')

# Preprocessing
# Drop rows with missing values
df_cleaned = df.dropna()

# Handle weighted stats (weights could be based on total matches, M)
df_cleaned.loc[:, 'weighted_peakrank'] = df_cleaned['PeakRank'] / df_cleaned['M']

# Selecting only numeric columns for correlation
df_numeric = df_cleaned.select_dtypes(include=['number'])

# Now calculate the correlation matrix for the numeric columns
correlation_matrix = df_numeric.corr()

# Display correlation heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
plt.title("Correlation Heatmap")
plt.show()

# Check the top features correlated with PeakRank
top_correlated_features = correlation_matrix['PeakRank'].sort_values(ascending=False).head(10)
print("Top Correlated Features with PeakRank:")
print(top_correlated_features)

# Exploratory data analysis (visualizations)
# Scatter plot for 'Hld%' vs 'PeakRank' (example)
plt.scatter(df_cleaned['Hld%'], df_cleaned['PeakRank'])
plt.title('Hld% vs PeakRank')
plt.xlabel('Hld%')
plt.ylabel('PeakRank')
plt.show()

# Scatter plot for 'Brk%' vs 'PeakRank'
plt.scatter(df_cleaned['Brk%'], df_cleaned['PeakRank'])
plt.title('Brk% vs PeakRank')
plt.xlabel('Brk%')
plt.ylabel('PeakRank')
plt.show()

# Feature Scaling (necessary for some models like Linear Regression)
scaler = StandardScaler()
scaled_features = scaler.fit_transform(df_cleaned.drop(columns=['Player', 'PeakRank']))

# Target (PeakRank) and feature set
X = scaled_features
y = df_cleaned['PeakRank']

# Split the data into training and testing sets (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 1. Linear Regression Model (for regression)
lin_reg = LinearRegression()
lin_reg.fit(X_train, y_train)

# Predict and evaluate Linear Regression model
y_pred_reg = lin_reg.predict(X_test)
mse_reg = mean_squared_error(y_test, y_pred_reg)
print(f"Linear Regression MSE: {mse_reg}")

# 2. Random Forest Classifier Model (for classification)
# Let's first classify players as "Elite" (PeakRank <= 10) or "Non-Elite" (PeakRank > 10)
y_class = (y <= 10).astype(int)  # Convert PeakRank into a binary classification (elite or not)

# Split data again for classification
X_train_class, X_test_class, y_train_class, y_test_class = train_test_split(X, y_class, test_size=0.2, random_state=42)

rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
rf_classifier.fit(X_train_class, y_train_class)

# Predict and evaluate Random Forest Classifier model
y_pred_class = rf_classifier.predict(X_test_class)
accuracy_class = accuracy_score(y_test_class, y_pred_class)
print(f"Random Forest Classifier Accuracy: {accuracy_class}")

# Calculate precision, recall, and F1-score
precision = precision_score(y_test_class, y_pred_class)
recall = recall_score(y_test_class, y_pred_class)
f1 = f1_score(y_test_class, y_pred_class)

print(f"Precision: {precision}")
print(f"Recall: {recall}")
print(f"F1-Score: {f1}")

# Feature Importance from Random Forest (for further analysis)
feature_importances = rf_classifier.feature_importances_
feature_names = df_cleaned.drop(columns=['Player', 'PeakRank']).columns
importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': feature_importances})
importance_df = importance_df.sort_values(by='Importance', ascending=False)

# Plot Feature Importance
plt.figure(figsize=(10, 6))
sns.barplot(x='Importance', y='Feature', data=importance_df)
plt.title("Feature Importance from Random Forest")
plt.show()

# ---================================---- 

# Quantile-based categorization into 5 roughly equal groups
q = 10  # or any number of quantiles you want
labels = [f'Tier {i+1}' for i in range(q)]

df_cleaned['PeakRankCategory'], bins = pd.qcut(
    df_cleaned['weighted_peakrank'],
    q=q,
    labels=labels,
    retbins=True,
    duplicates='drop'
)

# Step 2: Handle missing values (if any) and keep only the necessary columns
df_cleaned = df_cleaned.dropna(subset=['PeakRankCategory', 'M'])

# Optional: Visualize the distribution of categories
df_cleaned['PeakRankCategory'].value_counts().plot(kind='bar', title='Distribution of PeakRank Categories')

# Step 3: Split the data for classification
X = df_cleaned.drop(columns=['PeakRank', 'PeakRankCategory'])
y = df_cleaned['PeakRankCategory']

# One-hot encode categorical features (if any)
X = pd.get_dummies(X)

# Step 4: Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 5: Train a Random Forest Classifier
rf_classifier = RandomForestClassifier(random_state=42)
rf_classifier.fit(X_train, y_train)

# Step 6: Evaluate the model
accuracy = rf_classifier.score(X_test, y_test)
print(f"Random Forest Classifier Accuracy: {accuracy:.4f}")

# Print additional classification report (precision, recall, F1-score)
y_pred = rf_classifier.predict(X_test)
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# Optional: Feature importance (to see which stats matter most)
importances = rf_classifier.feature_importances_
feature_importance = pd.DataFrame({'Feature': X.columns, 'Importance': importances})
feature_importance = feature_importance.sort_values(by='Importance', ascending=False)

print("Feature Importances:\n", feature_importance)

# Show the bins that were used to create the categories
print("Quantile bins (PeakRank cutoffs):", bins)

# Show how many players are in each class
print("\nPlayer count per category:")
print(df_cleaned['PeakRankCategory'].value_counts().sort_index())
