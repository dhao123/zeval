import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Progress,
  Tag,
  Spin,
  Alert,
  Typography,
  Tooltip,
} from 'antd'
import {
  DatabaseOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import axios from 'axios'

const { Text } = Typography

// API 基础URL
const API_BASE_URL = '/api/v1'

// 统计数据接口
interface CategoryStats {
  draft_count: number
  training_count: number
  evaluation_count: number
  total_confirmed: number
}

// 类目接口
interface Category {
  id: number
  category_id: string
  l1_name: string
  l2_name: string
  l3_name: string
  l4_name: string
  full_path: string
  source: string
  is_active: boolean
  created_at: string
  updated_at: string
  stats?: CategoryStats
}

// 仪表盘数据接口
interface DashboardData {
  total_categories: number
  total_draft: number
  total_training: number
  total_evaluation: number
  total_data: number
  categories: Category[]
}

// API响应接口
interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// 来源标签映射
const sourceMap: Record<string, { label: string; color: string }> = {
  upload: { label: '上传', color: 'blue' },
  auto: { label: '自动', color: 'green' },
  manual: { label: '手动', color: 'orange' },
}

// 四级类目展示组件
const CategoryDisplay = ({
  l1,
  l2,
  l3,
  l4,
}: {
  l1: string
  l2: string
  l3: string
  l4: string
}) => {
  return (
    <div style={{ fontSize: 12 }}>
      <div>
        <Text type="secondary">L1:</Text>
        <Tag color="blue" style={{ marginLeft: 4 }}>
          {l1}
        </Tag>
      </div>
      <div style={{ marginTop: 2 }}>
        <Text type="secondary">L2:</Text>
        <Tag color="cyan" style={{ marginLeft: 4 }}>
          {l2}
        </Tag>
      </div>
      <div style={{ marginTop: 2 }}>
        <Text type="secondary">L3:</Text>
        <Tag color="green" style={{ marginLeft: 4 }}>
          {l3}
        </Tag>
      </div>
      <div style={{ marginTop: 2 }}>
        <Text type="secondary">L4:</Text>
        <Tag color="purple" style={{ marginLeft: 4 }}>
          {l4}
        </Tag>
      </div>
    </div>
  )
}

// 分布可视化组件
const DistributionBar = ({ stats }: { stats?: CategoryStats }) => {
  if (!stats || stats.total_confirmed === 0) {
    return <Text type="secondary">暂无数据</Text>
  }

  const total = stats.total_confirmed
  const trainingPercent = Math.round((stats.training_count / total) * 100)
  const evaluationPercent = Math.round((stats.evaluation_count / total) * 100)

  return (
    <div style={{ width: 200 }}>
      <Tooltip
        title={
          <div>
            <div>训练池: {stats.training_count}</div>
            <div>评测池: {stats.evaluation_count}</div>
            <div>总计: {stats.total_confirmed}</div>
          </div>
        }
      >
        <Progress
          percent={100}
          success={{ percent: trainingPercent }}
          strokeColor={{
            '0%': '#52c41a',
            '100%': '#1890ff',
          }}
          showInfo={false}
          size="small"
        />
      </Tooltip>
      <div style={{ fontSize: 11, marginTop: 4 }}>
        <Text type="success" style={{ marginRight: 8 }}>
          训练: {trainingPercent}%
        </Text>
        <Text style={{ color: '#1890ff' }}>评测: {evaluationPercent}%</Text>
      </div>
    </div>
  )
}

function Dashboard() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get<ApiResponse<DashboardData>>(
        `${API_BASE_URL}/categories/dashboard`
      )

      if (response.data.code === 0) {
        setData(response.data.data)
      } else {
        setError(response.data.message || '获取数据失败')
      }
    } catch (err: any) {
      console.error('Fetch dashboard error:', err)
      setError(err.response?.data?.message || '获取数据失败，请检查网络连接')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // 表格列定义
  const columns: ColumnsType<Category> = [
    {
      title: '类目层级',
      key: 'category',
      width: 200,
      render: (_: any, record: Category) => (
        <CategoryDisplay
          l1={record.l1_name}
          l2={record.l2_name}
          l3={record.l3_name}
          l4={record.l4_name}
        />
      ),
    },
    {
      title: '初创池',
      dataIndex: ['stats', 'draft_count'],
      key: 'draft_count',
      width: 100,
      align: 'center',
      render: (_: number, record: Category) => (
        <Tag color="default">{record.stats?.draft_count || 0}</Tag>
      ),
    },
    {
      title: '训练池',
      dataIndex: ['stats', 'training_count'],
      key: 'training_count',
      width: 100,
      align: 'center',
      render: (_: number, record: Category) => (
        <Tag color="green">{record.stats?.training_count || 0}</Tag>
      ),
    },
    {
      title: '评测池',
      dataIndex: ['stats', 'evaluation_count'],
      key: 'evaluation_count',
      width: 100,
      align: 'center',
      render: (_: number, record: Category) => (
        <Tag color="blue">{record.stats?.evaluation_count || 0}</Tag>
      ),
    },
    {
      title: '总确认量',
      dataIndex: ['stats', 'total_confirmed'],
      key: 'total_confirmed',
      width: 100,
      align: 'center',
      render: (_: number, record: Category) => (
        <Text strong>{record.stats?.total_confirmed || 0}</Text>
      ),
    },
    {
      title: '分布',
      key: 'distribution',
      width: 220,
      render: (_: any, record: Category) => (
        <DistributionBar stats={record.stats} />
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 100,
      align: 'center',
      render: (source: string) => {
        const { label, color } = sourceMap[source] || {
          label: source,
          color: 'default',
        }
        return <Tag color={color}>{label}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
    },
  ]

  return (
    <div>
      <div className="page-header">
        <h2>数据看板</h2>
        <p className="subtitle">平台数据概览</p>
      </div>

      {error && (
        <Alert
          message="数据加载失败"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          closable
          onClose={() => setError(null)}
        />
      )}

      <Spin spinning={loading} tip="加载中...">
        <Row gutter={[16, 16]}>
          <Col span={4}>
            <Card>
              <Statistic
                title="总类目数"
                value={data?.total_categories || 0}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card>
              <Statistic
                title="初创池总量"
                value={data?.total_draft || 0}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card>
              <Statistic
                title="训练池总量"
                value={data?.total_training || 0}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card>
              <Statistic
                title="评测池总量"
                value={data?.total_evaluation || 0}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card>
              <Statistic
                title="总数据量"
                value={data?.total_data || 0}
                prefix={<TrophyOutlined />}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card title="类目统计详情">
              <Table
                columns={columns}
                dataSource={data?.categories || []}
                rowKey="category_id"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条`,
                }}
                scroll={{ x: 1100 }}
                size="middle"
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  )
}

export default Dashboard
