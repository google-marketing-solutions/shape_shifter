#!/usr/bin/env python3

###########################################################################
#
#  Copyright 2025 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
###########################################################################

import csv
import json
import argparse
from io import BytesIO, StringIO

from google.cloud import storage
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel, Image as VertexImage

IMAGE_GENERATED_JSON = 'generated/image_ads.json'
IMAGE_GENERATED_CSV = 'generated/image_ads.csv'

def get_gcs_json_path(gcs_bucket: str) -> str:
  return f"generated/image_ads.json"

def get_gcs_csv_path(gcs_bucket: str) -> str:
  return f"generated/image_ads.csv"

def prompt_replace(prompt:str, variables:dict):
  '''Helper to replaces keys in a string with values from a dict.'''
  for k, v in variables.items():
    prompt = prompt.replace(k,v)
  return prompt


def _convert_image_ads_json_to_csv_content(json_content: str) -> str:
  '''Converts generated image ads JSON content into a CSV string.'''
  ads = json.loads(json_content)
  output = StringIO()
  csv_writer = csv.writer(output)

  csv_writer.writerow(['Product', 'Scene', 'Audience', 'Image'])

  for product, product_data in ads.items():
    for scene, scene_data in product_data.items():
      for audience, audience_data in scene_data.items():
        csv_writer.writerow([product, scene, audience] + ['\n'.join(audience_data)])
  return output.getvalue()


def json_to_csv(gcs_bucket: str):
  '''Helper to convert generated JSON into a CSV for export, using GCS.'''
  storage_client = storage.Client()
  bucket = storage_client.bucket(gcs_bucket)

  # Read JSON from GCS
  json_blob = bucket.blob(get_gcs_json_path(gcs_bucket))
  json_content = json_blob.download_as_string().decode('utf-8')

  # Convert JSON to CSV using the pure function
  csv_content = _convert_image_ads_json_to_csv_content(json_content)

  # Write CSV to GCS
  csv_blob = bucket.blob(get_gcs_csv_path(gcs_bucket))
  csv_blob.upload_from_string(csv_content, 'text/csv')


def main(
  prompts:str,
  export:bool,
  project:str,
  verbose:bool,
  gcs_bucket:str
):
  '''Loops through prompts and generates images.'''

  if export:
    return json_to_csv(gcs_bucket)

  vertexai.init(project=project)
  model = ImageGenerationModel.from_pretrained("imagegeneration@005")

  storage_client = storage.Client()
  bucket = storage_client.bucket(gcs_bucket)

  # Read existing ads from GCS or initialize empty dict
  ads_blob = bucket.blob(get_gcs_json_path(gcs_bucket))
  try:
    ads_content = ads_blob.download_as_string().decode('utf-8')
    ads = json.loads(ads_content)
  except Exception:
    ads = {}

  # Read prompt spec from GCS
  prompt_blob = bucket.blob(prompts)
  spec_content = prompt_blob.download_as_string().decode('utf-8')
  spec = json.loads(spec_content)

  for image in spec['images']:
    ads.setdefault(image['image'], {})
    print('IMAGE:', image['image'])
    
    # Load image from GCS
    image_blob = bucket.blob(image['file'])
    image_bytes = image_blob.download_as_bytes()
    base_image = VertexImage(image_bytes)
    
    for scene in image['scenes']:
      ads[image['image']].setdefault(scene, {})
      print('  SCENE:', scene)
      for target in spec['targeting']:
        target_name = " - ".join(f"{key}:{value}" for key, value in target.items())
        ads[image['image']][scene].setdefault(target_name, [])
        ai = {
          'prompt':prompt_replace(spec['prompt'] + ' ' + spec['scenes'][scene]['prompt'], target),
          'file':f'{image["image"]} - {scene} - {target_name}'
        }
        
        filename = f'generated/{ai["file"]} - 1.jpg'
        
        # Check if image exists in GCS
        image_exists_blob = bucket.blob(filename)

        if image_exists_blob.exists():
          ads[image['image']][scene][target_name].append(filename)
          print('    EXISTS: ', filename)
        else:
          images = model.edit_image(
            prompt = ai['prompt'],
            base_image = base_image,
            number_of_images=1
          )
          
          for variant, ai_image in enumerate(images, 1):
            generated_filename = f'generated/{ai["file"]} - {variant}.jpg'
            
            # Save the image to GCS
            output_blob = bucket.blob(generated_filename)
            img_byte_arr = BytesIO()
            ai_image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            output_blob.upload_from_string(img_byte_arr, 'image/jpeg')
            
            ads[image['image']][scene][target_name].append(generated_filename)
            print('    FILE:', generated_filename)

  # Save the JSON file to GCS
  json_blob = bucket.blob(get_gcs_json_path(gcs_bucket))
  json_blob.upload_from_string(json.dumps(ads, indent=2), 'application/json')


if __name__ == '__main__':

  # load command line parameters
  parser = argparse.ArgumentParser()

  parser.add_argument('--prompts', help='Prompt file to use, must be json.', default=None)
  parser.add_argument('--export', '-e', help='Export the JSON file to CSV.', action='store_true')
  parser.add_argument('--project', '-p', help='Cloud ID of Google Cloud Project.', default=None)
  parser.add_argument('--verbose', '-v', help='Print all the steps as they happen.', action='store_true')
  parser.add_argument('--gcs_bucket', help='Google Cloud Storage bucket for input/output.', default=None)

  args = parser.parse_args()

  main(
    prompts=args.prompts,
    export=args.export,
    project=args.project,
    verbose=args.verbose,
    gcs_bucket=args.gcs_bucket
  )