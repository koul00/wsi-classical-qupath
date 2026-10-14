"""
evaluate_vs_xml.py

Quantitative check of the classical pipeline (classical_pipeline.ipynb) against the
CAMELYON16 expert annotation of the same slide (tumor_084.xml).

The notebook's Random Forest is trained on WEAK labels (cellularity terciles), never on
the XML, so the XML is an independent ground truth here — no leakage.

Same steps and parameters as the notebook (Otsu on saturation -> H&E deconvolution ->
9 hand-crafted features per 256-px tile at pyramid level 2 -> Random Forest), computed in
row chunks to keep RAM low (the level-2 image is 16384 x 21504 px).

Ground truth per tile: the tile's centroid lies inside a 'Tumor' polygon of the XML (the
same rule as lazyslide-wsi-pipeline's validate()). Two looser definitions are also
reported (tile overlaps the tumor by >=5% / >=25% of its area).

Usage:  python evaluate_vs_xml.py [path/to/tumor_084.tif]
Output: prints the report and writes results/evaluation_vs_xml.txt
"""
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import openslide
from scipy import ndimage as ndi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep
from skimage.color import rgb2hed, rgb2hsv
from skimage.feature import graycomatrix, graycoprops
from skimage.filters import threshold_otsu
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

SLIDE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/github-projects/lazyslide/slides/tumor_084.tif")
XML = os.path.splitext(SLIDE)[0] + ".xml"
LV, TILE, CHUNK = 2, 256, 1024
FEAT_NAMES = ["contrast", "homogeneity", "energy", "correlation", "ASM",
              "nuclei_density", "mean_R", "mean_G", "mean_B"]

lines = []


def say(msg=""):
    print(msg, flush=True)
    lines.append(msg)


# ---------------------------------------------------------------- notebook steps
s = openslide.OpenSlide(SLIDE)
W, H = s.level_dimensions[LV]
DS = s.level_downsamples[LV]
thumb = np.array(s.read_region((0, 0), LV, (W, H)).convert("RGB"))

# saturation, HSV value ("gray") and hematoxylin, computed chunk by chunk
sat = np.empty((H, W), np.float32)
val = np.empty((H, W), np.uint8)
hema = np.empty((H, W), np.float32)
for y in range(0, H, CHUNK):
    blk = thumb[y:y + CHUNK]
    hsv = rgb2hsv(blk)
    sat[y:y + CHUNK] = hsv[..., 1]
    val[y:y + CHUNK] = (hsv[..., 2] * 255).astype(np.uint8)
    hema[y:y + CHUNK] = rgb2hed(blk)[..., 0]

tissue = sat > threshold_otsu(sat)
tissue = ndi.binary_fill_holes(ndi.binary_opening(tissue, iterations=2))
hema_thr = threshold_otsu(hema[tissue])


def tile_features(y, x):
    g = val[y:y + TILE, x:x + TILE] // 32
    glcm = graycomatrix(g, [1], [0], levels=8, symmetric=True, normed=True)
    texture = [graycoprops(glcm, p)[0, 0]
               for p in ("contrast", "homogeneity", "energy", "correlation", "ASM")]
    density = (hema[y:y + TILE, x:x + TILE] > hema_thr).mean()
    colour = [thumb[y:y + TILE, x:x + TILE, c].mean() for c in range(3)]
    return texture + [density] + colour


feats, coords = [], []
for y in range(0, H - TILE, TILE):
    for x in range(0, W - TILE, TILE):
        if tissue[y:y + TILE, x:x + TILE].mean() < 0.5:
            continue
        feats.append(tile_features(y, x))
        coords.append((y, x))
feats, coords = np.array(feats), np.array(coords)
dens = feats[:, FEAT_NAMES.index("nuclei_density")]

lo, hi = np.quantile(dens, [0.33, 0.67])
y_weak = np.full(len(dens), -1)
y_weak[dens <= lo] = 0
y_weak[dens >= hi] = 1
train = y_weak >= 0
rf = RandomForestClassifier(n_estimators=300, random_state=0).fit(feats[train], y_weak[train])
prob = rf.predict_proba(feats)[:, 1]

# ---------------------------------------------------------------- ground truth (XML)
polys = []
for a in ET.parse(XML).iter("Annotation"):
    if (a.get("PartOfGroup") or "").lower().startswith(("tumor", "metastas")):
        pts = [(float(c.get("X")), float(c.get("Y"))) for c in a.iter("Coordinate")]
        if len(pts) >= 3:
            polys.append(Polygon(pts).buffer(0))
tumor = unary_union(polys)
tumor_p = prep(tumor)

from shapely.geometry import Point  # noqa: E402
centroid_label = np.array([tumor_p.contains(Point((x + TILE / 2) * DS, (y + TILE / 2) * DS))
                           for y, x in coords]).astype(int)
overlap = np.array([tumor.intersection(box(x * DS, y * DS, (x + TILE) * DS, (y + TILE) * DS)).area
                    / (TILE * DS) ** 2 for y, x in coords])

rng = np.random.default_rng(0)


def auc_ci(y, score, n=2000):
    vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            vals.append(roc_auc_score(y[i], score[i]))
    return np.percentile(vals, [2.5, 97.5])


# ---------------------------------------------------------------- report
say(f"slide: {os.path.basename(SLIDE)}   level {LV} (downsample {DS:.0f}), tile {TILE}px "
    f"= {TILE * DS * float(s.properties['openslide.mpp-x']):.0f} um")
say(f"tissue tiles: {len(feats)}   (RF trained on {train.sum()} weak-labelled tiles)")
say()
say("ROC-AUC of the RF probability vs the expert XML, tile level:")
for name, yt in [("centroid inside tumor", centroid_label),
                 ("overlap >= 25%", (overlap >= 0.25).astype(int)),
                 ("overlap >=  5%", (overlap >= 0.05).astype(int))]:
    lo_ci, hi_ci = auc_ci(yt, prob)
    say(f"  {name:22s} tumor tiles {yt.sum():3d}/{len(yt)}   AUC {roc_auc_score(yt, prob):.3f}"
        f"  95% CI [{lo_ci:.3f}, {hi_ci:.3f}]   (nuclei_density alone: "
        f"{roc_auc_score(yt, dens):.3f})")
say()
say("Single features vs centroid-rule labels (AUC<0.5 means LOWER value = tumor):")
for i, n in enumerate(FEAT_NAMES):
    say(f"  {n:15s} {roc_auc_score(centroid_label, feats[:, i]):.3f}")
top = np.argsort(-prob)[:int(0.1 * len(prob))]
say()
say(f"Tumor tiles among the RF top-10% ({len(top)} tiles): {centroid_label[top].sum()} "
    f"of {centroid_label.sum()}")
say("Reference: zero-shot PLIP on the same slide, AUC 0.946 "
    "(lazyslide-wsi-pipeline).")
say("Caveat: ONE slide, few tumor tiles -> exploratory; single-feature AUCs are not "
    "corrected for multiple comparisons.")

os.makedirs("results", exist_ok=True)
with open("results/evaluation_vs_xml.txt", "w") as f:
    f.write("\n".join(lines) + "\n")
