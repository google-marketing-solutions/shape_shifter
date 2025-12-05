# Basic Shape Shifter (Google Cloud Storage)

This is a simple Python implementation using JSON to construct the prompts and Google Cloud Storage (GCS) for input and output. The JSON files become assets you can keep for specific campaigns.

## Requirements

1. A Google Cloud Project with the Vertex AI API enabled.
2. A Google Cloud Storage bucket.
3. Authenticated `gcloud` CLI or a service account with `Storage Object Admin` and `Vertex AI User` roles.

## Setup

1. Clone the repository.
2. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. Upload your product images and `images.json` / `text.json` prompt files to your GCS bucket.

## Images

Used to generate advertising images from JSON files stored in GCS.

The script authenticates against a GCP project, reads prompts and images from a GCS bucket, generates images, and writes them back to the same bucket.

```bash
python basic/images_gcs.py --prompts images.json --gcs_bucket [YOUR_GCS_BUCKET] --project [GCP_PROJECT] -v
```

Results are in: `gs://[YOUR_GCS_BUCKET]/generated/`

### JSON Prompt File

The Prompt file consists of three parts:

##### Prompt

The general prompt added to every scene.

##### The Images

These are sourced from your GCS bucket. Each image has a name, path within the bucket, and associated scenes the AI will generate.

##### The Scenes

These are specific prompts to render the product into.

##### The Targeting

These are variables used to customize the prompt and scenes. Each key is
replaced with its value in the final prompt sent to the AI. This allows
creating unlimited custom variants.

### Generated Images

The resulting images go into the `generated` folder in your GCS bucket. The program checks
for images that already exist and skips asking the AI for those.

- `gs://[YOUR_GCS_BUCKET]/generated/image_ads.json`
- `gs://[YOUR_GCS_BUCKET]/generated/IMAGE - SCENE - TARGETING - VARIANT.jpg`

### Export to CSV

To export the generated image data to a CSV file in your GCS bucket:

```bash
python basic/images_gcs.py --export --gcs_bucket [YOUR_GCS_BUCKET]
```
The CSV will be saved at `gs://[YOUR_GCS_BUCKET]/generated/image_ads.csv`.

## Text

Used to generate advertising copy from JSON files.

The script authenticates against a GCP project and executes the given prompts.

```bash
python basic/text_gcs.py --prompts text.json --gcs_bucket [YOUR_GCS_BUCKET] --project [GCP_PROJECT] -v
```

Results are in: `gs://[YOUR_GCS_BUCKET]/generated/text_ads.json`

### JSON Prompt File

The Prompt file consists of three parts:

##### Prompt

The general prompt added to every AI call.

##### Pitches

Specific pitches your are making to help tune towards an audience.

##### Products

The products for which the ads are being generated.

##### The Targeting

These are variables used to customize the prompt and scenes.  Each key is
replaced with its value in the final prompt sent to the AI.  This allows
creating unlimited custom variants.

### Export to CSV

To export the generated text ads to a CSV file in your GCS bucket:

```bash
python basic/text_gcs.py --export --gcs_bucket [YOUR_GCS_BUCKET]
```
The CSV will be saved at `gs://[YOUR_GCS_BUCKET]/generated/text_ads.csv`.
