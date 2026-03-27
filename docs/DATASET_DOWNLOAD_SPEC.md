# ZKH Benchmark 数据集下载系统 - 技术规格书

## 1. 需求分析

### 1.1 功能需求
| 需求项 | 具体要求 |
|--------|----------|
| 文件格式 | JSON（必支持）、CSV、Parquet（可选） |
| 文件大小 | 最大支持 1GB |
| 版本控制 | 支持版本号管理和历史版本下载 |
| 权限控制 | 登录用户即可下载 |

### 1.2 实现方式
| 方式 | 说明 |
|------|------|
| Web页面 | 浏览器直接下载，支持大文件流式传输 |
| API/SDK | HTTP接口封装，提供Python SDK |
| CLI工具 | 仿Huggingface风格，安装后命令行可用 |

## 2. 技术架构

### 2.1 架构图
```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
├──────────────┬──────────────────┬───────────────────────────┤
│   Web页面     │   Python SDK      │     CLI工具              │
│  (React)     │  (zkh_benchmark)  │  (zkh-benchmark)         │
└──────┬───────┴────────┬─────────┴────────────┬──────────────┘
       │                │                      │
       └────────────────┴──────────────────────┘
                          │
                    HTTP/HTTPS
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                    网关层 (Nginx)                          │
│         静态文件服务 / 反向代理 / 大文件流式传输            │
└─────────────────────────┼─────────────────────────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                   FastAPI后端                              │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐ │
│  │ /datasets/* │  │ /download   │  │ /export (异步)      │ │
│  │ 元数据查询   │  │ 直接下载     │  │ 大文件生成任务       │ │
│  └─────────────┘  └─────────────┘  └────────────────────┘ │
└─────────────────────────┬─────────────────────────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
┌────────────┐    ┌──────────────┐   ┌──────────────┐
│   SQLite   │    │   本地存储    │   │  MinIO/S3    │
│ (版本信息)  │    │ (<100MB缓存) │   │  (>100MB)    │
└────────────┘    └──────────────┘   └──────────────┘
```

### 2.2 下载策略

| 文件大小 | 处理方式 | 技术实现 |
|----------|----------|----------|
| < 100MB | 直接流式下载 | FastAPI StreamingResponse |
| 100MB - 1GB | 异步生成 + 下载链接 | Celery任务 + 预签名URL |
| > 1GB | 分片下载 | 不支持，提示联系管理员 |

### 2.3 版本控制设计

```python
# 版本号格式: v{major}.{minor}.{patch}
# 示例: v1.0.0, v1.1.0, v2.0.0

版本发布流程:
1. 数据工程师确认数据质量
2. 生成版本快照（导出当前数据）
3. 更新 version 表
4. 设置 is_latest=true

历史版本保留:
- 默认保留最近5个版本
- 支持归档到冷存储
```

## 3. API设计

### 3.1 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/datasets/info` | 获取数据集元数据 |
| GET | `/api/v1/datasets/versions` | 获取版本列表 |
| GET | `/api/v1/datasets/download` | 直接下载（<100MB）|
| POST | `/api/v1/datasets/export` | 创建导出任务（>100MB）|
| GET | `/api/v1/datasets/export/{task_id}/status` | 查询导出进度 |
| GET | `/api/v1/datasets/export/{task_id}/download` | 下载导出结果 |

### 3.2 请求/响应示例

**获取数据集信息**
```http
GET /api/v1/datasets/info?category_l4=螺丝刀&pool_type=training

Response:
{
  "code": 0,
  "data": {
    "category_l4": "螺丝刀",
    "pool_type": "training",
    "version": "v1.2.0",
    "record_count": 15000,
    "file_size": 52428800,  // 50MB
    "formats": ["json", "csv", "parquet"],
    "updated_at": "2024-03-25T10:30:00Z"
  }
}
```

**创建导出任务（大文件）**
```http
POST /api/v1/datasets/export
Content-Type: application/json

{
  "category_l4": "螺丝刀",
  "pool_type": "both",
  "format": "parquet",
  "version": "v1.2.0"
}

Response:
{
  "code": 0,
  "data": {
    "task_id": "export_abc123",
    "status": "pending",
    "estimated_time": 120  // seconds
  }
}
```

## 4. SDK设计

### 4.1 使用示例

```python
from zkh_benchmark import Dataset

# 简单下载（自动处理大小）
Dataset.download(
    category="螺丝刀",
    pool_type="training",
    format="json",
    output_dir="./data"
)

# 指定版本下载
Dataset.download(
    category="螺丝刀",
    pool_type="both",
    format="parquet",
    version="v1.0.0",  # 历史版本
    output_dir="./data"
)

# 查看数据集信息
info = Dataset.info("螺丝刀")
print(f"Records: {info.record_count}")
print(f"Latest version: {info.version}")

# 列出所有版本
versions = Dataset.versions("螺丝刀")
for v in versions:
    print(f"{v.version}: {v.release_date}")
```

## 5. CLI设计

### 5.1 命令结构（仿Huggingface）

```bash
# 查看帮助
zkh-benchmark --help

# 下载数据集
zkh-benchmark download 螺丝刀 --pool training --format json

# 指定版本
zkh-benchmark download 螺丝刀 --pool both --format parquet --version v1.0.0

# 查看数据集信息
zkh-benchmark info 螺丝刀

# 查看版本列表
zkh-benchmark versions 螺丝刀

# 列出所有可用数据集
zkh-benchmark list

# 登录（配置API Key）
zkh-benchmark login

# 登出
zkh-benchmark logout
```

## 6. 性能优化策略

### 6.1 数据库查询优化
- 流式查询：使用 `yield_per()` 分批读取
- 索引优化：`category_l4`, `pool_type`, `created_at`

### 6.2 文件生成优化
- CSV/JSON：流式写入，边读边写
- Parquet：使用 PyArrow 批量写入

### 6.3 下载优化
- 流式响应：StreamingResponse
- 压缩：Gzip 压缩减少传输
- 缓存：热点数据预生成

### 6.4 异步任务（Celery）
```
大文件导出流程:
1. 用户 POST /export 创建任务
2. 返回 task_id
3. Celery Worker 异步生成文件
4. 用户轮询 GET /export/{task_id}/status
5. 完成后返回下载链接
6. 文件保留7天后自动删除
```

## 7. 安全设计

- 所有接口需要登录（JWT Token）
- 下载链接使用预签名URL（限时15分钟）
- 操作审计日志记录
- 频率限制：单用户每秒最多1次下载请求

## 8. 实现计划

### Phase 1: 后端API优化（2h）
- [x] 修复模型冲突
- [x] 添加Token缓存
- [ ] 实现版本控制完整逻辑
- [ ] 大文件异步导出（Celery）

### Phase 2: Web组件完善（1h）
- [ ] 流式下载进度显示
- [ ] 大文件导出等待页面

### Phase 3: SDK完善（1h）
- [ ] 流式下载优化
- [ ] 断点续传支持

### Phase 4: CLI完善（1h）
- [ ] Huggingface风格命令
- [ ] 进度条显示

### Phase 5: 文档编写（1h）
- [ ] 技术文档
- [ ] 使用手册
