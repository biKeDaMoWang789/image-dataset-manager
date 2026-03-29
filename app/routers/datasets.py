import base64
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Dataset, Image
from app.schemas import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
    ImageResponse,
)

router = APIRouter(prefix="/api", tags=["datasets"])


def load_image_data(path: str) -> str | None:
    full_path = Path(path)
    if full_path.exists():
        with open(full_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None


def image_to_response(image: Image, include_data: bool = False) -> ImageResponse:
    return ImageResponse(
        id=image.id,
        dataset_id=image.dataset_id,
        filename=image.filename,
        path=image.path,
        created_at=image.created_at,
        image_data=load_image_data(image.path) if include_data else None,
    )


@router.get("/datasets", response_model=list[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)) -> list[Dataset]:
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()  # 查询所有数据集


@router.post("/datasets", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def add_dataset(data: DatasetCreate, db: Session = Depends(get_db)) -> Dataset:
    dataset = Dataset(name=data.name, description=data.description)     # 新增数据集,传名字和描述
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()    # 通过id查询数据集
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.put("/datasets/{dataset_id}", response_model=DatasetResponse)
def modify_dataset(dataset_id: int, data: DatasetUpdate, db: Session = Depends(get_db)) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if data.name is not None:                   # 更新数据集名字
        dataset.name = data.name
    if data.description is not None:
        dataset.description = data.description  # 更新数据集描述
    db.commit()
    db.refresh(dataset)
    return dataset


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_dataset(dataset_id: int, db: Session = Depends(get_db)) -> None:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(dataset)          # 删除给定id的数据集
    db.commit()


@router.get("/datasets/{dataset_id}/images", response_model=list[ImageResponse])
def list_images(dataset_id: int, db: Session = Depends(get_db)) -> list[ImageResponse]:
    if not db.query(Dataset).filter(Dataset.id == dataset_id).first():
        raise HTTPException(status_code=404, detail="Dataset not found")
    images = db.query(Image).filter(Image.dataset_id == dataset_id).order_by(Image.created_at.desc()).all() # 查询给定数据集下的所有图片
    return [image_to_response(img) for img in images]   # 遍历图片列表，将图片转换成响应对象


@router.post("/datasets/{dataset_id}/images", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def add_image(dataset_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)) -> ImageResponse:
    if not db.query(Dataset).filter(Dataset.id == dataset_id).first():
        raise HTTPException(status_code=404, detail="Dataset not found")

    dest_dir = Path(settings.data.path) # 服务器图片保存目录
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ".jpg"   # 图片扩展名
    filename = f"{uuid.uuid4().hex}{ext}"   # 生成uuid/扩展名
    dest_path = dest_dir / filename # 类似Path("data/images/a3f2c8e1d9b4f7a6c2e8d1f9b3a7c5e2.jpg")

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)            # 写入服务器创建好的文件

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

    file_path = Path.cwd() / image.path     # 图片的绝对路径
    if file_path.exists():
        file_path.unlink()                  # 从服务器上删除图片

    db.delete(image)    # 根据id删除图片了
    db.commit()
