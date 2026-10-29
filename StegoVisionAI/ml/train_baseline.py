"""
Research starter for a supervised image classifier.
Expected dataset layout:
dataset/
  train/clean, train/stego/
  val/clean, val/stego/
  test/clean, test/stego/

This script intentionally raises an explanatory error until PyTorch/torchvision
and a properly labeled dataset are installed. It is not a trained model.
"""
from pathlib import Path

ROOT = Path("dataset")
required = [ROOT / split / label for split in ("train", "val", "test") for label in ("clean", "stego")]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit(
        "Dataset not found. Create the documented train/val/test folders with clean and stego labels. "
        "Use licensed data and split by original source image. Missing: " + ", ".join(missing)
    )
try:
    import torch
    import torchvision
except ImportError as exc:
    raise SystemExit("Install research dependencies first: pip install torch torchvision") from exc

raise SystemExit(
    "Dataset folders found, but this starter does not claim a trained detector. "
    "Implement and document a CNN training/evaluation protocol before enabling detector predictions."
)
