# 图片数据集管理系统 SPEC

## 1. 项目概述

- **项目名称**: image-dataset-manager
- **项目类型**: REST API 后端服务
- **核心功能**: 管理图片数据集的增删改查，每个数据集包含多张图片
- **目标用户**: 开发者、数据标注人员

## 2. 技术栈

| 组件 | 工具 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | API 开发 |
| ORM | SQLAlchemy 2.0 | 数据库操作 |
| 配置管理 | PyYAML + Pydantic Settings | 配置文件加载 |
| 数据库 | SQLite | 轻量级文件数据库 |
| 代码质量 | Ruff | 格式化与检查 |
| 静态检查 | MyPy | 类型检查 |
| 接口调试 | Apifox | API 调试工具 |

## 3. 数据模型

### Dataset (数据集)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | str | 数据集名称 |
| description | str | 描述 |
| created_at | datetime | 创建时间 |

### Image (图片)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| dataset_id | int | 外键，关联数据集 |
| filename | str | 文件名 |
| path | str | 文件路径 |
| created_at | datetime | 创建时间 |

## 4. API 接口

### 数据集管理
- `GET /api/datasets` - 获取所有数据集
- `POST /api/datasets` - 创建数据集
- `GET /api/datasets/{id}` - 获取单个数据集
- `PUT /api/datasets/{id}` - 更新数据集
- `DELETE /api/datasets/{id}` - 删除数据集

### 图片管理
- `GET /api/datasets/{id}/images` - 获取数据集下的所有图片
- `POST /api/datasets/{id}/images` - 添加图片到数据集
- `DELETE /api/images/{id}` - 删除图片

### AI 智能分类
- `POST /api/ai/classify-image` - 调用大模型自动判断图片类别并添加到对应数据集

## 5. 项目结构

```
image-dataset-manager/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 入口
│   ├── base.py          # SQLAlchemy Base
│   ├── config.py        # 配置管理
│   ├── models.py        # SQLAlchemy ORM 模型
│   ├── schemas.py       # Pydantic V2  schemas
│   ├── database.py      # SQLAlchemy 数据库配置
│   └── routers/
│       ├── __init__.py
│       ├── datasets.py  # 数据集路由
│       └── ai.py        # AI 智能分类路由
├── data/                # 数据存储目录
├── config.yaml          # 配置文件
├── pyproject.toml
└── README.md
```

## 6. 初始数据

系统初始化时创建 3 个示例数据集，每个数据集包含 3 张示例图片。

## 7. 配置说明

配置文件 `config.yaml` 包含:
- `database.path`: SQLite 数据库文件路径
- `data.path`: 图片存储目录路径
- `app.host`: 服务主机
- `app.port`: 服务端口
- `ai.base_url`: AI API 地址
- `ai.api_key`: AI API 密钥
- `ai.model`: AI 模型名称
