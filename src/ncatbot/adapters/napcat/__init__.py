import sys

import napcat.exceptions
import napcat.matcher
import napcat.types
from napcat import NapCatClient, __version__

from ..base import BaseAdapter


class NapCatAdapter(NapCatClient, BaseAdapter):
    @property
    def adapter_name(self) -> str:
        return "Ncatbot.NapCatAdapter"

    @property
    def adapter_version(self) -> str:
        return __version__

    @property
    def platform_name(self) -> str:
        return "qq"


exceptions = napcat.exceptions
types = napcat.types
matcher = napcat.matcher

sys.modules[f"{__name__}.exceptions"] = exceptions
sys.modules[f"{__name__}.types"] = types
sys.modules[f"{__name__}.matcher"] = matcher

__all__ = ["NapCatAdapter"]
