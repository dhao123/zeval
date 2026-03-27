# ZKH Benchmark 数据集下载系统

## 项目概述

为 ZKH Benchmark 评测平台构建的完整数据集下载解决方案，支持 Web 页面、Python SDK、CLI 工具三种使用方式，最大支持 1GB 文件下载，具备版本控制功能。

## 功能特性

### 核心功能
- ✅ 多格式支持：JSON（必支持）、CSV、Parquet
- ✅ 大文件支持：最大 1GB，智能选择下载方式
- ✅ 版本控制：支持历史版本下载和版本管理
- ✅ 权限控制：登录用户即可下载

### 三种使用方式

| 方式 | 适用场景 | 特点 |
|------|----------|------|
| **Web页面** | 浏览器直接下载 | 可视化操作，实时进度显示 |
| **Python SDK** | 程序化下载 | 流式下载，智能检测，易于集成 |
| **CLI工具** | 命令行操作 | Huggingface 风格，批量下载 |

## 技术架构

```
┌───────────────────────────────────────────────────────────────┐
│                        用户接口层                              │
├──────────────┬────────────────────┬───────────────────────────┤
│   Web页面     │   Python SDK        │     CLI工具              │
│  (React)     │  (zkh_benchmark)    │  (zkh-benchmark)         │
└──────┬───────┴──────────┬──────────┴──────────┬───────────────┘
       │                  │                     │
       └──────────────────┼─────────────────────┘
                          │ HTTP/HTTPS
                          ▼
┌───────────────────────────────────────────────────────────────┐
│                      FastAPI 后端                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ /datasets/* │  │ /download   │  │ /export (异步)       │   │
│  │  元数据查询  │  │ 直接下载     │  │ 大文件生成任务        │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
└───────────────────────────┬───────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
┌──────────────┐    ┌──────────────┐   ┌──────────────┐
│   SQLite     │    │   本地存储    │   │  Celery      │
│  (版本信息)   │    │ (<100MB缓存) │   │  Worker      │
└──────────────┘    └──────────────┘   └──────────────┘
```

## 下载策略

| 文件大小 | 处理方式 | 响应时间 |
|----------|----------|----------|
| < 100MB | 直接流式下载 | < 30s |
| 100MB - 1GB | 异步生成 + 下载链接 | 1-10min |
| > 1GB | 不支持 | N/A |

## 快速开始

### 1. Web 页面下载

```bash
# 启动前端
cd frontend
npm install
npm run dev

# 访问 http://localhost:5173
# 点击「下载数据集」按钮即可
```

### 2. Python SDK

```bash
# 安装 SDK
cd sdk/python
pip install -e .

# 使用示例
python -c "
from zkh_benchmark import Dataset
Dataset.smart_download('螺丝刀', 'training')
"
```

### 3. CLI 工具

```bash
# 安装后自动可用
zkh-benchmark --help

# 下载数据集
zkh-benchmark download -c "螺丝刀" -p training -f json

# 查看版本
zkh-benchmark versions -c "螺丝刀"

# 批量下载
zkh-benchmark download-batch 螺丝刀 球阀 扳手
```

## 项目结构

```
zeval/
├── backend/
│   ├── app/
│   │   ├── api/v1/datasets.py      # 下载 API 端点
│   │   ├── services/dataset_service.py  # 数据集服务
│   │   ├── models/dataset_export.py     # 版本/任务模型
│   │   ├── tasks/export_tasks.py        # Celery 导出任务
│   │   └── core/celery_app.py           # Celery 配置
│   └── requirements.txt
├── frontend/
│   └── src/components/DatasetDownload/  # Web 下载组件
├── sdk/python/
│   ├── zkh_benchmark/
│   │   ├── dataset.py    # Dataset 类
│   │   ├── client.py     # API 客户端
│   │   └── cli.py        # 命令行工具
│   └── setup.py
└── docs/
    ├── DATASET_DOWNLOAD_SPEC.md   # 技术规格书
    └── DATASET_DOWNLOAD_GUIDE.md  # 使用指南
```

## 核心功能实现

### 1. 智能下载 (Python SDK)

```python
from zkh_benchmark import Dataset

# 自动检测文件大小，选择最佳下载方式
Dataset.smart_download(
    category="螺丝刀",
    pool_type="training",
    format="json"
)
```

### 2. 异步导出 (大文件)

```python
# 创建导出任务，后台生成
Dataset.download_async(
    category="螺丝刀",
    pool_type="both",
    format="parquet"
)
```

### 3. 版本控制

```bash
# 查看所有版本
zkh-benchmark versions -c "螺丝刀"

# 下载历史版本
zkh-benchmark download -c "螺丝刀" -v v1.0.0
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/datasets/info` | GET | 获取数据集元数据 |
| `/datasets/versions` | GET | 获取版本列表 |
| `/datasets/download` | GET | 直接下载（<100MB）|
| `/datasets/export` | POST | 创建导出任务 |
| `/datasets/export/{id}/status` | GET | 查询导出进度 |
| `/datasets/export/{id}/download` | GET | 下载导出结果 |

## 性能优化

1. **流式查询**: 数据库 `yield_per()` 分批读取
2. **流式响应**: HTTP 流式传输，边读边写
3. **Token缓存**: 认证信息缓存5分钟
4. **文件预生成**: 热点数据可预生成
5. **Gzip压缩**: 减少传输体积

## 文档

- [技术规格书](DATASET_DOWNLOAD_SPEC.md) - 详细架构设计
- [使用指南](DATASET_DOWNLOAD_GUIDE.md) - 完整使用说明

## 开发团队

ZKH AI 团队

---

**版本**: 2.0.0  
**最后更新**: 2024-03-25
