from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImageBase(BaseModel):
    filename: str
    path: str


class ImageCreate(BaseModel):
    source_path: str


class ImageResponse(ImageBase):
    id: int
    dataset_id: int
    created_at: datetime
    image_data: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DatasetBase(BaseModel):
    name: str
    description: str = ""


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DatasetResponse(DatasetBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetWithImages(DatasetResponse):
    images: list[ImageResponse] = []
