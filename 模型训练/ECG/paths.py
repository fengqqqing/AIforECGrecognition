from pathlib import Path


TRAINING_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TRAINING_DIR.parents[1]

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "training" / "ecg"
RAW_DATA_DIR = ARTIFACTS_DIR / "raw_data"
PROCESSED_DATA_DIR = ARTIFACTS_DIR / "processed_data"
MODEL_ARTIFACTS_DIR = ARTIFACTS_DIR / "models"
FIGURES_DIR = ARTIFACTS_DIR / "figures"
