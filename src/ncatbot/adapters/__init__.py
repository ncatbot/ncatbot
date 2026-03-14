import sys

import napcat
from napcat import NapCatClient, __version__

from .base import BaseAdapter
from .internal import InternalEventAdapter


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

sys.modules[f"{__name__}.napcat"] = napcat

__all__ = ["BaseAdapter", "InternalEventAdapter", "NapCatAdapter", "napcat"]
