import { useState, useEffect, useCallback, useMemo } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Input,
  Tooltip,
  Row,
  Col,
  Typography,
  Statistic,
  AutoComplete,
  message,
  Select,
  Divider
} from 'antd'
import { 
  DownloadOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  RiseOutlined,
  FullscreenOutlined,
  CompressOutlined,
  UserOutlined
} from '@ant-design/icons'
import PoolDownloadModal from '@/components/PoolDownloadModal'
import type { ColumnsType } from 'antd/es/table'
import axios from 'axios'
import { Line } from '@ant-design/plots'
import dayjs from 'dayjs'
import { formatBeijingTime } from '@/utils/date'

const { Text, Paragraph } = Typography

const API_BASE_URL = '/api/v1'
const USE_TEST_API = true

interface DataPoolItem {
  id: number
  pool_id: string
  data_type: string
  source_id: string
  pool_type: string
  category_l1?: string
  category_l2?: string
  category_l3?: string
  category_l4: string
  input: string
  gt: Record<string, any>
  route_batch_id?: string
  created_by?: number
  owner_name?: string
  created_at: string
  updated_at: string
}

interface ApiResponse<T> {
  code: number
  message: string
  data: T
  pagination?: {
    page: number
    size: number
    total: number
    pages: number
  }
}

// 计算日增量数据
const calculateDailyIncrement = (data: DataPoolItem[], days: number = 7) => {
  const endDate = dayjs()
  const startDate = endDate.subtract(days - 1, 'day')
  
  const dateMap: Record<string, number> = {}
  for (let i = 0; i < days; i++) {
    const date = startDate.add(i, 'day').format('YYYY-MM-DD')
    dateMap[date] = 0
  }
  
  data.forEach(item => {
    const date = dayjs(item.created_at).format('YYYY-MM-DD')
    if (dateMap.hasOwnProperty(date)) {
      dateMap[date]++
    }
  })
  
  return Object.entries(dateMap).map(([date, count]) => ({
    date: dayjs(date).format('MM-DD'),
    fullDate: date,
    count,
  }))
}

// GT展示组件 - 与初创池一致
const GTDisplay = ({ gt, compact = false }: { gt: Record<string, any>; compact?: boolean }) => {
  const entries = Object.entries(gt || {})
  
  if (entries.length === 0) {
    return <Text type="secondary">-</Text>
  }
  
  if (compact) {
    // 紧凑模式：标签云展示
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, maxWidth: 300 }}>
        {entries.slice(0, 4).map(([key, value]) => (
          <Tooltip key={key} title={`${key}: ${String(value)}`}>
            <Tag style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {key}: {String(value).substring(0, 15)}
            </Tag>
          </Tooltip>
        ))}
        {entries.length > 4 && (
          <Tag color="blue">+{entries.length - 4}</Tag>
        )}
      </div>
    )
  }
  
  // 完整模式：键值对列表
  return (
    <div style={{ 
      background: '#f6ffed', 
      padding: '8px 12px', 
      borderRadius: 6, 
      border: '1px solid #b7eb8f',
      maxWidth: 400
    }}>
      {entries.map(([key, value]) => (
        <div key={key} style={{ marginBottom: 4, display: 'flex', gap: 8 }}>
          <Text type="secondary" style={{ minWidth: 80, fontSize: 12 }}>{key}:</Text>
          <Text style={{ fontSize: 13, fontWeight: 500, color: '#389e0d' }}>
            {String(value)}
          </Text>
        </div>
      ))}
    </div>
  )
}

// 四级类目展示组件 - 与初创池一致
const CategoryDisplay = ({ 
  l1, l2, l3, l4 
}: { 
  l1?: string; l2?: string; l3?: string; l4?: string 
}) => {
  return (
    <div style={{ fontSize: 12 }}>
      {l1 && (
        <div>
          <Text type="secondary">一级:</Text>
          <Tag color="blue">{l1}</Tag>
        </div>
      )}
      {l2 && (
        <div style={{ marginTop: 2 }}>
          <Text type="secondary">二级:</Text>
          <Tag color="cyan">{l2}</Tag>
        </div>
      )}
      {l3 && (
        <div style={{ marginTop: 2 }}>
          <Text type="secondary">三级:</Text>
          <Tag color="green">{l3}</Tag>
        </div>
      )}
      {l4 && (
        <div style={{ marginTop: 2 }}>
          <Text type="secondary">四级:</Text>
          <Tag color="purple">{l4}</Tag>
        </div>
      )}
    </div>
  )
}

// Input展示组件 - 与初创池一致
const InputDisplay = ({ input }: { input: string }) => {
  return (
    <Tooltip 
      title={
        <div style={{ maxWidth: 400, padding: 8 }}>
          <Text strong style={{ color: '#fff' }}>完整Input:</Text>
          <Paragraph style={{ color: '#fff', marginTop: 8 }}>{input}</Paragraph>
        </div>
      }
      placement="topLeft"
      overlayStyle={{ maxWidth: 450 }}
    >
      <div style={{ 
        maxWidth: 300, 
        cursor: 'pointer',
        padding: '4px 8px',
        background: '#e6f7ff',
        borderRadius: 4,
        border: '1px solid #91d5ff'
      }}>
        <Text style={{ fontSize: 13 }}>
          {input.length > 50 ? input.substring(0, 50) + '...' : input}
        </Text>
      </div>
    </Tooltip>
  )
}

function TrainingPool() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<DataPoolItem[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  })
  
  const [filters, setFilters] = useState({
    keyword: '',
    category_l4: undefined as string | undefined,
  })
  
  const [categoryOptions, setCategoryOptions] = useState<{value: string, label: string}[]>([])
  const [timeRange, setTimeRange] = useState(7)
  const [downloadModalOpen, setDownloadModalOpen] = useState(false)
  const [showFullContent, setShowFullContent] = useState(false)
  const [expandedRowKeys, setExpandedRowKeys] = useState<React.Key[]>([])

  const fetchCategoryOptions = useCallback(async (keyword?: string) => {
    try {
      const params = new URLSearchParams()
      if (keyword) params.append('keyword', keyword)
      const response = await axios.get<ApiResponse<any[]>>(
        `${API_BASE_URL}/categories/l4-options?${params.toString()}`
      )
      if (response.data.code === 0) {
        setCategoryOptions(response.data.data || [])
      }
    } catch (error) {
      console.error('Failed to fetch category options:', error)
    }
  }, [])

  useEffect(() => {
    fetchCategoryOptions()
  }, [fetchCategoryOptions])

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('page', String(pagination.current))
      params.append('size', String(pagination.pageSize))
      
      if (filters.category_l4) params.append('category_l4', filters.category_l4)
      if (filters.keyword) params.append('keyword', filters.keyword)

      const apiPath = USE_TEST_API 
        ? `/data-pools/test/training?${params.toString()}`
        : `/data-pools/training?${params.toString()}`

      const response = await axios.get<ApiResponse<DataPoolItem[]>>(
        `${API_BASE_URL}${apiPath}`
      )
      
      if (response.data.code === 0) {
        setData(response.data.data || [])
        if (response.data.pagination) {
          setPagination(prev => ({
            ...prev,
            total: response.data.pagination!.total,
          }))
        }
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '获取数据失败')
    } finally {
      setLoading(false)
    }
  }, [pagination.current, pagination.pageSize, filters])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const dailyData = useMemo(() => {
    return calculateDailyIncrement(data, timeRange)
  }, [data, timeRange])

  // 平滑折线图配置
  const lineConfig = useMemo(() => ({
    data: dailyData,
    xField: 'date',
    yField: 'count',
    smooth: true,
    color: '#52c41a',
    xAxis: {
      title: { text: '日期' },
    },
    yAxis: {
      title: { text: '数据量' },
      minInterval: 1,
    },
    meta: {
      date: { alias: '日期' },
      count: { alias: '数据量' },
    },
    areaStyle: {
      fill: 'l(270) 0:#ffffff 0.5:#d9f7be 1:#52c41a',
      opacity: 0.3,
    },
    point: {
      size: 4,
      shape: 'circle',
      style: {
        fill: '#52c41a',
        stroke: '#fff',
        lineWidth: 2,
      },
    },
    tooltip: {
      showMarkers: true,
    },
  }), [dailyData])

  // 展开行内容
  const expandedRowRender = (record: DataPoolItem) => {
    return (
      <div style={{ padding: '16px 24px', background: '#fafafa', borderRadius: 8 }}>
        <Row gutter={24}>
          <Col span={12}>
            <div style={{ marginBottom: 16 }}>
              <Text strong style={{ fontSize: 14, color: '#1890ff' }}>📝 Input (输入)</Text>
              <div style={{ 
                marginTop: 8, 
                padding: 12, 
                background: '#fff', 
                borderRadius: 6,
                border: '1px solid #d9d9d9',
                minHeight: 60
              }}>
                <Text style={{ fontSize: 14 }}>{record.input}</Text>
              </div>
            </div>
          </Col>
          <Col span={12}>
            <div style={{ marginBottom: 16 }}>
              <Text strong style={{ fontSize: 14, color: '#52c41a' }}>✓ GT (标准答案)</Text>
              <div style={{ marginTop: 8 }}>
                <GTDisplay gt={record.gt} />
              </div>
            </div>
          </Col>
        </Row>
        
        <Divider style={{ margin: '12px 0' }} />
        
        <Row gutter={24}>
          <Col span={8}>
            <Text strong style={{ fontSize: 13 }}>📂 类目信息</Text>
            <div style={{ marginTop: 8 }}>
              <Tag color="blue">{record.category_l4}</Tag>
            </div>
          </Col>
          <Col span={8}>
            <Text strong style={{ fontSize: 13 }}>🏷️ 元数据</Text>
            <div style={{ marginTop: 8, fontSize: 12 }}>
              <div>ID: <Text copyable>{record.pool_id}</Text></div>
              <div>来源: {record.source_id}</div>
              {record.route_batch_id && (
                <div>分流批次: <Tag color="green">{record.route_batch_id}</Tag></div>
              )}
            </div>
          </Col>
          <Col span={8}>
            <Text strong style={{ fontSize: 13 }}>⏰ 时间信息</Text>
            <div style={{ marginTop: 8, fontSize: 12 }}>
              <div>创建: {formatBeijingTime(record.created_at)}</div>
              <div>更新: {formatBeijingTime(record.updated_at)}</div>
            </div>
          </Col>
        </Row>
      </div>
    )
  }

  const columns: ColumnsType<DataPoolItem> = [
    {
      title: 'ID',
      dataIndex: 'pool_id',
      key: 'pool_id',
      width: 180,
      render: (text: string) => (
        <Text copyable style={{ fontSize: 12 }}>{text}</Text>
      ),
    },
    {
      title: '输入 (Input)',
      dataIndex: 'input',
      key: 'input',
      width: 300,
      render: (text: string) => <InputDisplay input={text} />,
    },
    {
      title: '标准答案 (GT)',
      dataIndex: 'gt',
      key: 'gt',
      width: 350,
      render: (gt: Record<string, any>) => <GTDisplay gt={gt} compact={!showFullContent} />,
    },
    {
      title: '四级类目',
      key: 'category',
      width: 180,
      render: (_: any, record: DataPoolItem) => (
        <CategoryDisplay 
          l1={record.category_l1} 
          l2={record.category_l2} 
          l3={record.category_l3} 
          l4={record.category_l4} 
        />
      ),
    },
    {
      title: '数据Owner',
      dataIndex: 'owner_name',
      key: 'owner_name',
      width: 120,
      render: (text: string) => (
        <Space>
          <UserOutlined style={{ color: '#8c8c8c' }} />
          <Text>{text || '-'}</Text>
        </Space>
      ),
    },
    {
      title: '来源批次',
      dataIndex: 'route_batch_id',
      key: 'route_batch_id',
      width: 150,
      render: (text: string) => text ? <Tag color="green">{text}</Tag> : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (value: string) => formatBeijingTime(value),
    },
  ]

  return (
    <div>
      <div className="page-header">
        <h2>训练池</h2>
        <p className="subtitle">包含完整 Input + GT，供模型训练使用（参考 GAIA 训练集设计）</p>
      </div>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card style={{ height: 180 }}>
            <Statistic
              title="训练池数据量"
              value={pagination.total}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={18}>
          <Card 
            style={{ height: 180 }}
            title={
              <Space>
                <RiseOutlined style={{ color: '#52c41a' }} />
                <span>日增量趋势</span>
                <Select
                  value={timeRange}
                  onChange={setTimeRange}
                  options={[
                    { label: '最近7天', value: 7 },
                    { label: '最近14天', value: 14 },
                    { label: '最近30天', value: 30 },
                  ]}
                  size="small"
                  style={{ width: 100 }}
                />
              </Space>
            }
            bodyStyle={{ padding: '8px 12px', height: 'calc(100% - 48px)' }}
          >
            {dailyData.length > 0 && dailyData.some(d => d.count > 0) ? (
              <div style={{ height: '100%' }}>
                <Line {...lineConfig} />
              </div>
            ) : (
              <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                暂无数据
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space wrap>
            <Input.Search
              placeholder="搜索输入文本"
              style={{ width: 250 }}
              value={filters.keyword}
              onChange={(e) => setFilters(prev => ({ ...prev, keyword: e.target.value }))}
              onSearch={fetchData}
              allowClear
            />
            <AutoComplete
              placeholder="搜索四级类目"
              style={{ width: 320 }}
              popupMatchSelectWidth={false}
              dropdownStyle={{ minWidth: 400, maxWidth: 600 }}
              value={filters.category_l4}
              onChange={(value) => setFilters(prev => ({ ...prev, category_l4: value }))}
              onSearch={fetchCategoryOptions}
              options={categoryOptions}
              allowClear
            />
            <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
          </Space>
          
          <Space>
            <Button 
              icon={showFullContent ? <CompressOutlined /> : <FullscreenOutlined />}
              onClick={() => setShowFullContent(!showFullContent)}
            >
              {showFullContent ? '紧凑视图' : '展开视图'}
            </Button>
            <Button 
              type="primary" 
              icon={<DownloadOutlined />}
              onClick={() => setDownloadModalOpen(true)}
            >
              下载训练集
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="pool_id"
          expandable={{
            expandedRowRender,
            expandedRowKeys,
            onExpandedRowsChange: (keys: readonly React.Key[]) => setExpandedRowKeys([...keys]),
          }}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => {
              setPagination(prev => ({ ...prev, current: page, pageSize: pageSize || 10 }))
            },
          }}
          scroll={{ x: 1400 }}
          size="small"
        />
      </Card>

      {/* 下载对话框 */}
      <PoolDownloadModal
        open={downloadModalOpen}
        onClose={() => setDownloadModalOpen(false)}
        poolType="training"
        defaultCategory={filters.category_l4}
      />
    </div>
  )
}

export default TrainingPool
