from typing import TypedDict

class DistroItem(TypedDict):
    name: str
    is_default: bool
    is_chosen: bool
