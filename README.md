# 图片数据集管理系统

基于 FastAPI 的轻量级图片数据集管理 API。

## 技术栈

| 组件 | 工具 |
|------|------|
| Web 框架 | FastAPI |
| 配置管理 | PyYAML + Pydantic Settings |
| 数据库 | SQLite |
| 代码质量 | Ruff |
| 静态检查 | MyPy |

## 快速启动

```bash
# 安装依赖
uv sync

# 启动服务
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API 接口

服务启动后访问 `http://localhost:8000/docs` 查看 Swagger 文档。

### 数据集管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/datasets` | 获取所有数据集 |
| POST | `/api/datasets` | 创建数据集 |
| GET | `/api/datasets/{id}` | 获取单个数据集（含图片） |
| PUT | `/api/datasets/{id}` | 更新数据集 |
| DELETE | `/api/datasets/{id}` | 删除数据集 |

### 图片管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/datasets/{id}/images` | 获取数据集下的所有图片 |
| POST | `/api/datasets/{id}/images` | 添加图片到数据集 |
| DELETE | `/api/images/{id}` | 删除图片 |

## Apifox 使用

1. 启动服务
2. 在 Apifox 中新建项目，添加 Base URL: `http://localhost:8000`
3. 导入或手动添加上述 API 接口
4. 使用 Apifox 发送请求测试

## 开发

```bash
# 代码检查
uv run ruff check .

# 代码格式化
uv run ruff format .

# 类型检查
uv run mypy app/
```
