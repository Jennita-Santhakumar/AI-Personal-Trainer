"""
ml/training/train_injury_risk.py
Train the injury risk RandomForest on collected session data.

Usage
-----
python ml/training/train_injury_risk.py --data_path data/sessions_export.json
"""
import argparse
import json
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
from ml.models.injury_risk import InjuryRiskModel


def build_dataset(sessions: list):
    """
    Build (X, y) dataset from session history.
    Each sample is a 14-session window; label is the injury flag on session 15.
    """
    model = InjuryRiskModel()
    X, y = [], []
    for i in range(14, len(sessions)):
        window = sessions[i-14:i]
        label  = sessions[i].get("injury_occurred", 0)
        features = model.build_features(window)
        X.append(features[0])
        y.append(label)
    return np.array(X), np.array(y)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", required=True)
    parser.add_argument("--n_estimators", type=int, default=100)
    parser.add_argument("--max_depth", type=int, default=8)
    args = parser.parse_args()

    with open(args.data_path) as f:
        sessions = json.load(f)

    print(f"Loaded {len(sessions)} sessions")
    X, y = build_dataset(sessions)
    print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Class balance: {dict(zip(*np.unique(y, return_counts=True)))}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    clf = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    cv_scores = cross_val_score(clf, X_train, y_train, cv=5, scoring="f1_macro")
    print(f"\nCV F1 macro: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    y_pred = clf.predict(X_test)
    print("\nTest set report:")
    print(classification_report(y_test, y_pred, target_names=["low", "moderate", "high"]))

    risk_model = InjuryRiskModel()
    risk_model.save(clf)
    print("Training complete.")


if __name__ == "__main__":
    main()
