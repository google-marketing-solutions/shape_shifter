import os
import json

from countries import COUNTRIES

ADS_PATH = 'docs'

SCENES = {
  'Landscape':'Include only this one car in the photo. The car parked in a beautiful landscape found in a travel magazine from COUNTRY. The photo is from an exotic luxury travel magazine. The terrain under the car matches the terrain in the background. The photo has an adventure mood. The sky is sunny and clear. The car is the only object in the foreground, create distance around the car. The photo was taken using a wide angle lens by a professional photographer for an luxury travel magazine cover. The season is summer.  The time of day is the golden hour.',
  'Farm':'Include only this one car in the photo. The car is parked in the center of a farm field dirt road with native crops from COUNTRY. The dirt road is visible and goes diagonally from the bottom right corner to the middle left side of the photo. The low crops in the distance and foreground are indigenous to COUNTRY. In the distance are large indigenous trees. The photo has a calm mood. The lower left side of the photo has some low crops. The sky is sunny and clear. The car is the only object in the foreground, create distance around the car. The photo was taken using a wide angle lens by a professional photographer for an luxury travel magazine cover. The season is summer.  The time of day is the golden hour.',
  'Street':'Include only this one car in the photo. Make the car look like it is parked on the street in front of a single neat, stylish, and cheerful house in the country of COUNTRY that would appeal to the LIFESTYLE persona from that country. The house looks like it is from the cover of a luxury magazine in COUNTRY. The perspective is front view.',
  'Counter':'Include only this one lotion bottle in the photo. Replace the background with a kitchen counter and a decorative plant representing the culture, colors, and theme of COUNTRY.  The photo was taken using a professional photographer for a luxury home magazine cover. The season is summer.  The time of day is bright morning.',
  'Garden':'Include only this one lotion bottle in the photo. Replace the background with a calm garden representing the culture, colors, and theme of COUNTRY.  The photo was taken using a professional photographer for a luxury home magazine cover. The season is summer.  The time of day is the golden hour.',
  'Flowers':'Include only this one lotion bottle in the photo. Replace the background with a few scattered flowers and petals representing the culture, colors, and theme of COUNTRY.  The flowers are vigrant and alive.  The photo was taken using a professional photographer for a luxury home magazine cover. The light is white and diffuse with a spa look.',
}

if __name__ == '__main__':
  ads = {}
  labels = {}

  counter = 0
  for filename in os.listdir(f'{ADS_PATH}/generated'):
    counter += 1
    if filename.endswith(".jpg"):
      try:
        product, feature, scene, country, _ = filename.split(' - ')
        lookup = product.lower().replace(' ', '')
        label = f"{lookup}_{country.lower().replace(' ', '_')}"

        ads.setdefault(lookup, [])
        ads[lookup].append({
          'id':f'id_{counter}',
          'image':f'generated/{filename}',
          'country':country,
          'coordinates':COUNTRIES[country],
          'label':label,
          'scene':scene,
          'feature':feature,
          'prompt':SCENES[scene],
        })

      except ValueError:
        print(f'ERROR: {filename}')
        pass

  with open(f'{ADS_PATH}/ads.js', 'w') as f:
    f.write(f'const ads = {json.dumps(ads, indent=2)}')

  print(f'{counter} Ads Written')
