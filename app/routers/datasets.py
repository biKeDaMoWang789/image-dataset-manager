import base64
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Dataset, Image
from app.schemas import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
    DatasetWithImages,
    ImageCreate,
    ImageResponse,
)

router = APIRouter(prefix="/api", tags=["datasets"])


def load_image_data(path: str) -> str | None:
    if Path(path).is_absolute():
        full_path = Path(path)
    else:
        full_path = Path.cwd() / path
    if full_path.exists():
        with open(full_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None


def image_to_response(image: Image) -> ImageResponse:
    return ImageResponse(
        id=image.id,
        dataset_id=image.dataset_id,
        filename=image.filename,
        path=image.path,
        created_at=image.created_at,
        image_data=load_image_data(image.path),
    )


@router.get("/datasets", response_model=list[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)) -> list[Dataset]:
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


@router.post("/datasets", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def add_dataset(data: DatasetCreate, db: Session = Depends(get_db)) -> Dataset:
    dataset = Dataset(name=data.name, description=data.description)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.put("/datasets/{dataset_id}", response_model=DatasetResponse)
def modify_dataset(dataset_id: int, data: DatasetUpdate, db: Session = Depends(get_db)) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if data.name is not None:
        dataset.name = data.name
    if data.description is not None:
        dataset.description = data.description
    db.commit()
    db.refresh(dataset)
    return dataset


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_dataset(dataset_id: int, db: Session = Depends(get_db)) -> None:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(dataset)
    db.commit()


@router.get("/datasets/{dataset_id}/images", response_model=list[ImageResponse])
def list_images(dataset_id: int, db: Session = Depends(get_db)) -> list[ImageResponse]:
    if not db.query(Dataset).filter(Dataset.id == dataset_id).first():
        raise HTTPException(status_code=404, detail="Dataset not found")
    images = db.query(Image).filter(Image.dataset_id == dataset_id).order_by(Image.created_at.desc()).all()
    return [image_to_response(img) for img in images]


@router.post("/datasets/{dataset_id}/images", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
def add_image(dataset_id: int, data: ImageCreate, db: Session = Depends(get_db)) -> ImageResponse:
    if not db.query(Dataset).filter(Dataset.id == dataset_id).first():
        raise HTTPException(status_code=404, detail="Dataset not found")

    source_path = Path(data.source_path)
    if not source_path.exists():
        raise HTTPException(status_code=400, detail="Source file not found")

    filename = source_path.name
    dest_dir = Path(settings.data.path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    shutil.copy2(source_path, dest_path)

    db_path = f"data/images/{filename}"
    image = Image(dataset_id=dataset_id, filename=filename, path=db_path)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image_to_response(image)


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_image(image_id: int, db: Session = Depends(get_db)) -> None:
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = Path(image.path)
    if not file_path.is_absolute():
        file_path = Path.cwd() / image.path
    if file_path.exists():
        file_path.unlink()

    db.delete(image)
    db.commit()
