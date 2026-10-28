# wsi-classical-qupath — classical cell features computed with QuPath

Handcrafted, pathologist-readable cell features for whole-slide H&E images, computed with
**QuPath's own commands** (cell detection, intensity/Haralick texture, shape, neighbourhood
features) through its scripting engine. Nothing is reimplemented: the Groovy script tells
QuPath what to run, and QuPath produces the numbers.

Requires [QuPath](https://qupath.github.io) **0.7.0** (Bankhead et al., *Sci. Rep.* 2017).
QuPath's source is not included here; see <https://github.com/qupath/qupath> and its licence.

A separate Python reimplementation of the same kind of pipeline (scikit-image) is in
[wsi-classical-python](https://github.com/koul00/wsi-classical-python). Its results are
not QuPath's results.

## What the script does (`scripts/classical_features.groovy`)

| Step | QuPath command | Notes |
|------|----------------|-------|
| Stain vectors | `setColorDeconvolutionStains` | QuPath default H&E |
| Cell detection | `WatershedCellDetection` | Hematoxylin OD, 0.5 µm/px, area 10–400 µm², threshold 0.1, 5 µm cell expansion |
| Intensity + texture | `IntensityFeaturesPlugin` | Nuclear hematoxylin at 0.25 and 0.5 µm/px; whole-cell eosin at 0.5 µm/px; mean, std. dev., min/max, Haralick (distance 1, 32 bins) |
| Shape | `addShapeMeasurements` | area, length, circularity, solidity, min/max diameter, nucleus/cell ratio |
| Context | `SmoothFeaturesPlugin` | 50 µm FWHM neighbourhood averages |
| Export | `saveDetectionMeasurements` | one TSV per image: 214 columns per cell |

A 2.0 µm/px intensity run from the original command history was removed: nuclei are only
3–6 pixels wide at that scale, and most Haralick values were missing.

## Running it

The script needs an annotation marking the region to analyse. If an image has none, it
imports `annotations/<image name>.geojson` from the QuPath project folder, and stops
if there is neither (so a whole slide is never processed by accident).

- **QuPath GUI:** open the project, *Automate > Show script editor*, open the script, *Run*;
  or *Automate > Project scripts > Run for project* for every image.
- **Headless** (use absolute paths; a relative project path fails):
  ```bash
  QuPath-0.7.0-arm64 script -p /abs/path/project.qpproj -i slide.tif /abs/path/scripts/classical_features.groovy
  ```
- Environment variables: `QP_RESULTS_SUBDIR` (output folder, default `results`) and
  `QP_FORCE_GEOJSON=1` (clear existing objects and use the GeoJSON outline).

Output: `<project>/<results>/<image>_cell_features.tsv`. The tables are large and are not committed.
`Object ID` changes on every run; use the centroids to match cells between runs.

## Example: CAMELYON16 `tumor_084`

| Run | Region | Cells | Time | Peak memory |
|-----|--------|------:|-----:|------------:|
| Region | ~1.2 × 1.15 mm hand-drawn annotation (1.39 mm²) | 16,707 | ~17 s | ~1.7 GB |
| Whole tissue | 103.5 mm² outline (`annotations/tumor_084.tif.geojson`) | 667,332 | 12.5 min | ~10 GB RAM, 1.0 GB TSV |

Measured on a 10-core Apple-silicon Mac with 26 GB RAM. The GUI run and a headless rerun
gave identical values (all numeric columns), and the same area inside the whole-tissue run
has matching medians (nuclear area 15.8 vs 15.7 µm², hematoxylin OD mean 0.83 vs 0.83).
The tissue outline was exported from LazySlide's tissue mask so that other methods can
analyse the same tissue.

`scripts/make_feature_figures.py` (Python, separate from QuPath) plots a feature table:
histograms for quality checks and morphology, a correlation heatmap and spatial maps; see
[`figures/`](figures). The spatial maps of the region show a sharp boundary between sparse
tissue with larger, paler nuclei and a dense area with small, dark, round nuclei.

```bash
python scripts/make_feature_figures.py results/tumor_084_cell_features.tsv figures
```

## Limitations
- Segmentation is imperfect: 720 of 667,332 nuclei exceed 100 µm² and are probably merged nuclei.
- Cell area depends on the fixed 5 µm expansion and is not a biological measurement.
- One slide so far; no performance claim is made.

## Reference
Bankhead P. et al. **QuPath: Open source software for digital pathology image analysis.** *Sci. Rep.* 7, 16878 (2017).
