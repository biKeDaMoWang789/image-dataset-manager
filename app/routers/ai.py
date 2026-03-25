import base64
from pathlib import Path

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Dataset, Image
from app.schemas import ImageResponse
from app.routers.datasets import image_to_response

router = APIRouter(prefix="/api/ai", tags=["ai"])


def get_existing_categories(db: Session) -> list[str]:
    datasets = db.query(Dataset).all()
    return [ds.name for ds in datasets]


def classify_image(image_path: str, categories: list[str]) -> str | None:
    full_path = Path(image_path)
    if not full_path.is_absolute():
        full_path = Path.cwd() / image_path

    if not full_path.exists():
        raise HTTPException(status_code=400, detail="Image file not found")

    with open(full_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    client = anthropic.Anthropic(
        base_url=settings.ai.base_url,
        api_key=settings.ai.api_key,
    )

    categories_text = ", ".join(categories) if categories else "create a new category"

    try:
        message = client.messages.create(
            model=settings.ai.model,
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"""分析这张图片，判断它属于哪个类别。
已有类别: {categories_text}
请只返回一个类别名称，不要其他文字。如果图片不属于任何已有类别，请返回"__NEW_CATEGORY__"。""",
                        },
                    ],
                }
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI API error: {str(e)}")

    # Skip thinking blocks and find the text result
    result = None
    content_types = [b.type for b in message.content]
    thinking_content = None
    for block in message.content:
        if block.type == "text":
            result = block.text.strip()
            break
        elif block.type == "thinking":
            # Thinking blocks have 'thinking' attribute
            thinking_content = getattr(block, "thinking", None)

    if result is None:
        raise HTTPException(
            status_code=500,
            detail=f"AI returned no text result. Content types: {content_types}, thinking: {thinking_content[:200] if thinking_content else None}",
        )

    return result


@router.post("/classify-image", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
def classify_and_add_image(
    source_path: str,
    db: Session = Depends(get_db),
) -> ImageResponse:
    categories = get_existing_categories(db)

    if not categories:
        raise HTTPException(
            status_code=400,
            detail="No datasets exist. Please create a dataset first.",
        )

    category = classify_image(source_path, categories)

    if category == "__NEW_CATEGORY__":
        raise HTTPException(
            status_code=400,
            detail="Image does not match any existing dataset. Please create a new dataset first.",
        )

    dataset = db.query(Dataset).filter(Dataset.name == category).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{category}' not found")

    full_path = Path(source_path)
    if not full_path.is_absolute():
        full_path = Path.cwd() / source_path

    filename = full_path.name
    dest_dir = Path(settings.data.path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    import shutil
    shutil.copy2(full_path, dest_path)

    db_path = f"data/images/{filename}"
    image = Image(dataset_id=dataset.id, filename=filename, path=db_path)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image_to_response(image)
