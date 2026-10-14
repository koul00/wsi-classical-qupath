# wsi-classical-qupath classical WSI cancer analysis


A fully-scriptable, reproduction of the pre-deep-learning histopathology
recipe — the approach behind [**QuPath**](https://qupath.github.io) (Bankhead et al.,
*Sci. Rep.* 2017) and surveyed in Gurcan et al., *IEEE RBME* 2009. Everything runs in a
VS Code / Jupyter notebook with `openslide` + `scikit-image` + `scikit-learn`.

![classical RF map](results/classical_rf_map.png)

Run on `tumor_084` from CAMELYON16 — the same slide used for the deep dive in
[lazyslide-wsi-pipeline](https://github.com/koul00/lazyslide-wsi-pipeline#single-slide-deep-dive-tumor_084),
so the classical map above can be compared directly against that repo's
zero-shot tumour heatmap.

## The pipeline (`classical_pipeline.ipynb`)

Run top-to-bottom. Each stage is a classic building block of the era:

| Step | Method | Library |
|------|--------|---------|
| 1. Tissue detection | Otsu threshold on saturation | scikit-image |
| 2. Colour deconvolution | H&E → hematoxylin / eosin (Ruifrok & Johnston 2001) | `skimage.color.rgb2hed` |
| 3. Nuclei segmentation | distance-transform **watershed** | scikit-image |
| 4. Hand-crafted features | **Haralick / GLCM** texture + nuclei density + colour | `graycomatrix` |
| 5. Classification | **Random Forest** → whole-slide tumour-cellularity map | scikit-learn |

## Quick start

```bash
pip install -r requirements.txt
# download tumor_084 via lazyslide-wsi-pipeline's scripts/download_data.sh
# (or any CAMELYON16/own slide — just point `SLIDE` at it), then:
jupyter notebook classical_pipeline.ipynb     # or open it in VS Code and Run All
```

## Results (`tumor_084`, CAMELYON16)

- 1103 tissue tiles (256px grid on a 16× downsampled thumbnail) → 9 hand-crafted
  features each → weak-labeled Random Forest (728 training tiles, cellularity terciles).
- Top features by importance: `mean_R` (0.35), `nuclei_density` (0.27), `ASM` (0.16) —
  colour and nuclear density dominate over the texture descriptors.
- The resulting cellularity map **qualitatively agrees** with
  [lazyslide-wsi-pipeline](https://github.com/koul00/lazyslide-wsi-pipeline)'s
  zero-shot PLIP heatmap on the same slide — both flag the same dense region in
  the lower-left lobe as tumour-like — though the classical map is coarser (grid
  cells vs per-tile) and the agreement is visual, not pixel-registered.

- **Every feature is hand-engineered** — no learned representations. This is the ceiling
  of classical digital pathology: stain unmixing, morphometry, and texture descriptors.
- **The classifier is a Random Forest** — the workhorse of the era.
- The output map is the hand-crafted-feature analogue of a deep attention map, which is
  exactly what Stages 2 (SAMPLER) and 3 (LazySlide) replace with learned features.

## A note on QuPath
QuPath is a Java desktop application, not a Python library. Rather than script its GUI,
this repo reimplements the *same classical techniques* QuPath uses internally
(watershed nuclei, Haralick texture, Random Forest object classification) as transparent,
reproducible Python — so the whole stage runs in VS Code. QuPath remains the canonical
reference tool for this era.

## Limitations (honest)
- Labels are **weak** (cellularity terciles), not expert annotations — this demonstrates
  the *method*, not clinical-grade tumour detection.
- Works at a downsampled level for the whole-slide map; nuclei segmentation is shown at 40x
  on one high-cellularity tile.

## References
- Bankhead et al. **QuPath: Open source software for digital pathology image analysis.** *Sci. Rep.* 2017.
- Gurcan et al. **Histopathological Image Analysis: A Review.** *IEEE RBME* 2009.
- Ruifrok & Johnston. **Quantification of histochemical staining by colour deconvolution.** 2001.
- Haralick et al. **Textural Features for Image Classification.** *IEEE SMC* 1973.
