###########################################################################
#
#  Copyright 2024 Google LLC
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

from bqflow.util.auth import get_credentials
import google.auth
import googleapiclient.discovery as discovery
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, HttpError
from bqflow.util.data import get_rows, put_rows
from bqflow.util.drive import Drive, API_Drive
import shutil
import io
import os
import cv2
import numpy as np

API_NAME = "displayvideo"
API_VERSION = "v2"
API_SCOPES = ["https://www.googleapis.com/auth/display-video",
              "https://www.googleapis.com/auth/display-video-user-management"]

def create_creatives(dv_service: any, assets: list[dict], kwargs_list: list) -> None:
    """Creates creatives in DV360

    Args:
        dv_service: the DV360 service to call the API
        assets: a list of assets to attach to a creative
    """
    ad_contents = []
    for kwargs in kwargs_list:
        contents = {}
        contents['URI'] = kwargs['URI']
        contents['Text'] = kwargs['Text'].split('text:')[1].split('"')[1]
        ad_contents.append(contents)

    for asset in assets:
        asset_name = asset.get("name")
        media_id = asset.get("media_id")
        icon_media_id = "126987487024" # Use same icon for all creatives for now
        advertiser_id = asset_name.split("_")[0] if len(asset_name.split("_")) > 0 else 0
        campaign_id = asset_name.split("_")[1] if len(asset_name.split("_")) > 0 else 0
        asset_display_name = asset_name.split("_")[5]
        content = "My Content!"

        # get advertiser.
        advertiser = dv_service.advertisers().get(
            advertiserId=advertiser_id).execute()
        
        # get campaign.
        campaign = dv_service.advertisers().campaigns().get(
            advertiserId=advertiser_id,
            campaignId=campaign_id).execute()

        if advertiser_id == 0:
            print(f"The advertiser id for asset {asset_name} is not valid.")
            return

        for ad_content in ad_contents:
            if ad_content['URI'] == asset_name.split('-0.png')[0] and len(ad_content['Text']) <= 90:
                content = ad_content['Text']

        creative_obj = {
            'name': asset_name,
            'displayName': asset_display_name,
            'entityStatus': 'ENTITY_STATUS_ACTIVE',
            'hostingSource': 'HOSTING_SOURCE_HOSTED',
            'creativeType': 'CREATIVE_TYPE_NATIVE',
            'dimensions': {
                'heightPixels': 1200,
                'widthPixels': 627
        },
        'assets': [
            {
                'asset': {'mediaId' : media_id},
                'role': 'ASSET_ROLE_MAIN'
            },
            {
                'asset': {'mediaId' : icon_media_id},
                'role': 'ASSET_ROLE_ICON'
            },
            {
                'asset': {'content' : advertiser['displayName']},
                'role': 'ASSET_ROLE_ADVERTISER_NAME'
            },
            {
                'asset': {'content' : campaign['displayName']},
                'role': 'ASSET_ROLE_HEADLINE'
            },
            {
                'asset': {'content' : content},
                'role': 'ASSET_ROLE_BODY'
            },
            {
                'asset': {'content' : "https://www.google.com/"},
                    'role': 'ASSET_ROLE_CAPTION_URL'
            },
            {
                'asset': {'content' : "Buy Now"},
                'role': 'ASSET_ROLE_CALL_TO_ACTION'
            },
        ],
        'exitEvents': [
            {
                'type': 'EXIT_EVENT_TYPE_DEFAULT',
                'url': "https://www.google.com/"
            }
        ]
        }
        # Create the creative.
        creative = dv_service.advertisers().creatives().create(
        advertiserId=advertiser_id,
        body=creative_obj
        ).execute()
        # Display the new creative.
        print(f"Creative {creative['name']} was created.")


def list_files_from_drive(config, auth, drive_url: str) -> list[any]:
    """Lists files from a drive folder

    Args:
        config (class): an object conatining the credentials and project settings
        auth: authentication type
        drive_url: the url for the drive folder
    Returns:
        files: a list of files in the provided drive url
    """
    files = []
    root = Drive(config, auth).file_id(drive_url)
    q = f'"{root}" in parents and trashed=false'
    for file in API_Drive(config, auth, iterate=True).files().list(
      q=q, fields='files(id,name,parents)'
    ).execute():
        files.append(file)
    return files


def download_file(config: dict, auth: str, file: any, temp_dir: str) -> None:
    """Download a file from Drive to local storage

    Args:
        config (class): an object conatining the credentials and project settings
        auth: authentication type
        file: file object to download
        temp_dir: tempt dir to store the downloaded files
    """
    service = discovery.build('drive', 'v3', credentials=get_credentials(config, auth))
    request = service.files().get_media(fileId=file["id"])
    #request1 = API_Drive(config, auth).get_media(fileId=file_id)
    try:
        fh = io.BytesIO()
        # Initialise a downloader object to download the file
        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False
        # Download the data in chunks
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)

        # Write the received data to the file
        os.makedirs(temp_dir, exist_ok=True)
        file_name = f"{temp_dir}/{file['name']}"
        with open(file_name, 'wb') as f:
            shutil.copyfileobj(fh, f)

        print("File Downloaded")

        resize_image(file_name)

        # Return True if file Downloaded successfully
        return True
    except Exception as ex:
        print(f"Something went wrong: {ex}")
        return False

def resize_image(src_image):
    # read image
    old_image = cv2.imread(src_image)
    old_image_height, old_image_width, channels = old_image.shape

    # create new image of desired size and color (blue) for padding
    new_image_width = 2940
    new_image_height = 1538
    color = (255,255,255)
    result = np.full((new_image_height,new_image_width, channels), color, dtype=np.uint8)

    # compute center offset
    x_center = (new_image_width - old_image_width) // 2
    y_center = (new_image_height - old_image_height) // 2

    # copy img image into center of result image
    result[y_center:y_center+old_image_height, 
        x_center:x_center+old_image_width] = old_image

    # save result
    os.remove(src_image)
    cv2.imwrite(src_image, result)

def do_upload_asset(dv_service: any, assets_temp_dir: str) -> list[dict]:
    """Uploads an asset to DV360

    Args:
        dv_service: the DV360 service to call the API
        assets_temp_dir: a temp dir where the assets are stored locally
    Returns:
        assets: list of uploaded assets
    """
    assets_dir = os.listdir(assets_temp_dir)
    assets = []
    for asset_name in assets_dir:
        if '.png' in asset_name:
            asset_path = f"{assets_temp_dir}/{asset_name}"
            advertiser_id = asset_name.split("_")[0] if len(asset_name.split("_")) > 0 else 0
            if advertiser_id == 0:
                print(f"The advertiser id for asset {asset_name} is not valid")
                return

            body = {
                "filename": asset_name
            }

            # Create upload object.
            media = MediaFileUpload(asset_path)
            if not media.mimetype():
                media = MediaFileUpload(asset_path, "application/octet-stream")

            # Upload the asset.
            response = dv_service.advertisers().assets().upload(
                advertiserId=advertiser_id,
                body=body,
                media_body=media
            ).execute()

            # Display the new asset media ID.
            assets.append({"name": asset_name, "media_id": response['asset']['mediaId']})
            print("Asset was created with media ID %s" % response['asset']['mediaId'])

            os.remove(asset_path)
    return assets

def upload_assets(config: dict, log: dict, task: dict) -> None:
    """Uploads a list of assets to DV360
    Args:
        config (class): an object conatining the credentials and project settings
        log (class): an object that can be logged to.
        task (dict): the parameters passed from the workflow (see top level doc).
    """
    if "upload" in task:
        auth = task.get("auth")

        # get parameters
        if 'kwargs' in task:
            kwargs_list = task['kwargs'] if isinstance(task['kwargs'], (list, tuple)) else [task['kwargs']]
        elif 'kwargs_remote' in task:
            kwargs_list = get_rows(
            config,
            task['auth'],
            task['kwargs_remote'],
            as_object=True
            )

        assets_temp_dir = f"{os.getcwd()}/workflows/temp"
        drive_url = task.get("upload").get("drive_url")
        dv_service = discovery.build(API_NAME, API_VERSION, credentials=get_credentials(config, task.get("auth")))
        # Download files to local directory
        files = list_files_from_drive(config, auth, drive_url)
        for file in files:
            # Download files to local storage first
            download_file(config, auth, file, assets_temp_dir)

        # Upload assets to DV360
        dv_uploaded_assets = do_upload_asset(dv_service, assets_temp_dir)
        # Attach assets to new creatives
        create_creatives(dv_service, dv_uploaded_assets, kwargs_list)
