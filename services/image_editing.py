from __future__ import annotations
import base64
from typing import Literal
from google import genai
from google.genai import types
from services.base import ImageEditingService

class VertexAIImageEditingService(ImageEditingService):
    """
    Vertex AI implementation of the ImageEditingService using the Gemini-2.5-Flash-Image model
    (aka "Nano Banana").
    """

    def __init__(self, *, project_id: str, location: str, model_name: str = "gemini-2.5-flash-image"):
        """
        Initializes the service.

        Args:
            project_id: The Google Cloud project ID.
            location: The Google Cloud location (e.g., 'us-central1').
            model_name: The name of the Gemini model to use.
        """
        self.model = model_name
        self.client = genai.Client(
            vertexai=True,
            location=location,
            project=project_id,
        )

    def edit_image(self, prompt: str, base_image_bytes: bytes) -> types.Image:
        """
        Edits an image using the Vertex AI Gemini-3-Pro-Image model.

        Args:
            prompt: The text prompt describing the desired edit.
            base_image_bytes: The raw bytes of the image to be edited.

        Returns:
            The raw bytes of the edited image in PNG format.
        """
        parts = [
            types.Part.from_bytes(data=base_image_bytes, mime_type="image/jpeg"), # Assuming input is JPEG
            types.Part.from_text(text=prompt)
        ]
        content = types.Content(
                role="user",
                parts=parts,
            )

        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            max_output_tokens=32768,
            response_modalities=["IMAGE"], # Request only image output
            safety_settings=[
            ],
        )

        response = self.client.models.generate_content( # pyright: ignore[reportUnknownMemberType]
            model=self.model,
            contents=content,
            config=generate_content_config,
        )
        if not (response.candidates and len(response.candidates)):
            raise ValueError('no candidate found')
        if not ((candidate:=response.candidates[0]) and candidate.content):
            raise ValueError('missing content in candidate')
        if not ((parts:=candidate.content.parts) and parts and len(parts)):
            raise ValueError('missing parts in candidate')
        if not ((part:=parts[0]) and (inline_data:=getattr(part, 'inline_data', None))):
            raise ValueError('missing mime type or inline data')
        return types.Image(mime_type=inline_data.mime_type, image_bytes=inline_data.data)


type AspectRatio = Literal['1:1', '3:2', '2:3', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9']