# Slide data (not stored in git)

The pipeline runs on one TCGA-BRCA whole-slide image ,the shared **hero slide** used
across all three stages of the progression.

| Slide | Size | GDC file UUID |
|-------|------|---------------|
| `TCGA-AR-A0TP-01Z-00-DX1.58E6A3A6-D1D7-4AE5-87A5-E823F04CBB2F.svs` | 1.23 GB | `f9415b74-ee9c-4e63-8deb-5fb8766256f8` |

It is **open access** — no login or token needed.

## Download

Direct link (browser):
```
https://api.gdc.cancer.gov/data/f9415b74-ee9c-4e63-8deb-5fb8766256f8
```

Or command line (saves to the shared folder the notebook looks in first):
```bash
mkdir -p ~/wsi-shared-slides
curl -L -o ~/wsi-shared-slides/TCGA-AR-A0TP-01Z-00-DX1.58E6A3A6-D1D7-4AE5-87A5-E823F04CBB2F.svs \
  https://api.gdc.cancer.gov/data/f9415b74-ee9c-4e63-8deb-5fb8766256f8
```

The notebook checks `~/wsi-shared-slides/` first, then `data/`. Drop the file in either.

Source: NCI Genomic Data Commons — https://portal.gdc.cancer.gov
