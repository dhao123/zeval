import { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Space,
  Tag,
  Typography,
  Table,
  Descriptions,
  Badge,
  message,
  Empty
} from 'antd'
import {
  ArrowLeftOutlined,
  FileOutlined,
  UserOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  DownloadOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import axios from 'axios'
import { formatBeijingTime } from '@/utils/date'

const { Title, Text, Link } = Typography

interface UploadBatch {
  batch_id: string
  file_name: string
  file_url: string
  file_size: number
  owner_name: string
  record_count: number
  success_count: number
  fail_count: number
  status: string
  remark: string
  created_at: string
}

interface SyntheticCase {
  id: number
  synthetic_id: string
  input: string
  gt: Record<string, any>
  category_l4: string
  status: string
  created_at: string
}

interface UploadBatchDetailProps {
  batch: UploadBatch
  onBack: () => void
}

export function UploadBatchDetail({ batch, onBack }: UploadBatchDetailProps) {
  const [loading, setLoading] = useState(false)
  const [cases, setCases] = useState<SyntheticCase[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
    pages: 0
  })

  const fetchCases = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const response = await axios.get(
        `/api/v1/upload-batches/${batch.batch_id}/cases?page=${page}&size=${pageSize}`
      )
      if (response.data.code === 0) {
        setCases(response.data.data || [])
        setPagination(response.data.pagination || { current: 1, pageSize: 10, total: 0, pages: 0 })
      }
    } catch (error) {
      console.error('Failed to fetch cases:', error)
      message.error('获取Case列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCases()
  }, [batch.batch_id])

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { status: 'processing' | 'success' | 'error' | 'default'; text: string }> = {
      processing: { status: 'processing', text: '处理中' },
      completed: { status: 'success', text: '已完成' },
      failed: { status: 'error', text: '失败' }
    }
    const { status: badgeStatus, text } = statusMap[status] || { status: 'default', text: status }
    return <Badge status={badgeStatus} text={text} />
  }

  const getCaseStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      draft: { color: 'default', text: '草稿' },
      confirmed: { color: 'success', text: '已确认' },
      rejected: { color: 'error', text: '已拒绝' }
    }
    const { color, text } = statusMap[status] || { color: 'default', text: status }
    return <Tag color={color}>{text}</Tag>
  }

  const columns: ColumnsType<SyntheticCase> = [
    {
      title: 'ID',
      dataIndex: 'synthetic_id',
      key: 'synthetic_id',
      width: 180,
      render: (text: string) => <Text code copyable style={{ fontSize: 11 }}>{text}</Text>
    },
    {
      title: '输入 (Input)',
      dataIndex: 'input',
      key: 'input',
      render: (text: string) => (
        <div style={{ maxWidth: 400, padding: '8px', background: '#e6f7ff', borderRadius: 4 }}>
          <Text style={{ fontSize: 13 }}>{text.length > 100 ? text.substring(0, 100) + '...' : text}</Text>
        </div>
      )
    },
    {
      title: '标准答案 (GT)',
      dataIndex: 'gt',
      key: 'gt',
      render: (gt: Record<string, any>) => {
        const entries = Object.entries(gt || {})
        if (entries.length === 0) return <Text type="secondary">-</Text>
        return (
          <div style={{ background: '#f6ffed', padding: '8px', borderRadius: 4 }}>
            {entries.slice(0, 2).map(([key, value]) => (
              <div key={key}><Text type="secondary" style={{ fontSize: 12 }}>{key}:</Text> <Text style={{ fontSize: 13 }}>{String(value).substring(0, 30)}</Text></div>
            ))}
            {entries.length > 2 && <Tag color="green">+{entries.length - 2}</Tag>}
          </div>
        )
      }
    },
    {
      title: '类目',
      dataIndex: 'category_l4',
      key: 'category_l4',
      width: 120,
      render: (text: string) => <Tag color="blue">{text || '未分类'}</Tag>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getCaseStatusTag(status)
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (value: string) => formatBeijingTime(value)
    }
  ]

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Space size="large">
          <Button icon={<ArrowLeftOutlined />} onClick={onBack} size="large">返回批次列表</Button>
          <Title level={4} style={{ margin: 0 }}>批次详情: {batch.batch_id}</Title>
          {getStatusBadge(batch.status)}
        </Space>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions title="批次基本信息" bordered column={3}
          extra={<Button type="primary" icon={<DownloadOutlined />} href={batch.file_url} target="_blank">下载原文件</Button>}>
          <Descriptions.Item label="文件名"><Space><FileOutlined style={{ color: '#1890ff' }} /><Link href={batch.file_url} target="_blank">{batch.file_name}</Link></Space></Descriptions.Item>
          <Descriptions.Item label="文件大小">{formatFileSize(batch.file_size)}</Descriptions.Item>
          <Descriptions.Item label="数据Owner"><Space><UserOutlined />{batch.owner_name || '未知'}</Space></Descriptions.Item>
          <Descriptions.Item label="上传时间"><Space><ClockCircleOutlined />{formatBeijingTime(batch.created_at)}</Space></Descriptions.Item>
          <Descriptions.Item label="总数据量"><Space><DatabaseOutlined style={{ color: '#52c41a' }} /><Text strong>{batch.record_count} 条</Text></Space></Descriptions.Item>
          <Descriptions.Item label="处理结果"><Space><Tag color="success">成功: {batch.success_count}</Tag>{batch.fail_count > 0 && <Tag color="error">失败: {batch.fail_count}</Tag>}</Space></Descriptions.Item>
          {batch.remark && <Descriptions.Item label="备注" span={3}>{batch.remark}</Descriptions.Item>}
        </Descriptions>
      </Card>

      <Card title={<Space><DatabaseOutlined style={{ color: '#1890ff' }} /><span>Case明细列表</span><Tag color="blue">{pagination.total} 条</Tag></Space>}>
        <Table
          columns={columns}
          dataSource={cases}
          rowKey="synthetic_id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => fetchCases(page, pageSize)
          }}
          scroll={{ x: 1200 }}
          size="small"
          locale={{ emptyText: <Empty description="该批次暂无Case数据" /> }}
        />
      </Card>
    </div>
  )
}

export default UploadBatchDetail
