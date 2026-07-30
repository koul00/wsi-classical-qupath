# wsi-classical-qupath classical WSI cancer analysis


A fully-scriptable, reproduction of the pre-deep-learning histopathology
recipe — the approach behind [**QuPath**](https://qupath.github.io) (Bankhead et al.,
*Sci. Rep.* 2017) and surveyed in Gurcan et al., *IEEE RBME* 2009. Everything runs in a
VS Code / Jupyter notebook with `openslide` + `scikit-image` + `scikit-learn`.

![classical RF map](results/classical_rf_map.png)

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
# put the slide in ~/wsi-shared-slides/ (see data/download_slides.md), then:
jupyter notebook classical_pipeline.ipynb     # or open it in VS Code and Run All
```

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
