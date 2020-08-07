from datetime import datetime as dt
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Type, Union

from geojson_pydantic.features import Feature, FeatureCollection
from pydantic import Field, BaseModel, create_model
from pydantic.fields import FieldInfo

from .shared import Asset, BBox, ExtensionTypes, Link
from .extensions import Extensions
from .version import STAC_VERSION
from .api.extensions.context import ContextExtension
from .api.extensions.paging import PaginationLink
from .utils import decompose_model


class ItemProperties(BaseModel):
    """
    https://github.com/radiantearth/stac-spec/blob/v0.9.0/item-spec/item-spec.md#properties-object
    """

    datetime: Union[str, dt] = Field(..., alias="datetime")
    # stac common metadata (https://github.com/radiantearth/stac-spec/blob/v0.9.0/item-spec/common-metadata.md)
    title: Optional[str] = Field(None, alias="title")
    description: Optional[str] = Field(None, alias="description")
    start_datetime: Optional[Union[str, dt]] = Field(None, alias="start_datetime")
    end_datetime: Optional[Union[str, dt]] = Field(None, alias="end_datetime")
    platform: Optional[str] = Field(None, alias="platform")
    instruments: Optional[List[str]] = Field(None, alias="instruments")
    constellation: Optional[str] = Field(None, alias="constellation")
    mission: Optional[str] = Field(None, alias="mission")

    class Config:
        extra = "allow"


class Item(Feature):
    """
    https://github.com/radiantearth/stac-spec/blob/v0.9.0/item-spec/item-spec.md
    """

    id: str
    stac_version: str = Field(STAC_VERSION, const=True)
    properties: ItemProperties
    assets: Dict[str, Asset]
    links: List[Link]
    bbox: BBox
    stac_extensions: Optional[List[Union[str, ExtensionTypes]]]
    collection: Optional[str]

    def to_dict(self, **kwargs):
        return self.dict(by_alias=True, exclude_unset=True, **kwargs)

    def to_json(self, **kwargs):
        return self.json(by_alias=True, exclude_unset=True, **kwargs)


class ItemCollection(FeatureCollection):
    """
    https://github.com/radiantearth/stac-spec/blob/v0.9.0/item-spec/itemcollection-spec.md
    """

    stac_version: str = Field(STAC_VERSION, const=True)
    features: List[Item]
    stac_extensions: Optional[List[ExtensionTypes]]
    links: List[Union[PaginationLink, Link]]
    context: Optional[ContextExtension]

    def to_dict(self, **kwargs):
        return self.dict(by_alias=True, exclude_unset=True, **kwargs)

    def to_json(self, **kwargs):
        return self.json(by_alias=True, exclude_unset=True, **kwargs)


@lru_cache
def _extension_model_factory(stac_extensions: Tuple[str]):
    """
    Create a stac item properties model for a set of stac extensions
    """
    fields = {}
    for ext in stac_extensions:
        if ext == "checksum":
            continue
        fields.update(decompose_model(Extensions.get(ext)))
    return (
        create_model("CustomItemProperties", __base__=ItemProperties, **fields),
        FieldInfo(...),
    )


def item_factory(item: Dict) -> Type[BaseModel]:
    item_fields = decompose_model(Item)
    stac_extensions = item.get("stac_extensions")

    if stac_extensions:
        item_fields["properties"] = _extension_model_factory(tuple(stac_extensions))

    return create_model("CustomStacItem", **item_fields, __base__=Item)
