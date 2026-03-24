import { Card, Table, Button, Input, Select, Space, Tag, Steps, Form, Modal } from 'antd'
import { PlusOutlined, EyeOutlined } from '@ant-design/icons'
import { useState } from 'react'

const { Step } = Steps

const columns = [
  {
    title: '评测ID',
    dataIndex: 'eval_id',
    key: 'eval_id',
  },
  {
    title: '评测名称',
    dataIndex: 'eval_name',
    key: 'eval_name',
  },
  {
    title: '模型版本',
    dataIndex: 'model_version',
    key: 'model_version',
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
    title: '得分',
    dataIndex: 'score',
    key: 'score',
    render: (score: number) => score ? `${(score * 100).toFixed(2)}%` : '-',
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
        <a><EyeOutlined /> 查看</a>
        <a>重新评测</a>
      </Space>
    ),
  },
]

const mockData = [
  {
    id: 1,
    eval_id: 'eval_001',
    eval_name: 'GPT-4o 评测 v1',
    model_version: 'gpt-4o-2024-01',
    status: 'completed',
    score: 0.8567,
    created_at: '2024-01-15 10:30:00',
  },
]

function Evaluation() {
  const [modalVisible, setModalVisible] = useState(false)

  return (
    <div>
      <div className="page-header">
        <h2>评测任务</h2>
        <p className="subtitle">创建评测任务，上传结果文件，获取自动评分</p>
      </div>

      <Card title="评测流程" style={{ marginBottom: 24 }}>
        <Steps current={0}>
          <Step title="下载评测集" description="仅Input，无GT" />
          <Step title="本地推理" description="执行模型推理" />
          <Step title="上传结果" description="上传prediction文件" />
          <Step title="自动评分" description="获取评测报告" />
        </Steps>
      </Card>

      <Card>
        <div className="table-actions">
          <Space>
            <Input.Search
              placeholder="搜索评测任务"
              style={{ width: 300 }}
              allowClear
            />
            <Select
              placeholder="状态"
              style={{ width: 120 }}
              allowClear
            >
              <Select.Option value="pending">等待中</Select.Option>
              <Select.Option value="running">运行中</Select.Option>
              <Select.Option value="completed">已完成</Select.Option>
            </Select>
          </Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
            创建评测
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={mockData}
          rowKey="id"
        />
      </Card>

      <Modal
        title="创建评测任务"
        open={modalVisible}
        onOk={() => setModalVisible(false)}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form layout="vertical">
          <Form.Item label="评测名称" required>
            <Input placeholder="例如：GPT-4o 评测 v1" />
          </Form.Item>
          <Form.Item label="模型版本" required>
            <Input placeholder="例如：gpt-4o-2024-01" />
          </Form.Item>
          <Form.Item label="Prompt版本">
            <Input placeholder="可选" />
          </Form.Item>
          <Form.Item label="RAG版本">
            <Input placeholder="可选" />
          </Form.Item>
          <Form.Item label="Skill版本">
            <Input placeholder="可选" />
          </Form.Item>
          <Form.Item label="数据版本">
            <Input placeholder="可选，默认使用最新" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Evaluation
