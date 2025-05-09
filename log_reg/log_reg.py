import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

# Load the data
df = pd.read_csv("structured_embeddings.csv")

# Features and labels
X = df.drop(columns=["label", "label_name", "logical_structure"])
y = df["label"]

# Split data
X_train, _, y_train, _ = train_test_split(
    X, y, stratify=y, test_size=0.2, random_state=42
)

# Train logistic regression model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Save to file
joblib.dump(model, "logreg_model.joblib")
