import { useState } from 'react'
import { Card, Table, Button, Input, Select, Space, Tag, Upload, message } from 'antd'
import { UploadOutlined, PlusOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

interface SeedData {
  id: number
  seed_id: string
  input: string
  category_l4: string
  status: string
  created_at: string
}

const columns: ColumnsType<SeedData> = [
  {
    title: 'ID',
    dataIndex: 'seed_id',
    key: 'seed_id',
  },
  {
    title: '输入',
    dataIndex: 'input',
    key: 'input',
    ellipsis: true,
  },
  {
    title: '类目',
    dataIndex: 'category_l4',
    key: 'category_l4',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: string) => (
      <Tag color={status === 'official' ? 'green' : 'orange'}>
        {status === 'official' ? '正式' : '草稿'}
      </Tag>
    ),
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
  },
  {
    title: '操作',
    key: 'action',
    render: () => (
      <Space size="middle">
        <a>查看</a>
        <a>编辑</a>
        <a>确认</a>
      </Space>
    ),
  },
]

const mockData: SeedData[] = [
  {
    id: 1,
    seed_id: 'seed_001',
    input: 'UPVC管 DN20 PN2.5',
    category_l4: '管材',
    status: 'official',
    created_at: '2024-01-15 10:30:00',
  },
  {
    id: 2,
    seed_id: 'seed_002',
    input: '镀锌钢管 DN50',
    category_l4: '管材',
    status: 'draft',
    created_at: '2024-01-15 11:00:00',
  },
]

function Seeds() {
  const [loading, setLoading] = useState(false)

  const handleUpload = (info: any) => {
    if (info.file.status === 'done') {
      message.success(`${info.file.name} 上传成功`)
    } else if (info.file.status === 'error') {
      message.error(`${info.file.name} 上传失败`)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>种子管理</h2>
        <p className="subtitle">管理种子数据，支持批量上传</p>
      </div>

      <Card>
        <div className="table-actions">
          <Space>
            <Input.Search
              placeholder="搜索种子"
              style={{ width: 300 }}
              allowClear
            />
            <Select
              placeholder="状态"
              style={{ width: 120 }}
              allowClear
              options={[
                { label: '草稿', value: 'draft' },
                { label: '正式', value: 'official' },
              ]}
            />
            <Select
              placeholder="类目"
              style={{ width: 150 }}
              allowClear
              options={[
                { label: '管材', value: '管材' },
                { label: '阀门', value: '阀门' },
              ]}
            />
          </Space>
          <Space>
            <Upload
              accept=".xlsx,.xls,.csv"
              showUploadList={false}
              customRequest={handleUpload}
            >
              <Button icon={<UploadOutlined />}>批量上传</Button>
            </Upload>
            <Button type="primary" icon={<PlusOutlined />}>
              新增种子
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={mockData}
          loading={loading}
          rowKey="id"
          pagination={{
            total: 100,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>
    </div>
  )
}

export default Seeds
