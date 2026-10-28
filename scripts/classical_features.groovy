/**
 * Classical (handcrafted) cell features with QuPath's own algorithms.
 * Cleaned from QuPath 0.7.0's auto-generated command history (Workflow > Create script).
 *
 * Per image: H&E stain setup -> watershed cell detection inside the annotation(s)
 * -> intensity + Haralick features -> shape features -> smoothed (neighbourhood) features
 * -> one TSV of all cell measurements in <project>/results/.
 *
 * Needs an annotation on each image, or annotations/<image name>.geojson to import.
 * Run for the whole project: Automate > Project scripts > "Run for project".
 */

// ---- Parameters (change here, not in the calls below) ----
double DETECTION_PIXEL_SIZE = 0.5   // µm; resolution used for cell detection
double SMOOTH_FWHM = 50.0           // µm; radius for neighbourhood averaging

// ---- 0. Region to analyse ----
// Use the annotation(s) already on the image. If there are none, import the tissue outline
// <project>/annotations/<image name>.geojson (exported from LazySlide's tissue mask, so every
// method analyses the same tissue). Without either, stop rather than process a whole slide.
// QP_FORCE_GEOJSON=1 clears everything already on the image first, so the outline is used instead.
if (System.getenv('QP_FORCE_GEOJSON') == '1')
    clearAllObjects()
if (getAnnotationObjects().isEmpty()) {
    def name = getProjectEntry() != null ? getProjectEntry().getImageName() : getCurrentImageNameWithoutExtension()
    def geojson = new File(buildFilePath(PROJECT_BASE_DIR, 'annotations', name + '.geojson'))
    if (geojson.exists()) {
        addObjects(qupath.lib.io.PathIO.readObjects(geojson))
        println 'Imported tissue annotation(s) from ' + geojson
    } else {
        println 'No annotation on this image and no ' + geojson + ' - skipping.'
        return
    }
}

// ---- 1. Image type and stain vectors (QuPath default H&E) ----
setImageType('BRIGHTFIELD_H_E')
setColorDeconvolutionStains('{"Name" : "H&E default", "Stain 1" : "Hematoxylin", "Values 1" : "0.6511078257574492 0.7011930431234068 0.29049426072255424", "Stain 2" : "Eosin", "Values 2" : "0.2158989356208711 0.8011960501132094 0.5580972485873468", "Background" : " 255 255 255"}')

// ---- 2. Cell detection (nucleus + 5 µm cell expansion) inside the annotation(s) ----
selectAnnotations()
runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', '{"detectionImageBrightfield":"Hematoxylin OD","requestedPixelSizeMicrons":' + DETECTION_PIXEL_SIZE + ',"backgroundRadiusMicrons":8.0,"backgroundByReconstruction":true,"medianRadiusMicrons":0.0,"sigmaMicrons":1.5,"minAreaMicrons":10.0,"maxAreaMicrons":400.0,"threshold":0.1,"maxBackground":2.0,"watershedPostProcess":true,"cellExpansionMicrons":5.0,"includeNuclei":true,"smoothBoundaries":true,"makeMeasurements":true}')

// ---- 3. Intensity + Haralick (distance 1, 32 bins) ----
// Nuclear hematoxylin at 0.25 and 0.5 µm per pixel (2.0 µm was dropped: nuclei are too small, mostly NaN)
selectCells()
runPlugin('qupath.lib.algorithms.IntensityFeaturesPlugin', '{"pixelSizeMicrons":0.25,"region":"NUCLEUS","tileSizeMicrons":25.0,"colorOD":false,"colorStain1":true,"colorStain2":false,"colorStain3":false,"colorRed":false,"colorGreen":false,"colorBlue":false,"colorHue":false,"colorSaturation":false,"colorBrightness":false,"doMean":true,"doStdDev":true,"doMinMax":true,"doMedian":false,"doHaralick":true,"haralickDistance":1,"haralickBins":32}')
selectCells()
runPlugin('qupath.lib.algorithms.IntensityFeaturesPlugin', '{"pixelSizeMicrons":0.5,"region":"NUCLEUS","tileSizeMicrons":25.0,"colorOD":false,"colorStain1":true,"colorStain2":false,"colorStain3":false,"colorRed":false,"colorGreen":false,"colorBlue":false,"colorHue":false,"colorSaturation":false,"colorBrightness":false,"doMean":true,"doStdDev":true,"doMinMax":true,"doMedian":false,"doHaralick":true,"haralickDistance":1,"haralickBins":32}')
// Whole-cell eosin at 0.5 µm per pixel
selectCells()
runPlugin('qupath.lib.algorithms.IntensityFeaturesPlugin', '{"pixelSizeMicrons":0.5,"region":"ROI","tileSizeMicrons":25.0,"colorOD":false,"colorStain1":false,"colorStain2":true,"colorStain3":false,"colorRed":false,"colorGreen":false,"colorBlue":false,"colorHue":false,"colorSaturation":false,"colorBrightness":false,"doMean":true,"doStdDev":true,"doMinMax":true,"doMedian":false,"doHaralick":true,"haralickDistance":1,"haralickBins":32}')

// ---- 4. Shape features ----
selectCells()
addShapeMeasurements("AREA", "LENGTH", "CIRCULARITY", "SOLIDITY", "MAX_DIAMETER", "MIN_DIAMETER", "NUCLEUS_CELL_RATIO")

// ---- 5. Smoothed (neighbourhood) features - keep last, it averages everything above ----
selectAnnotations()
runPlugin('qupath.lib.plugins.objects.SmoothFeaturesPlugin', '{"fwhmMicrons":' + SMOOTH_FWHM + ',"smoothWithinClasses":false}')

// ---- 6. Export all cell measurements (all columns) ----
// Output folder can be overridden with the QP_RESULTS_SUBDIR environment variable (default: results)
def outDir = buildFilePath(PROJECT_BASE_DIR, System.getenv('QP_RESULTS_SUBDIR') ?: 'results')
mkdirs(outDir)
def name = getProjectEntry() != null ? getProjectEntry().getImageName() : getCurrentImageNameWithoutExtension()
def outFile = buildFilePath(outDir, GeneralTools.stripExtension(name) + '_cell_features.tsv')
saveDetectionMeasurements(outFile)
println 'Saved ' + outFile
