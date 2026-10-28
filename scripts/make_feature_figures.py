"""Histograms/heatmap/spatial map for the QuPath classical-feature table.

Usage: python -I make_feature_figures.py <cell_features.tsv> <out_dir>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

tsv, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(tsv, sep="\t", low_memory=False)
slide = df["Image"].iloc[0]
n = len(df)

H05 = "Nucleus: 0.50 µm per pixel: Hematoxylin: "
H025 = "Nucleus: 0.25 µm per pixel: Hematoxylin: "
AREA = "Nucleus: Area µm^2"


def hist(ax, col, title, xlabel=None, logy=False, clip=(1, 99), bins=60):
    x = df[col].dropna().to_numpy()
    lo, hi = np.percentile(x, clip)
    ax.hist(np.clip(x, lo, hi), bins=bins, color="#4C72B0", edgecolor="white", linewidth=0.3)
    med = np.median(x)
    ax.axvline(med, color="#C44E52", lw=1.2)
    ax.set_title(f"{title}\nmedian {med:.3g}, IQR {np.percentile(x, 25):.3g}–{np.percentile(x, 75):.3g}", fontsize=9)
    ax.set_xlabel(xlabel or col, fontsize=8)
    ax.tick_params(labelsize=7)
    if logy:
        ax.set_yscale("log")


def grid(panels, fname, suptitle, ncols=3):
    nrows = int(np.ceil(len(panels) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 3.4 * nrows))
    axes = np.atleast_1d(axes).ravel()
    for ax, p in zip(axes, panels):
        hist(ax, **p)
    for ax in axes[len(panels):]:
        ax.axis("off")
    fig.suptitle(f"{suptitle} — {slide}, n = {n:,} cells (clipped to 1st–99th percentile)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / fname, dpi=150)
    plt.close(fig)


# A. Quality checks
grid([
    dict(col=AREA, title="Nuclear area", xlabel="µm²", logy=True, clip=(0, 99.9)),
    dict(col="Cell: Area µm^2", title="Cell area (5 µm expansion artefact)", xlabel="µm²", logy=True, clip=(0, 99.9)),
    dict(col="Nucleus/Cell area ratio", title="Nucleus / cell area ratio", clip=(0, 100)),
    dict(col="Nucleus: Circularity", title="Nuclear circularity", clip=(0, 100)),
    dict(col="Nucleus: Solidity", title="Nuclear solidity", clip=(0, 100)),
    dict(col=H05 + "Mean", title="Nuclear hematoxylin OD, mean (0.5 µm/px)", xlabel="OD", clip=(0, 100)),
], "A_quality_checks.png", "A. Quality checks")

# B. Clinically readable morphology
grid([
    dict(col=AREA, title="Nuclear size", xlabel="µm²"),
    dict(col="Nucleus: Min diameter µm", title="Nuclear minimum diameter", xlabel="µm"),
    dict(col="Nucleus: Max diameter µm", title="Nuclear maximum diameter", xlabel="µm"),
    dict(col="Nucleus: Eccentricity", title="Nuclear eccentricity"),
    dict(col=H05 + "Std.dev.", title="Chromatin heterogeneity: H std.dev. (0.5 µm/px)", xlabel="OD"),
    dict(col=H025 + "Std.dev.", title="Chromatin heterogeneity: H std.dev. (0.25 µm/px)", xlabel="OD"),
    dict(col=H05 + "Haralick Contrast (F1)", title="Chromatin texture: Haralick contrast (0.5 µm/px)"),
    dict(col=H05 + "Haralick Entropy (F8)", title="Chromatin texture: Haralick entropy (0.5 µm/px)"),
    dict(col="ROI: 0.50 µm per pixel: Eosin: Mean", title="Whole-cell eosin, mean (0.5 µm/px)", xlabel="OD"),
    dict(col="Cytoplasm: Eosin OD mean", title="Cytoplasmic eosin OD, mean", xlabel="OD"),
], "B_morphology.png", "B. Clinically readable morphology")

# C. Context: smoothed features
grid([
    dict(col="Smoothed: 50 µm: " + AREA, title="Local mean nuclear area (50 µm)", xlabel="µm²"),
    dict(col="Smoothed: 50 µm: " + H05 + "Mean", title="Local mean nuclear H OD (50 µm)", xlabel="OD"),
    dict(col="Smoothed: 50 µm: Nearby detection counts", title="Local crowding: nearby detections (50 µm)", xlabel="count"),
], "C_context_smoothed.png", "C. Local context")

# Correlation heatmap
feats = [AREA, "Nucleus: Min diameter µm", "Nucleus: Max diameter µm", "Nucleus: Circularity", "Nucleus: Solidity",
         "Nucleus: Eccentricity", H05 + "Mean", H05 + "Std.dev.", H025 + "Mean", H025 + "Std.dev.",
         H05 + "Haralick Contrast (F1)", H05 + "Haralick Entropy (F8)", H05 + "Haralick Angular second moment (F0)",
         H025 + "Haralick Contrast (F1)", H025 + "Haralick Entropy (F8)",
         "ROI: 0.50 µm per pixel: Eosin: Mean", "Cytoplasm: Eosin OD mean", "Nucleus/Cell area ratio"]
short = [f.replace("Nucleus: ", "N ").replace(" per pixel", "").replace("Hematoxylin: ", "H ").replace("Haralick ", "Har ")
         for f in feats]
corr = df[feats].corr(method="spearman")
fig, ax = plt.subplots(figsize=(9.5, 8))
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(feats)), short, rotation=90, fontsize=7)
ax.set_yticks(range(len(feats)), short, fontsize=7)
fig.colorbar(im, ax=ax, label="Spearman ρ", shrink=0.8)
ax.set_title(f"Feature correlation — {slide}, n = {n:,}", fontsize=10)
fig.tight_layout()
fig.savefig(out / "D_correlation_heatmap.png", dpi=150)
plt.close(fig)
corr.to_csv(out / "D_correlation_matrix.csv")

# Spatial maps
fig, axes = plt.subplots(1, 3, figsize=(16, 5.4))
for ax, (col, label) in zip(axes, [(AREA, "Nuclear area (µm²)"), (H05 + "Mean", "H OD mean (0.5 µm/px)"),
                                   ("Nucleus: Circularity", "Circularity")]):
    v = df[col]
    sc = ax.scatter(df["Centroid X µm"], df["Centroid Y µm"], c=v, s=1.2, cmap="viridis",
                    vmin=np.percentile(v, 1), vmax=np.percentile(v, 99), rasterized=True)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_title(label, fontsize=10)
    ax.set_xlabel("x (µm)", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.colorbar(sc, ax=ax, shrink=0.8)
fig.suptitle(f"Spatial maps — {slide}", fontsize=11)
fig.tight_layout()
fig.savefig(out / "E_spatial_maps.png", dpi=150)
plt.close(fig)

print("Wrote:", sorted(p.name for p in out.glob("*")))
