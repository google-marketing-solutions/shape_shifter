
import abc
from typing import Any, Dict, List
from google.genai import types

class ExternalService(abc.ABC):
    """Abstract base class for external data services."""
    
    @abc.abstractmethod
    def get_targeting_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Retrieves targeting data from the external service."""
        pass

    @abc.abstractmethod
    def get_product_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Retrievis product data from the external service."""
        pass


class DV360Service(ExternalService):
    """Abstract base class for DV360 data service."""
    pass


class GoogleAdsService(ExternalService):
    """Abstract base class for Google Ads data service."""
    pass


class TextGenerationService[InputType, OutputType](abc.ABC):
    """Abstract base class for text generation services."""

    @abc.abstractmethod
    def generate_ad_copy(self, base_image: types.Blob, inputs: InputType) -> OutputType:
        """Generates ad copy for a list of products and their targeting."""
        pass


class ImageEditingService(abc.ABC):
    """Abstract base class for image editing services."""

    @abc.abstractmethod
    def edit_image(self, prompt: str, base_image_bytes: bytes) -> types.Image:
        """Edits an image based on a prompt."""
        pass
