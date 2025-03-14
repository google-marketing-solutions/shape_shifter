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
import os
import json
import argparse

from bqflow.util.configuration import Configuration
from bqflow.util.auth import get_credentials
from bqflow.util.vertexai_api import ImageAI, Image

IMAGE_GENERATED_JSON = 'generated/image_ads.json'
IMAGE_GENERATED_CSV = 'generated/image_ads.csv'

def prompt_replace(prompt:str, variables:list):
  '''Helper to replaces keys in a string with values from a dict.'''
  for k, v in variables.items():
    prompt = prompt.replace(k,v)
  return prompt


def json_to_csv():
  '''Helper to convert generated JSON into a CSV for export.'''
  with open(IMAGE_GENERATED_JSON, 'r') as file:
    ads = json.load(file)

  with open(IMAGE_GENERATED_CSV, 'w') as file:
    csv_writer = csv.writer(file)

    csv_writer.writerow(['Product', 'Scene', 'Audience', 'Image'])

    for product, product_data in ads.items():
      for scene, scene_data in product_data.items():
        for audience, audience_data in scene_data.items():
          csv_writer.writerow([product, scene, audience] + ['n'.join(audience_data)])


def main(
  prompts:dict,
  export:bool,
  project:str,
  service:str,
  client:str,
  user:str, 
  verbose:bool
):
  '''Loops through prompts and generates images.

  Args:
    prompts: a structure of image and prompts
    export: convert the generated JSON file to a CSV
    project: the id of the Google Cloud Project
    service: a path to credentials
    client: a path to credentials
    user: a path to credentials
    verbose: to print output or not
  '''

  if export:
    return json_to_csv()

  config = Configuration(
    project=project,
    service=service,
    client=client,
    user=user,
    verbose=verbose
  )

  image_ai = ImageAI(config = config, auth = 'user')
  ads = {}

  with open(prompts, 'r') as file:
    spec = json.load(file)

  for image in spec['images']:
    ads.setdefault(image['image'], {})
    print('IMAGE:', image['image'])
    local_image =  Image.load_from_file(image['file'])
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
        if os.path.exists(filename):
          ads[image['image']][scene][target_name].append(filename)
          print('    EXISTS: ', f'generated/{ai["file"]} - 1.jpg')
        else:
          for variant, ai_image in enumerate(image_ai.safely_edit_image(
            prompt = ai['prompt'],
            base_image = local_image
          ), 1):
            filename = f'generated/{ai["file"]} - {variant}.jpg'
            ads[image['image']][scene][target_name].append(filename)
            ai_image.save(filename)
            print('    FILE:', filename)

        with open('generated/image_ads.json', "w") as file:
          json.dump(ads, file, indent=2)


if __name__ == '__main__':

  # load command line parameters
  parser = argparse.ArgumentParser()

  parser.add_argument('--prompts', help='Prompt file to use, must be json.', default=None)
  parser.add_argument('--export', '-e', help='Export the JSON file to CSV.', action='store_true')
  parser.add_argument('--project', '-p', help='Cloud ID of Google Cloud Project.', default=None)
  parser.add_argument('--service', '-s', help='Path to SERVICE credentials json file.', default=None)
  parser.add_argument('--client', '-c', help='Path to CLIENT credentials json file.', default=None)
  parser.add_argument('--user', '-u', help='Path to USER credentials json file.', default=None)
  parser.add_argument('--verbose', '-v', help='Print all the steps as they happen.', action='store_true')

  main(**vars(parser.parse_args()))
