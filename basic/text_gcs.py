#!/usr/bin/env python3

"""Provides a subcommand for the main CLI to generate text advertisements.

This script processes a TextPrompts protobuf definition, which can be provided
as a JSON string, a textproto string, a local file path, or a Google Cloud
Storage (GCS) path. It uses the specified prompts, products, pitches, and
targeting attributes to generate headlines and descriptions for ads.

The generated ad data (headlines and descriptions) is stored in a JSON file
within a specified GCS bucket. There is also an option to export this
generated JSON data into a CSV format, also saved to GCS.
"""

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
import re
from io import StringIO

import click
from google.cloud import storage
from google.protobuf import json_format
from google.protobuf import text_format
import vertexai
from vertexai.preview.language_models import TextGenerationModel

from services.text_prompts_pb2 import TextPrompts

TEXT_GENERATED_JSON = 'generated/text_ads.json'
TEXT_GENERATED_CSV = 'generated/text_ads.csv'

def get_gcs_json_path(gcs_bucket: str) -> str:
  return f"generated/text_ads.json"

def get_gcs_csv_path(gcs_bucket: str) -> str:
  return f"generated/text_ads.csv"

def prompt_replace(prompt:str, variables:dict):
  '''Helper to replaces keys in a string with values from a dict.'''
  for k, v in variables.items():
    prompt = prompt.replace(f"{{{k}}}",v)
  return prompt

def prompt_format(prompt: str) -> str:
  """Helper to format lists into a string."""
  return '\n'.join(prompt)

def _safely_generate_list(model, prompt: str) -> list[str]:
    response = model.predict(prompt)
    # Use a regular expression to find all occurrences of "Ad copy:"
    # followed by the text until a newline or the end of the string.
    matches = re.findall(r"Ad copy:([^\n]*)", response.text)
    # Strip leading/trailing whitespace from each match
    return [match.strip() for match in matches]


def _convert_text_ads_json_to_csv_content(json_content: str) -> str:
  '''Converts generated text ads JSON content into a CSV string.'''
  ads = json.loads(json_content)
  output = StringIO()
  csv_writer = csv.writer(output)

  # Header definition
  headlines_header = [f'Headline {number}' for number in range(1, 15)]
  descriptions_header = [f'Description {number}' for number in range(1, 5)]
  csv_writer.writerow(
    ['Product', 'Pitch', 'Audience'] +
    headlines_header +
    descriptions_header
  )

  for product, product_data in ads.items():
    for pitch, pitch_data in product_data.items():
      for audience, audience_data in pitch_data.items():
        # Prepare headlines, padding with empty strings if fewer than 14
        headlines = audience_data['headlines']
        headlines_padded = headlines + [''] * (len(headlines_header) - len(headlines))
        
        # Prepare descriptions, padding with empty strings if fewer than 4
        descriptions = audience_data['descriptions']
        descriptions_padded = descriptions + [''] * (len(descriptions_header) - len(descriptions))

        csv_writer.writerow(
          [product, pitch, audience] +
          headlines_padded +
          descriptions_padded
        )
  return output.getvalue()


def json_to_csv(gcs_bucket: str):
  '''Helper to convert generated JSON into a CSV for export, using GCS.'''
  storage_client = storage.Client()
  bucket = storage_client.bucket(gcs_bucket)

  # Read JSON from GCS
  json_blob = bucket.blob(get_gcs_json_path(gcs_bucket))
  json_content = json_blob.download_as_string().decode('utf-8')

  # Convert JSON to CSV using the pure function
  csv_content = _convert_text_ads_json_to_csv_content(json_content)

  # Write CSV to GCS
  csv_blob = bucket.blob(get_gcs_csv_path(gcs_bucket))
  csv_blob.upload_from_string(csv_content, 'text/csv')


def load_text_prompts(targets: str) -> TextPrompts:
  """Loads text prompts from a string, local file, or GCS file.

  The input can be in JSON or textproto format.

  Args:
    targets: A string containing the prompts in JSON or textproto format,
      a local file path, or a GCS file path.

  Returns:
    A TextPrompts protobuf message.
  """
  prompts = TextPrompts()
  try:
    # Try parsing as JSON
    json_format.Parse(targets, prompts)
    return prompts
  except json_format.ParseError:
    try:
      # Try parsing as textproto
      text_format.Parse(targets, prompts)
      return prompts
    except text_format.ParseError:
      # If both fail, assume it's a path
      if targets.startswith('gs://'):
        # GCS path
        storage_client = storage.Client()
        bucket_name, blob_name = targets[5:].split('/', 1)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        content = blob.download_as_string().decode('utf-8')
        return load_text_prompts(content)
      else:
        # Local file path
        with open(targets, 'r') as f:
          content = f.read()
        return load_text_prompts(content)

@click.command(no_args_is_help=True)
@click.option('--targets', help='Textproto, JSON, local file, or gs:// file.', default=None)
@click.option('--export', '-e', is_flag=True, help='Export the JSON file to CSV.')
@click.option('--project', '-p', help='Cloud ID of Google Cloud Project.', default=None)
@click.option('--verbose', '-v', is_flag=True, help='Print all the steps as they happen.')
@click.option('--gcs_bucket', help='Google Cloud Storage bucket for input/output.', default=None)
def text_gcs(
  targets: str,
  export:bool,
  project:str,
  verbose:bool,
  gcs_bucket:str
):
  '''Loops through targets and generates images.

  Args:
    targets: a structure of image and targets
    export: convert json to csv
    project: the id of the Google Cloud Project
    verbose: to print output or not
    gcs_bucket: the GCS bucket to read and write data
  '''

  if export:
    return json_to_csv(gcs_bucket)

  targets = load_text_prompts(targets)
  
  vertexai.init(project=project)
  model = TextGenerationModel.from_pretrained("text-bison@001")

  storage_client = storage.Client()
  bucket = storage_client.bucket(gcs_bucket)

  # Read existing ads from GCS or initialize empty dict
  ads_blob = bucket.blob(get_gcs_json_path(gcs_bucket))
  try:
    ads_content = ads_blob.download_as_string().decode('utf-8')
    ads = json.loads(ads_content)
  except Exception:
    ads = {}

  for product in targets.products:
    ads.setdefault(product.product, {})
    print('PRODUCT:', product.product)
    for pitch_name in product.pitches:
      pitch = targets.pitches[pitch_name]
      ads[product.product].setdefault(pitch_name, {})
      print('  PITCH:', pitch_name)
      for target in targets.targeting:
        target_name = " - ".join(f"{key}:{value}" for key, value in target.attributes.items())
        if target_name in ads[product.product][pitch_name]:
          print('    EXISTS:', target_name)
        else:
          print('    AD:', target_name)
          variables = copy.deepcopy(target.attributes)
          variables['PRODUCT'] = product.product + ' - ' + product.description

          prompt_headlines = prompt_replace(prompt_format(targets.prompt.headlines) + ' ' + pitch.prompt, variables)
          prompt_descriptions = prompt_replace(prompt_format(targets.prompt.descriptions) + ' ' + pitch.prompt, variables)

          if verbose:
            print('    PROMPT HEADLINES:', prompt_headlines)
            print('    PROMPT DESCRIPTIONS:', prompt_descriptions)

          ads[product.product][pitch_name][target_name] = {
            'headlines': _safely_generate_list(model, prompt=prompt_headlines),
            'descriptions': _safely_generate_list(model, prompt=prompt_descriptions)
          }

  # Save the JSON file to GCS
  json_blob = bucket.blob(get_gcs_json_path(gcs_bucket))
  json_blob.upload_from_string(json.dumps(ads, indent=2), 'application/json')