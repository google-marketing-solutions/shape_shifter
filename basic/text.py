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

import copy
import csv
import os
import json
import argparse

from bqflow.util.configuration import Configuration
from bqflow.util.auth import get_credentials
from bqflow.util.vertexai_api import TextAI

TEXT_GENERATED_JSON = 'generated/text_ads.json'
TEXT_GENERATED_CSV = 'generated/text_ads.csv'

def prompt_format(prompt:str):
  '''Helper to consolidate list prompt into a paragraph.'''
  return prompt if isinstance(prompt, str) else '\n'.join(prompt)


def prompt_replace(prompt:str, variables:list):
  '''Helper to replaces keys in a string with values from a dict.'''
  for k, v in variables.items():
    prompt = prompt.replace(k,v)
  return prompt


def json_to_csv():
  '''Helper to convert generated JSON into a CSV for export.'''
  with open(TEXT_GENERATED_JSON, 'r') as file:
    ads = json.load(file)

  with open(TEXT_GENERATED_CSV, 'w') as file:
    csv_writer = csv.writer(file)

    csv_writer.writerow(
      ['Product', 'Pitch', 'Audience'] + 
      [f'Headline {number}' for number in range(1, 15)] + 
      [f'Description {number}' for number in range(1, 5)]
    )

    for product, product_data in ads.items():
      for pitch, pitch_data in product_data.items():
        for audience, audience_data in pitch_data.items():
          csv_writer.writerow(
            [product, pitch, audience] +
            audience_data['headlines'] +
            audience_data['descriptions']
          )


def main(
  prompts:dict,
  export:bool,
  project:str,
  service:str,
  client:str,
  user:str, 
  verbose:bool,
):
  '''Loops through prompts and generates images.

  Args:
    prompts: a structure of image and prompts
    export: convert json to csv
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

  text_ai = TextAI(config = config, auth = 'user')

  try:
    with open(TEXT_GENERATED_JSON, 'r') as file:
      ads = json.load(file)
  except FileNotFoundError:
    ads = {}

  with open(prompts, 'r') as file:
    spec = json.load(file)

  for product in spec['products']:
    ads.setdefault(product['product'], {})
    print('PRODUCT:', product['product'])
    for pitch in product['pitches']:
      ads[product['product']].setdefault(pitch, {})
      print('  PITCH:', pitch)
      for target in spec['targeting']:
        target_name = " - ".join(f"{key}:{value}" for key, value in target.items())
        if target_name in ads[product['product']][pitch]:
          print('    EXISTS:', target_name)
        else:
          print('    AD:', target_name)
          target = copy.deepcopy(target)
          target['PRODUCT'] = product['product'] + ' - ' + product['description']

          prompt_headlines = prompt_replace(prompt_format(spec['prompt']['headlines']) + ' ' + spec['pitches'][pitch]['prompt'], target)
          prompt_descriptions = prompt_replace(prompt_format(spec['prompt']['descriptions']) + ' ' + spec['pitches'][pitch]['prompt'], target)

          if verbose:
            print('    PROMPT HEADLINES:', prompt_headlines)
            print('    PROMPT DESCRIPTIONS:', prompt_descriptions)

          ads[product['product']][pitch][target_name] = {
            'headlines': text_ai.safely_generate_list(prompt=prompt_headlines),
            'descriptions': text_ai.safely_generate_list(prompt=prompt_descriptions)
          }
          with open(TEXT_GENERATED_JSON, "w") as file:
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
