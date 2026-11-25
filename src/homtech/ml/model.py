"""Classical SVM pipelines and versioned local model files."""

from pathlib import Path

import joblib
import numpy as np
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC, SVC

from homtech.ml.features import FEATURE_CONFIG, HOG_PRESETS, make_descriptor
from homtech.ml.rafdb import CLASSES, SIX_CLASSES


LINEAR_SCHEMA_VERSION = 2
RBF_SCHEMA_VERSION = 3
LINEAR_ALGORITHM = "hog_linear_svm"
RBF_ALGORITHM = "hog_pca_rbf_svm"
RBF_FEATURE_CONFIG = HOG_PRESETS["orient12"]


def build_model(*, c: float = 0.1, seed: int = 42, max_iter: int = 10000) -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("svm", LinearSVC(C=c, class_weight="balanced", dual="auto",
                          random_state=seed, max_iter=max_iter)),
    ])


def build_estimator(model: str, c: float, pca_components: int, seed: int, max_iter: int) -> Pipeline:
    if model == "linear":
        return build_model(c=c, seed=seed, max_iter=max_iter)
    return Pipeline([
        ("scaler", StandardScaler()),
        ("pca", PCA(n_components=pca_components, svd_solver="randomized", random_state=seed)),
        ("svm", SVC(C=c, kernel="rbf", gamma="scale", class_weight="balanced", cache_size=1000)),
    ])


def save_model(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(".joblib.tmp")
    joblib.dump(payload, temporary)
    temporary.replace(path)


def predict_with_margin(estimator: Pipeline, features):
    scores = estimator.decision_function(features)
    predictions = estimator.predict(features)
    rows = np.arange(len(predictions))
    columns = np.searchsorted(estimator.classes_, predictions)
    chosen_scores = scores[rows, columns].copy()
    scores[rows, columns] = -np.inf
    return predictions, chosen_scores - scores.max(axis=1)


def load_model(path: Path) -> dict:
    # joblib/pickle files must only be loaded from a trusted, locally created run.
    payload = joblib.load(path)
    if not isinstance(payload, dict):
        raise ValueError("Model biçimi uyumsuz.")
    if payload.get("algorithm") == RBF_ALGORITHM:
        classes = CLASSES if payload.get("classes") == list(CLASSES) else SIX_CLASSES
        schema_version, feature_config = RBF_SCHEMA_VERSION, RBF_FEATURE_CONFIG
        step_types = (("scaler", StandardScaler), ("pca", PCA), ("svm", SVC))
    else:
        schema_version, classes, feature_config = LINEAR_SCHEMA_VERSION, CLASSES, FEATURE_CONFIG
        step_types = (("scaler", StandardScaler), ("svm", LinearSVC))
    if (payload.get("algorithm") not in (LINEAR_ALGORITHM, RBF_ALGORITHM)
            or payload.get("schema_version") != schema_version
            or payload.get("classes") != list(classes)
            or payload.get("feature_config") != feature_config):
        raise ValueError("Model sürümü, algoritması, sınıfları veya HOG ayarları uyumsuz.")
    estimator = payload.get("estimator")
    if (not isinstance(estimator, Pipeline)
            or tuple(estimator.named_steps) != tuple(name for name, _ in step_types)
            or any(not isinstance(estimator[name], kind) for name, kind in step_types)
            or (isinstance(estimator["svm"], SVC) and estimator["svm"].kernel != "rbf")
            or getattr(estimator, "n_features_in_", None) != make_descriptor(feature_config).getDescriptorSize()
            or list(getattr(estimator, "classes_", ())) != [CLASSES.index(label) for label in classes]):
        raise ValueError("Model eğitim sözleşmesi uyumsuz.")
    return payload
