# ZKH Benchmark 数据集下载系统 - 使用指南

## 📚 目录

1. [快速开始](#快速开始)
2. [Web页面下载](#web页面下载)
3. [Python SDK使用](#python-sdk使用)
4. [CLI命令行工具](#cli命令行工具)
5. [API接口文档](#api接口文档)
6. [版本控制](#版本控制)
7. [性能优化说明](#性能优化说明)
8. [常见问题](#常见问题)

---

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+ (Web)
- RabbitMQ + Redis (大文件导出)

### 安装

#### 1. Python SDK/CLI 安装

```bash
# 从源码安装
cd sdk/python
pip install -e .

# 或安装到系统
pip install zkh-benchmark
```

#### 2. Web 前端

```bash
cd frontend
npm install
npm run dev
```

#### 3. 后端服务

```bash
cd backend
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload

# 启动Celery Worker（大文件导出需要）
celery -A app.core.celery_app worker --loglevel=info -Q export
celery -A app.core.celery_app beat --loglevel=info
```

---

## Web页面下载

### 1. 打开数据集下载对话框

在类目详情页，点击「下载数据集」按钮打开下载对话框。

### 2. 选择下载参数

| 参数 | 说明 | 选项 |
|------|------|------|
| **数据集类型** | 选择训练集或评测集 | 训练集 / 评测集 / 全部 |
| **文件格式** | 导出文件格式 | JSON / CSV / Parquet |
| **版本** | 数据集版本 | 最新版 / 历史版本 |

### 3. 下载方式

#### 小文件 (< 100MB) - 直接下载
- 选择参数后点击「开始下载」
- 浏览器直接下载，显示实时进度

#### 大文件 (≥ 100MB) - 后台导出
- 系统提示文件较大，建议使用后台导出
- 点击「后台导出」创建导出任务
- 等待任务完成，自动下载

#### Parquet 格式
- 无论文件大小，Parquet 格式自动使用后台导出
- 适合大数据量分析场景

---

## Python SDK使用

### 基础用法

```python
from zkh_benchmark import Dataset

# 1. 下载最新版本（智能选择下载方式）
Dataset.smart_download(
    category="螺丝刀",
    pool_type="training",
    output_dir="./data",
    format="json"
)

# 2. 查看数据集信息
info = Dataset.info("螺丝刀")
print(f"记录数: {info['pools']['training']['record_count']}")
print(f"文件大小: {info['pools']['training']['file_size']}")

# 3. 列出所有版本
versions = Dataset.versions("螺丝刀")
for v in versions:
    print(f"{v['version']} - {v['release_date']}")

# 4. 下载指定历史版本
Dataset.download(
    category="螺丝刀",
    pool_type="training",
    version="v1.0.0",  # 指定历史版本
    format="json"
)
```

### 高级用法

#### 直接下载（小文件）

```python
from zkh_benchmark import Dataset

# 直接下载（< 100MB）
filepath = Dataset.download(
    category="螺丝刀",
    pool_type="training",
    format="json",
    show_progress=True  # 显示进度条
)
```

#### 异步导出（大文件）

```python
from zkh_benchmark import Dataset

# 大文件异步导出（> 100MB）
filepath = Dataset.download_async(
    category="螺丝刀",
    pool_type="training",
    format="parquet",  # Parquet 必须异步导出
    poll_interval=5    # 每5秒查询一次进度
)
```

#### 批量下载

```python
from zkh_benchmark import Dataset

categories = ["螺丝刀", "球阀", "扳手"]

for cat in categories:
    try:
        Dataset.smart_download(
            category=cat,
            pool_type="training",
            format="json"
        )
        print(f"✓ {cat} 下载完成")
    except Exception as e:
        print(f"✗ {cat} 下载失败: {e}")
```

### API客户端高级用法

```python
from zkh_benchmark import ZKHBenchmarkClient

# 创建客户端
client = ZKHBenchmarkClient(
    api_key="your-api-key",
    base_url="http://localhost:8000/api/v1"
)

# 获取数据集信息
info = client.get_dataset_info("螺丝刀", "training")

# 列出类目
categories = client.list_categories(level=4)

# 列出版本
versions = client.list_versions("螺丝刀")
```

---

## CLI命令行工具

### 命令概览

```bash
$ zkh-benchmark --help

Usage: zkh-benchmark [OPTIONS] COMMAND [ARGS]...

  ZKH Benchmark CLI - Download datasets for AI evaluation.

Options:
  --api-key TEXT    API key (or set ZKH_API_KEY env var)
  --base-url TEXT   Base URL for the API
  --version         Show version and exit.
  --help            Show this message and exit.

Commands:
  config           Manage configuration
  download         Download a dataset
  download-batch   Download multiple datasets
  info             Show dataset information
  list             List available resources
  versions         List available versions
```

### 常用命令

#### 1. 配置 API Key

```bash
# 方式1: 使用环境变量
export ZKH_API_KEY="your-api-key"

# 方式2: 保存到配置文件
zkh-benchmark config set-api-key "your-api-key"

# 查看配置
zkh-benchmark config show
```

#### 2. 查看数据集信息

```bash
zkh-benchmark info -c "螺丝刀"
zkh-benchmark info -c "螺丝刀" -p evaluation
```

#### 3. 列出可用类目

```bash
zkh-benchmark list categories
zkh-benchmark list categories -l 3  # 列出3级类目
```

#### 4. 查看版本列表

```bash
zkh-benchmark versions -c "螺丝刀"
```

#### 5. 下载数据集

```bash
# 基础下载（智能选择方式）
zkh-benchmark download -c "螺丝刀"

# 指定参数
zkh-benchmark download -c "螺丝刀" -p training -f json

# 下载评测集
zkh-benchmark download -c "螺丝刀" -p evaluation

# 下载 Parquet 格式（自动异步导出）
zkh-benchmark download -c "螺丝刀" -f parquet

# 下载历史版本
zkh-benchmark download -c "螺丝刀" -v v1.0.0

# 指定输出目录
zkh-benchmark download -c "螺丝刀" -o ./my_data

# 强制使用异步导出
zkh-benchmark download -c "螺丝刀" --async

# 禁用智能检测，强制直接下载
zkh-benchmark download -c "螺丝刀" --no-smart
```

#### 6. 批量下载

```bash
# 下载多个类目的训练集
zkh-benchmark download-batch 螺丝刀 球阀 扳手 -p training

# 下载多个类目的全部数据
zkh-benchmark download-batch 螺丝刀 球阀 --pool both -f json
```

---

## API接口文档

### 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/datasets/info` | 获取数据集元数据 |
| GET | `/api/v1/datasets/versions` | 获取版本列表 |
| GET | `/api/v1/datasets/download` | 直接下载（<100MB）|
| POST | `/api/v1/datasets/export` | 创建导出任务（>100MB）|
| GET | `/api/v1/datasets/export/{task_id}/status` | 查询导出进度 |
| GET | `/api/v1/datasets/export/{task_id}/download` | 下载导出结果 |

### 接口详情

#### 1. 获取数据集信息

**请求**
```http
GET /api/v1/datasets/info?category_l4=螺丝刀&pool_type=both
Authorization: Bearer {token}
```

**响应**
```json
{
  "code": 0,
  "data": {
    "category": "螺丝刀",
    "latest_version": "v1.2.0",
    "versions": ["v1.2.0", "v1.1.0", "v1.0.0"],
    "formats": ["json", "csv", "parquet"],
    "pools": {
      "training": {
        "record_count": 15000,
        "file_size": 52428800,
        "fields": ["id", "input", "gt", "category_l4"],
        "updated_at": "2024-03-25T10:30:00Z"
      },
      "evaluation": {
        "record_count": 1500,
        "file_size": 5242880,
        "fields": ["id", "input", "category_l4"],
        "updated_at": "2024-03-25T10:30:00Z"
      }
    }
  }
}
```

#### 2. 获取版本列表

**请求**
```http
GET /api/v1/datasets/versions?category_l4=螺丝刀
Authorization: Bearer {token}
```

**响应**
```json
{
  "code": 0,
  "data": {
    "category": "螺丝刀",
    "versions": [
      {
        "version": "v1.2.0",
        "release_date": "2024-03-25T10:30:00Z",
        "changelog": "Added 5000 new samples",
        "is_latest": true
      },
      {
        "version": "v1.1.0",
        "release_date": "2024-03-01T08:00:00Z",
        "changelog": "Fixed data quality issues",
        "is_latest": false
      }
    ]
  }
}
```

#### 3. 直接下载（小文件）

**请求**
```http
GET /api/v1/datasets/download?category_l4=螺丝刀&pool_type=training&format=json&version=v1.2.0
Authorization: Bearer {token}
```

**响应** - 流式文件下载

```
Content-Type: application/json
Content-Disposition: attachment; filename=螺丝刀_training_v1.2.0.json
```

#### 4. 创建导出任务（大文件）

**请求**
```http
POST /api/v1/datasets/export
Content-Type: application/json
Authorization: Bearer {token}

{
  "category_l4": "螺丝刀",
  "pool_type": "both",
  "format": "parquet",
  "version": "v1.2.0"
}
```

**响应**
```json
{
  "code": 0,
  "data": {
    "task_id": "export_abc123def456",
    "status": "pending",
    "progress": 0,
    "created_at": "2024-03-25T10:30:00Z"
  }
}
```

#### 5. 查询导出任务状态

**请求**
```http
GET /api/v1/datasets/export/export_abc123def456/status
Authorization: Bearer {token}
```

**响应（进行中）**
```json
{
  "code": 0,
  "data": {
    "task_id": "export_abc123def456",
    "status": "running",
    "progress": 65,
    "estimated_time": 30,
    "download_url": null,
    "expires_at": null,
    "error_message": null
  }
}
```

**响应（完成）**
```json
{
  "code": 0,
  "data": {
    "task_id": "export_abc123def456",
    "status": "completed",
    "progress": 100,
    "file_size": 104857600,
    "download_url": "/api/v1/datasets/export/export_abc123def456/download",
    "expires_at": "2024-04-01T10:30:00Z",
    "error_message": null
  }
}
```

#### 6. 下载导出结果

**请求**
```http
GET /api/v1/datasets/export/export_abc123def456/download
Authorization: Bearer {token}
```

**响应** - 文件下载

---

## 版本控制

### 版本号格式

采用语义化版本控制：`v{major}.{minor}.{patch}`

- **Major**: 重大更新，数据格式变更
- **Minor**: 新增数据，功能增强
- **Patch**: Bug修复，数据修正

### 版本发布流程

1. **数据准备**: 数据工程师确认数据质量
2. **创建版本**: 调用 API 创建新版本
3. **数据快照**: 系统自动导出当前数据
4. **版本标记**: 设置 `is_latest=true`
5. **保留策略**: 默认保留最近5个版本

### 版本回滚

```python
from zkh_benchmark import Dataset

# 下载历史版本
Dataset.download(
    category="螺丝刀",
    pool_type="training",
    version="v1.0.0"  # 指定历史版本
)
```

---

## 性能优化说明

### 下载策略

| 文件大小 | 处理方式 | 技术实现 |
|----------|----------|----------|
| < 100MB | 直接流式下载 | FastAPI StreamingResponse + HTTP流 |
| 100MB - 1GB | 异步生成 + 下载链接 | Celery任务 + 本地文件服务 |
| > 1GB | 不支持 | 提示联系管理员 |

### 性能优化点

1. **流式查询**: 数据库使用 `yield_per()` 分批读取
2. **流式响应**: HTTP 流式传输，边读边写
3. **压缩传输**: Gzip 压缩减少传输时间
4. **Token缓存**: 认证信息缓存5分钟，减少外部调用
5. **文件预生成**: 热点数据可预生成缓存

### 异步导出架构

```
用户请求导出
    ↓
创建 ExportTask (pending)
    ↓
Celery Worker 接收任务
    ↓
流式查询数据库
    ↓
生成文件 (JSON/CSV/Parquet)
    ↓
更新任务状态 (completed)
    ↓
用户提供下载链接 (保留7天)
    ↓
定时清理过期文件
```

---

## 常见问题

### Q: 下载大文件时超时怎么办？

**A**: 使用异步导出功能：

```bash
# CLI
zkh-benchmark download -c "螺丝刀" --async

# Python
Dataset.download_async("螺丝刀", "training")
```

### Q: 如何查看导出任务进度？

**A**: 

```python
from zkh_benchmark import ZKHBenchmarkClient

client = ZKHBenchmarkClient()
status = client.get(f"datasets/export/{task_id}/status")
print(f"进度: {status['data']['progress']}%")
```

### Q: 导出文件保留多久？

**A**: 导出文件默认保留7天，之后自动清理。

### Q: 如何下载历史版本？

**A**:

```bash
# CLI
zkh-benchmark download -c "螺丝刀" -v v1.0.0

# Python
Dataset.download("螺丝刀", "training", version="v1.0.0")
```

### Q: Parquet 格式有什么优势？

**A**: 
- 列式存储，读取速度快
- 自带压缩，文件体积小
- 支持复杂数据类型
- 适合大数据量分析

### Q: 如何批量下载多个类目？

**A**:

```bash
zkh-benchmark download-batch 螺丝刀 球阀 扳手 -p training -f json
```

### Q: API 调用频率有限制吗？

**A**: 
- 下载接口：单用户每秒最多1次请求
- 查询接口：单用户每分钟最多60次请求

### Q: 如何获取 API Key？

**A**: 登录平台后，在「个人设置」-「API密钥」中生成。

---

## 技术支持

如有问题，请联系：
- 技术支持邮箱：support@zkh360.com
- 内部钉钉群：ZKH Benchmark 技术支持
