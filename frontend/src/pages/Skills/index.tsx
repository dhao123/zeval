import { Card, Table, Button, Input, Space, Tag, Drawer, Form, Input as AntInput } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useState } from 'react'

const columns = [
  {
    title: '规则ID',
    dataIndex: 'skill_id',
    key: 'skill_id',
  },
  {
    title: '规则名称',
    dataIndex: 'skill_name',
    key: 'skill_name',
  },
  {
    title: '类目',
    dataIndex: 'category_l4',
    key: 'category_l4',
  },
  {
    title: '关联国标',
    dataIndex: 'standard_id',
    key: 'standard_id',
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
    title: '操作',
    key: 'action',
    render: () => (
      <Space>
        <a><EditOutlined /> 编辑</a>
      </Space>
    ),
  },
]

const mockData = [
  {
    id: 1,
    skill_id: 'skill_001',
    skill_name: '管材规格提取规则',
    category_l4: '管材',
    standard_id: 'std_001',
    status: 'official',
  },
]

function Skills() {
  const [drawerVisible, setDrawerVisible] = useState(false)

  return (
    <div>
      <div className="page-header">
        <h2>规则管理</h2>
        <p className="subtitle">管理Skills/规则，支持从国标自动生成</p>
      </div>

      <Card>
        <div className="table-actions">
          <Input.Search
            placeholder="搜索规则"
            style={{ width: 300 }}
            allowClear
          />
          <Space>
            <Button>从国标生成</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setDrawerVisible(true)}>
              新增规则
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={mockData}
          rowKey="id"
        />
      </Card>

      <Drawer
        title="编辑规则"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        <Form layout="vertical">
          <Form.Item label="规则名称" required>
            <AntInput />
          </Form.Item>
          <Form.Item label="类目" required>
            <AntInput />
          </Form.Item>
          <Form.Item label="规则定义 (JSON)">
            <AntInput.TextArea rows={10} />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

export default Skills
