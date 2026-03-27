import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Tag,
  Card,
  Typography,
  Tooltip,
  message,
  Popconfirm,
  Empty,
  Skeleton
} from 'antd'
import {
  EyeOutlined,
  DeleteOutlined,
  FileOutlined,
  UserOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import axios from 'axios'
import { formatBeijingTime } from '@/utils/date'

const { Text, Link } = Typography

interface UploadBatch {
  id: number
  batch_id: string
  file_name: string
  file_url: string
  object_key: string
  file_size: number
  owner_id: string
  owner_name: string
  record_count: number
  success_count: number
  fail_count: number
  status: string
  remark: string
  created_at: string
}

interface UploadBatchListProps {
  onViewDetail: (batch: UploadBatch) => void
  uploadButton?: React.ReactNode
}

export function UploadBatchList({ onViewDetail, uploadButton }: UploadBatchListProps) {
  const [loading, setLoading] = useState(false)
  const [batches, setBatches] = useState<UploadBatch[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
    pages: 0
  })

  const fetchBatches = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/v1/upload-batches?page=${page}&size=${pageSize}`)
      if (response.data.code === 0) {
        setBatches(response.data.data || [])
        const paginationData = response.data.pagination || { page: 1, size: 10, total: 0, pages: 0 }
        setPagination({
          current: paginationData.page,
          pageSize: paginationData.size,
          total: paginationData.total,
          pages: paginationData.pages
        })
      }
    } catch (error: any) {
      console.error('Failed to fetch batches:', error)
      const status = error.response?.status
      const detail = error.response?.data?.detail
      
      if (status === 401) {
        message.error('登录已过期，请重新登录')
      } else if (detail) {
        message.error(detail)
      }
      
      setBatches([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBatches()
  }, [])

  const handleDelete = async (batchId: string) => {
    try {
      const response = await axios.delete(`/api/v1/upload-batches/${batchId}`)
      if (response.data.code === 0) {
        message.success('删除成功')
        fetchBatches(pagination.current, pagination.pageSize)
      }
    } catch (error: any) {
      console.error('Delete failed:', error)
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      processing: { color: 'blue', text: '处理中' },
      completed: { color: 'green', text: '已完成' },
      failed: { color: 'red', text: '失败' }
    }
    const { color, text } = statusMap[status] || { color: 'default', text: status }
    return <Tag color={color}>{text}</Tag>
  }

  const columns: ColumnsType<UploadBatch> = [
    {
      title: '上传ID',
      dataIndex: 'batch_id',
      key: 'batch_id',
      width: 180,
      render: (text: string) => (
        <Text code style={{ fontSize: 12 }}>{text}</Text>
      )
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      width: 250,
      render: (text: string, record: UploadBatch) => (
        <Space>
          <FileOutlined style={{ color: '#1890ff' }} />
          <Link 
            href={record.file_url} 
            target="_blank"
            title={text}
            style={{ maxWidth: 200, display: 'inline-block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
          >
            {text}
          </Link>
        </Space>
      )
    },
    {
      title: '数据Owner',
      dataIndex: 'owner_name',
      key: 'owner_name',
      width: 120,
      render: (text: string) => (
        <Space>
          <UserOutlined />
          <Text>{text || '未知'}</Text>
        </Space>
      )
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (value: string) => (
        <Space>
          <ClockCircleOutlined style={{ color: '#8c8c8c' }} />
          <Text style={{ fontSize: 13 }}>{formatBeijingTime(value)}</Text>
        </Space>
      )
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size)
    },
    {
      title: '数据量',
      dataIndex: 'record_count',
      key: 'record_count',
      width: 120,
      render: (count: number, record: UploadBatch) => (
        <Tooltip title={`成功: ${record.success_count}, 失败: ${record.fail_count}`}>
          <Space>
            <DatabaseOutlined style={{ color: '#52c41a' }} />
            <Text strong>{count} 条</Text>
          </Space>
        </Tooltip>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status)
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record: UploadBatch) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="primary"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onViewDetail(record)}
            >
              详情
            </Button>
          </Tooltip>
          <Popconfirm
            title="确认删除"
            description={`确定要删除批次 ${record.batch_id} 吗？这将同时删除关联的 ${record.record_count} 条数据。`}
            onConfirm={() => handleDelete(record.batch_id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="link"
              danger
              size="small"
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  if (loading && batches.length === 0) {
    return <Skeleton active paragraph={{ rows: 5 }} />
  }

  return (
    <Card
      title={
        <Space>
          <DatabaseOutlined style={{ color: '#1890ff' }} />
          <span>上传任务列表</span>
          <Tag color="blue">{pagination.total} 个批次</Tag>
        </Space>
      }
      extra={
        <Space>
          {uploadButton}
          <Button 
            type="link" 
            icon={<ReloadOutlined />}
            onClick={() => fetchBatches(pagination.current, pagination.pageSize)}
          >
            刷新
          </Button>
        </Space>
      }
    >
      {batches.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无上传批次"
        />
      ) : (
        <Table
          columns={columns}
          dataSource={batches}
          rowKey="batch_id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => {
              fetchBatches(page, pageSize)
            }
          }}
          scroll={{ x: 1200 }}
          size="small"
        />
      )}
    </Card>
  )
}

export default UploadBatchList
