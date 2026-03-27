# ZKH Benchmark 数据集下载使用指南

本文档详细介绍如何使用 ZKH Benchmark 平台的数据集下载功能。

## 功能概述

ZKH Benchmark 提供三种方式下载数据集：

1. **Web 页面下载** - 适合偶尔下载的用户
2. **Python SDK** - 适合程序化集成
3. **CLI 命令行工具** - 适合自动化脚本和批量下载

## 一、Web 页面下载

### 1.1 访问下载页面

1. 登录 ZKH Benchmark 平台
2. 导航到「数据看板」或「数据池」页面
3. 找到需要下载的类目
4. 点击「下载数据集」按钮

### 1.2 选择下载选项

在弹出的下载对话框中，选择以下选项：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| 数据集类型 | 训练集（含GT）或评测集（仅Input） | 训练集 |
| 文件格式 | JSON、CSV 或 Parquet | JSON |
| 版本 | 数据集版本号 | 最新版本 |

### 1.3 下载说明

- **训练集**：包含完整的 `input` 和 `gt` 字段，用于模型训练
- **评测集**：仅包含 `input` 字段，`gt` 被隐藏，用于公平评测
- **小文件**（<100MB）：直接下载，显示进度条
- **大文件**（>100MB）：使用异步导出，生成完成后自动下载

### 1.4 代码示例

```tsx
import { DatasetDownload } from '@/components/DatasetDownload'

// 在页面中使用
function MyPage() {
  return (
    <DatasetDownload 
      category="单承口管箍"
      buttonText="下载数据集"
      buttonType="primary"
    />
  )
}
```

---

## 二、Python SDK

### 2.1 安装

```bash
pip install zkh-benchmark
```

### 2.2 配置认证

#### 方式一：环境变量（推荐）

```bash
export ZKH_API_KEY="your-api-key"
export ZKH_BASE_URL="http://localhost:8000/api/v1"  # 可选，默认生产环境
```

#### 方式二：代码中指定

```python
from zkh_benchmark import Dataset

Dataset.download(
    category="单承口管箍",
    pool_type="training",
    api_key="your-api-key"
)
```

### 2.3 基础下载

#### 下载训练集

```python
from zkh_benchmark import Dataset

# 下载训练集（含GT）
filepath = Dataset.download(
    category="单承口管箍",
    pool_type="training",
    output_dir="./training_data",
    format="json"
)

print(f"Downloaded to: {filepath}")
```

#### 下载评测集

```python
# 下载评测集（仅Input）
filepath = Dataset.download(
    category="球阀",
    pool_type="evaluation",
    output_dir="./eval_data",
    format="parquet"
)
```

### 2.4 大文件下载（异步导出）

对于超过 100MB 的大文件，使用异步导出：

```python
# 异步下载（自动处理大文件）
filepath = Dataset.download_async(
    category="UPVC管",
    pool_type="training",
    output_dir="./large_data",
    format="parquet",
    poll_interval=5  # 每5秒检查一次状态
)
```

### 2.5 批量下载

```python
from zkh_benchmark import Dataset

categories = ["单承口管箍", "球阀", "UPVC管", "铜接头"]

for category in categories:
    print(f"Downloading {category}...")
    
    # 下载训练集
    Dataset.download(
        category=category,
        pool_type="training",
        output_dir="./batch_training"
    )
    
    # 下载评测集
    Dataset.download(
        category=category,
        pool_type="evaluation",
        output_dir="./batch_evaluation"
    )
```

### 2.6 查询数据集信息

```python
from zkh_benchmark import Dataset

# 获取数据集元数据
info = Dataset.info("单承口管箍", "training")

print(f"记录数: {info['record_count']}")
print(f"文件大小: {info['file_size']} bytes")
print(f"可用字段: {info['fields']}")
print(f"最新版本: {info['latest_version']}")

# 列出所有类目
categories = Dataset.list_categories(level=4)
print(f"可用类目: {categories}")
```

### 2.7 使用 Client 直接调用 API

```python
from zkh_benchmark import ZKHBenchmarkClient

# 创建客户端
client = ZKHBenchmarkClient(
    api_key="your-api-key",
    base_url="http://localhost:8000/api/v1"
)

# 查询数据集信息
info = client.get_dataset_info("单承口管箍", "training")

# 列出类目
categories = client.list_categories(level=4)
```

---

## 三、CLI 命令行工具

### 3.1 安装

```bash
pip install zkh-benchmark
```

安装后自动添加 `zkh-benchmark` 命令到 PATH。

### 3.2 配置

```bash
# 设置 API Key
zkh-benchmark config set-api-key your-api-key

# 查看配置
zkh-benchmark config show
```

### 3.3 常用命令

#### 列出可用类目

```bash
# 列出所有四级类目
zkh-benchmark list categories

# 列出二级类目
zkh-benchmark list categories --level 2
```

#### 查看数据集信息

```bash
# 查看训练集信息
zkh-benchmark info --category "单承口管箍" --pool training

# 查看评测集信息
zkh-benchmark info --category "球阀" --pool evaluation

# 查看所有信息
zkh-benchmark info --category "UPVC管" --pool both
```

#### 下载数据集

```bash
# 基础下载
zkh-benchmark download \
  --category "单承口管箍" \
  --pool training \
  --output ./data

# 指定格式和版本
zkh-benchmark download \
  --category "球阀" \
  --pool evaluation \
  --format parquet \
  --version v1.0.0 \
  --output ./eval_data

# 下载大文件（自动使用异步导出）
zkh-benchmark download \
  --category "UPVC管" \
  --pool training \
  --async \
  --output ./large_data
```

#### 批量下载

```bash
# 批量下载多个类目的训练集
zkh-benchmark download-batch \
  单承口管箍 球阀 UPVC管 铜接头 \
  --pool training \
  --format json \
  --output ./training_datasets

# 批量下载所有类目的训练和评测集
zkh-benchmark download-batch \
  单承口管箍 球阀 UPVC管 铜接头 \
  --pool both \
  --format parquet \
  --output ./all_datasets
```

### 3.4 命令参考

```
zkh-benchmark [OPTIONS] COMMAND [ARGS]...

Commands:
  config        Manage configuration
  download      Download a dataset
  download-batch  Download multiple datasets
  info          Show dataset information
  list          List available resources

Options:
  --version     Show version
  --help        Show help
```

---

## 四、数据集格式说明

### 4.1 JSON 格式

#### 训练集结构

```json
{
  "metadata": {
    "category": "单承口管箍",
    "pool_type": "training",
    "version": "v1.0.0",
    "record_count": 10000,
    "fields": ["id", "input", "gt", "category_l1", "category_l2", "category_l3", "category_l4"],
    "generated_at": "2024-03-25T10:30:00Z"
  },
  "data": [
    {
      "id": "dp_abc123",
      "input": "单承口管箍DN350/DN8-CL6000-316L-GB/T14383",
      "gt": {
        "通用名称": "单承口管箍",
        "公称直径(大口)": "DN350",
        "公称直径(小口)": "DN8"
      },
      "category_l1": "建材",
      "category_l2": "管材管件",
      "category_l3": "塑料管材",
      "category_l4": "UPVC管"
    }
  ]
}
```

#### 评测集结构

```json
{
  "metadata": {
    "category": "单承口管箍",
    "pool_type": "evaluation",
    "version": "v1.0.0",
    "record_count": 2000,
    "fields": ["id", "input", "category_l1", "category_l2", "category_l3", "category_l4"],
    "note": "GT字段已移除，用于公平评测"
  },
  "data": [
    {
      "id": "dp_def456",
      "input": "单承口管箍DN350/DN8-CL6000-316L-GB/T14383",
      "category_l1": "建材",
      "category_l2": "管材管件",
      "category_l3": "塑料管材",
      "category_l4": "UPVC管"
    }
  ]
}
```

### 4.2 CSV 格式

```csv
id,input,gt,category_l1,category_l2,category_l3,category_l4
dp_abc123,"单承口管箍DN350...","{""材质"":""UPVC"",""规格"":""DN50""}",建材,管材管件,塑料管材,UPVC管
```

### 4.3 Parquet 格式

- Apache Arrow 列式存储格式
- 高效压缩，适合大数据量
- 与 Pandas/Polars 兼容

```python
import pandas as pd

# 读取 Parquet
df = pd.read_parquet("单承口管箍_training_v1.0.0.parquet")
print(df.head())
```

---

## 五、API 接口说明

### 5.1 获取数据集信息

```http
GET /api/v1/datasets/info?category_l4={category}&pool_type={type}
Authorization: Bearer {token}
```

### 5.2 下载数据集

```http
GET /api/v1/datasets/download?category_l4={category}&pool_type={type}&format={format}
Authorization: Bearer {token}
```

### 5.3 异步导出（大文件）

```http
# 创建导出任务
POST /api/v1/datasets/export
Authorization: Bearer {token}
Content-Type: application/json

{
  "category_l4": "单承口管箍",
  "pool_type": "training",
  "format": "parquet"
}

# 查询任务状态
GET /api/v1/datasets/export/{task_id}/status
Authorization: Bearer {token}

# 下载完成的任务文件
GET /api/v1/datasets/export/{task_id}/download
Authorization: Bearer {token}
```

---

## 六、常见问题

### Q1: 下载速度慢怎么办？

- 检查网络连接
- 对于大文件使用异步导出
- 考虑使用 CLI 工具的批量下载功能

### Q2: 如何获取 API Key？

登录 ZKH Benchmark 平台，在「个人设置」->「API 密钥」页面生成。

### Q3: 支持断点续传吗？

- SDK 和 CLI 支持断点续传
- Web 下载暂不支持（小文件直接下载）

### Q4: 数据集版本如何管理？

- 每次数据更新会自动生成新版本
- 默认下载最新版本
- 可指定历史版本下载

### Q5: 评测集为什么没有 GT？

评测集的 GT 被隐藏是为了公平评测。评测完成后，可提交结果到平台获取评分。

---

## 七、最佳实践

1. **版本控制**：下载时指定版本号，确保实验可复现
2. **本地缓存**：频繁使用的数据集建议本地缓存
3. **批量下载**：使用 CLI 的 `download-batch` 命令批量获取数据
4. **格式选择**：
   - 小数据量：JSON（易读）
   - 大数据量：Parquet（高效）
   - 通用场景：CSV（兼容性好）

---

**文档版本**: v1.0.0  
**更新日期**: 2024-03-25
