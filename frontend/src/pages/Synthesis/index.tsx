import { Card, Table, Button, Select, InputNumber, Form, Switch, Progress, Tag } from 'antd'
import { PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons'

const columns = [
  {
    title: '任务ID',
    dataIndex: 'task_id',
    key: 'task_id',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: string) => {
      const colorMap: Record<string, string> = {
        pending: 'default',
        running: 'processing',
        completed: 'success',
        failed: 'error',
      }
      const labelMap: Record<string, string> = {
        pending: '等待中',
        running: '运行中',
        completed: '已完成',
        failed: '失败',
      }
      return <Tag color={colorMap[status]}>{labelMap[status]}</Tag>
    },
  },
  {
    title: '进度',
    dataIndex: 'progress',
    key: 'progress',
    render: (progress: number, record: any) => (
      record.status === 'running' ? (
        <Progress percent={progress} size="small" />
      ) : (
        `${progress}%`
      )
    ),
  },
  {
    title: '难度',
    dataIndex: 'difficulty',
    key: 'difficulty',
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
      <Button size="small" icon={<PauseCircleOutlined />}>取消</Button>
    ),
  },
]

const mockData = [
  {
    id: 1,
    task_id: 'task_001',
    status: 'running',
    progress: 65,
    difficulty: 'medium',
    created_at: '2024-01-15 10:30:00',
  },
]

function Synthesis() {
  return (
    <div>
      <div className="page-header">
        <h2>数据合成</h2>
        <p className="subtitle">基于种子数据和规则进行AI数据合成</p>
      </div>

      <Card title="创建合成任务" style={{ marginBottom: 24 }}>
        <Form layout="inline">
          <Form.Item label="难度等级">
            <Select defaultValue="medium" style={{ width: 120 }}>
              <Select.Option value="low">低</Select.Option>
              <Select.Option value="medium">中</Select.Option>
              <Select.Option value="high">高</Select.Option>
              <Select.Option value="ultra">超高</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="每个种子生成数量">
            <InputNumber defaultValue={5} min={1} max={20} />
          </Form.Item>
          <Form.Item label="AI质检">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<PlayCircleOutlined />}>
              开始合成
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="合成任务列表">
        <Table
          columns={columns}
          dataSource={mockData}
          rowKey="id"
        />
      </Card>
    </div>
  )
}

export default Synthesis
