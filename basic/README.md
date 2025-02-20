# Basic Shape Shifter

This is a simple Python implementation using JSON to construct the prompts.
The JSON files become assets you can keep for specific campaigns.


## Text

Used to generate advertising copy from JSON files.

The script authenticates against a GCP project and executes the given prompts.
The included AI helpers from BQFlow are set to generate products correctly.
If you want to modify the behavior of the AI please see the BQFlow modules.

```
python text.py text.json -p [GCP PROJECT] -u ~user.json -v
```

Results are in: **generated/ads.json**

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

### Generated Ads

The resulting ads go into the **generated/ads.json** file.  The program checks
for ads that already exist and skips asking the AI for those.

### Suggested Process

1. Create a JSON file for you products, pitches, and targeting.
2. Generate a few ads and improve the prompts by editing the JSON.
3. Once prompt is good, run all the variants.
4. Review the file with the ads and remove any ads that need improving.
5. Run the script again and repeat culling until satisfied.
6. Transform the ads JSON into a CSV and upload the ads to the ad platform.

Adding campaign or ad level identifiers scenes, targeting, or images.
This allows you to synchronize creatives with campaigns.
For advanced users, modify the Python script to generate a mapping file.


## Images

Used to generate advertising images from JSON files.

The script authenticates against a GCP project and executes the given prompts.
The included AI helpers from BQFlow are set to generate products correctly.
If you want to modify the behavior of the AI please see the BQFlow modules.

```
python image.py image.json -p [GCP PROJECT] -u ~user.json -v
```

### JSON Prompt File

The Prompt file consists of three parts:

##### Prompt

The general prompt added to every scene.

##### The Images

Currently sourced from **../docs/images/**, these are loaded into the AI for
editing.  Each image has a name, path, and associated scenes the AI will
generate.

##### The Scenes

These are specific prompts to render the product into.

##### The Targeting

These are variables used to customize the prompt and scenes.  Each key is
replaced with its value in the final prompt sent to the AI.  This allows
creating unlimited custom variants.

### Generated Images

The resulting images go into the **generated** folder.  The program checks
for images that already exist and skips asking the AI for those. They have the
following format:

generated/IMAGE - SCENE - TARGETING - VARIANT.jpg

- IMAGE, SCENE, TARGETING are from the JSON file.
- VARIANT is 1 unless you alter the script to generate multiple prompt images.

### Suggested Process

1. Create a JSON file for you product, scenes, and targeting.
2. Generate a few images and improve the prompts by editing the JSON.
3. Once prompt is good, run all the variants.
4. Review the folder with the images and remove any images that need improving.
5. Run the script again and repeat culling until satisfied.
6. Upload the images as creatives to the ad platform.

Adding campaign or ad level identifiers scenes, targeting, or images. 
This allows you to synchronize creatives with campaigns.
For advanced users, modify the Python script to generate a mapping file.
