import os
import uuid
from pathlib import Path

from dashscope import MultiModalConversation
from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Dataset, Image
from app.schemas import ImageResponse
from app.routers.datasets import image_to_response

router = APIRouter(prefix="/api/ai", tags=["ai"])


def get_existing_categories(db: Session) -> list[str]:  # 获取所有数据集名称
    datasets = db.query(Dataset).all()
    return [ds.name for ds in datasets]


def classify_image(image_path: str, categories: list[str]) -> str | None:   # 调用大模型分类图片
    categories_text = ", ".join(categories) if categories else "create a new category" # 将类别列表转换成, 拼接的字符串

    messages = [
        {
            "role": "user",
            "content": [
                {"image": image_path},  # 传入项目的图片路径, 下面调用MultiModalConversation会自动读取该路径的图片并进行视觉分析
                {"text": f"""图片分类任务。你只能从以下类别中选择一个回复：
{categories_text}

规则：
1. 只回复其中一个类别名称，不要任何其他文字
2. 如果不属于任何类别，回复：__NEW_CATEGORY__"""},
            ]
        }
    ]

    try:
        response = MultiModalConversation.call(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            model=settings.ai.model,
            messages=messages,
            stream=True,
            enable_thinking=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI API error: {str(e)}")

    answer_content = ""

    for chunk in response:
        message = chunk.output.choices[0].message   # 消息对象，包含AI的回复内容
        if message.content:
            answer_content += message.content[0].get("text", "")    # content是一个列表，包含多个内容块,取text键的值

    print(f"[DEBUG] AI raw response: {answer_content}")

    # 用正则表达式清理响应文本，去掉引号、前缀等
    import re
    category_name = answer_content.strip().strip('"\'（）()【】\[\]')
    category_name = re.sub(r'^["\'（）()【】\[\]]+|["\'（）()【】\[\]]+$', '', category_name)
    category_name = category_name.strip()

    # 检查是否包含 __NEW_CATEGORY__ 标记
    if "__NEW_CATEGORY__" in answer_content:
        return "__NEW_CATEGORY__"

    # 精确匹配已有数据集名
    if category_name in categories:
        return category_name

    print(f"[DEBUG] category_name: '{category_name}', categories: {categories}")

    # 如果没有匹配到，返回 None 让调用方处理
    return None


@router.post("/classify-image", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def classify_and_add_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImageResponse:
    categories = get_existing_categories(db)    # 获取所有数据集名称

    if not categories:
        raise HTTPException(
            status_code=400,
            detail="No datasets exist. Please create a dataset first.",
        )

    file_bytes = await file.read()  # 读取上传的图片
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"   # 获取图片扩展名
    filename = f"{uuid.uuid4().hex}{ext}"   # 生成唯一的文件名

    dest_dir = Path(settings.data.path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename  # 图片保存路径

    # 先写入图片到 data/images 目录
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    print(f"[DEBUG] file.extension={ext}, file_size={len(file_bytes)}, saved to={dest_path}")

    # 调用大模型分类图片（使用本地文件路径）
    category = classify_image(str(dest_path), categories)

    if category is None:
        raise HTTPException(
            status_code=400,
            detail="AI did not return a valid category name. Please use an existing dataset name.",
        )

    if category == "__NEW_CATEGORY__":
        raise HTTPException(
            status_code=400,
            detail="Image does not match any existing dataset. Please create a new dataset first.",
        )

    dataset = db.query(Dataset).filter(Dataset.name == category).first()    # 通过名称查询数据集
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{category}' not found")

    db_path = f"data/images/{filename}"
    image = Image(dataset_id=dataset.id, filename=filename, path=db_path)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image_to_response(image)
