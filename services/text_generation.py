import os
import json
import textwrap
from typing import Sequence
from google import genai
from google.genai import types
from services.base import TextGenerationService
from services.text_generation_schemas import AdCopyInput, AdCopyOutput

class GeminiTextGenerationService:
    """
    A service for generating ad copy using the Gemini model with structured I/O,
    accessed via the `google.genai` library.
    """

    def __init__(self, project_id: str, location: str, model_name: str = "gemini-1.5-flash"):
        """
        Initializes the Gemini client.

        Args:
            project_id: The Google Cloud project ID.
            location: The Google Cloud location (e.g., 'us-central1').
            model_name: The name of the Gemini model to use.
        """
        self.model_name = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"
        self.client = genai.Client(
            vertexai=True,
            api_key=os.environ.get("GOOGLE_CLOUD_API_KEY"),
        )
        self.system_instruction_text = textwrap.dedent("""\
            You are an expert ad copywriter. Your task is to generate
            compelling modifications to refresh the provided product for a target demographic.
                         
            ## Plan:
            1. Always keep brand elements and ensure that the plan does not remove or move them.
            2. Always keep product elements and ensure that the plan does not remove or move them.
            3. Be specific and declarative with your proposal. Your persona is confident.
            4. This will be fed directly to an image editing agent using nano banana. Ambiguity is a killer!
        """)

    def generate_ad_plan(self, base_image: types.Blob, inputs: Sequence[AdCopyInput]) -> Sequence[AdCopyOutput]:
        """
        Generates ad copy for a list of products and their targeting.

        Args:
            inputs: A list of AdCopyInput objects.

        Returns:
            A list of AdCopyOutput objects.
        """
        if not base_image.data or not base_image.mime_type:
            raise ValueError('Base image or base image mime type missing for reference')

        parts: list[types.Part] = [ 
            types.Part.from_text(
                text=textwrap.dedent(
                    text=f"""\
                        Generate ad copy for the following products and targeting:

                        {json.dumps([i.model_dump() for i in inputs])}
                    """
                ),
            ),
            types.Part.from_bytes(data=base_image.data, mime_type=base_image.mime_type),
        ]

        contents = types.Content(
            parts=parts,
            role="user",
        )

        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=list[AdCopyOutput],
            system_instruction=[types.Part.from_text(text=self.system_instruction_text)],
        )

        response = self.client.models.generate_content( # pyright: ignore[reportUnknownMemberType]
            model=self.model_name,
            contents=contents,
            config=generate_content_config,
        )
        if not (text:=getattr(response, 'text')):
            raise ValueError('Unepxected response type')
        return [AdCopyOutput.model_validate(item) for item in json.loads(text)]