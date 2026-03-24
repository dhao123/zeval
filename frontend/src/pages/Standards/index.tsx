import { Card, Table, Button, Input, Space, Tag, Upload } from 'antd'
import { UploadOutlined, FileTextOutlined } from '@ant-design/icons'

const columns = [
  {
    title: '国标编号',
    dataIndex: 'standard_id',
    key: 'standard_id',
  },
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: string) => {
      const colorMap: Record<string, string> = {
        uploaded: 'blue',
        parsed: 'orange',
        active: 'green',
      }
      const labelMap: Record<string, string> = {
        uploaded: '已上传',
        parsed: '已解析',
        active: '已激活',
      }
      return <Tag color={colorMap[status]}>{labelMap[status]}</Tag>
    },
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
      <Space>
        <a>查看</a>
        <a>解析</a>
        <a>删除</a>
      </Space>
    ),
  },
]

const mockData = [
  {
    id: 1,
    standard_id: 'std_001',
    name: 'GB/T 4219.1',
    status: 'active',
    created_at: '2024-01-15 10:30:00',
  },
  {
    id: 2,
    standard_id: 'std_002',
    name: 'GB/T 5836.1',
    status: 'parsed',
    created_at: '2024-01-15 11:00:00',
  },
]

function Standards() {
  return (
    <div>
      <div className="page-header">
        <h2>国标管理</h2>
        <p className="subtitle">管理国标文件，支持PDF/Word/TXT格式</p>
      </div>

      <Card>
        <div className="table-actions">
          <Input.Search
            placeholder="搜索国标"
            style={{ width: 300 }}
            allowClear
          />
          <Space>
            <Upload accept=".pdf,.doc,.docx,.txt" showUploadList={false}>
              <Button icon={<UploadOutlined />}>上传国标</Button>
            </Upload>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={mockData}
          rowKey="id"
        />
      </Card>
    </div>
  )
}

export default Standards
