# Deep-learning detector extension (research phase)

The included app is a functional steganography and basic forensics platform, but **it does not ship with a trained deep-learning detector**. A credible detector requires a documented dataset, a reproducible train/validation/test split, and a model evaluation.

Suggested research workflow:
1. Collect licensed clean images and matching stego images generated with documented embedding algorithms and payload rates.
2. Split by source image before augmentation to avoid leakage.
3. Train a CNN baseline (e.g., ResNet-style or a steganalysis-oriented residual network).
4. Evaluate precision, recall, F1, ROC-AUC, false-positive rate, and robustness across image formats and payload rates.
5. Export a versioned model and expose inference through a separate API module.
6. Report dataset limitations and avoid presenting model confidence as certainty.

Do not train/test on near-duplicate images across splits. Do not label images as clean solely because this app did not find indicators.
