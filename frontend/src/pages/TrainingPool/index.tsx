import { useState, useEffect, useCallback, useMemo } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Input, 
  Alert,
  Row,
  Col,
  Typography,
  Statistic,
  AutoComplete,
  message,
  Select
} from 'antd'
import { 
  DownloadOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  RiseOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import axios from 'axios'
import { Line } from '@ant-design/plots'
import dayjs from 'dayjs'

const { Text } = Typography

const API_BASE_URL = '/api/v1'
const USE_TEST_API = true

interface DataPoolItem {
  id: number
  pool_id: string
  data_type: string
  source_id: string
  pool_type: string
  category_l4: string
  input: string
  gt: Record<string, any>
  route_batch_id?: string
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

  const GTDisplay = ({ gt }: { gt: Record<string, any> }) => {
    const entries = Object.entries(gt || {})
    if (entries.length === 0) return <Text type="secondary">-</Text>
    
    return (
      <div style={{ 
        background: '#f6ffed', 
        padding: '8px 12px', 
        borderRadius: 6, 
        border: '1px solid #b7eb8f',
        maxWidth: 400
      }}>
        {entries.slice(0, 3).map(([key, value]) => (
          <div key={key} style={{ marginBottom: 4 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>{key}:</Text>
            <Text style={{ fontSize: 13, marginLeft: 8, color: '#389e0d' }}>
              {String(value).substring(0, 50)}
            </Text>
          </div>
        ))}
        {entries.length > 3 && (
          <Tag color="green">+{entries.length - 3}</Tag>
        )}
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
      render: (text: string) => (
        <div style={{ 
          maxWidth: 280, 
          padding: '4px 8px',
          background: '#e6f7ff',
          borderRadius: 4,
          border: '1px solid #91d5ff'
        }}>
          <Text style={{ fontSize: 13 }}>
            {text.length > 60 ? text.substring(0, 60) + '...' : text}
          </Text>
        </div>
      ),
    },
    {
      title: '标准答案 (GT)',
      dataIndex: 'gt',
      key: 'gt',
      width: 350,
      render: (gt: Record<string, any>) => <GTDisplay gt={gt} />,
    },
    {
      title: '四级类目',
      dataIndex: 'category_l4',
      key: 'category_l4',
      width: 120,
      render: (text: string) => <Tag color="blue">{text}</Tag>,
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
      width: 150,
    },
  ]

  return (
    <div>
      <div className="page-header">
        <h2>训练池</h2>
        <p className="subtitle">包含完整 Input + GT，供模型训练使用（参考 GAIA 训练集设计）</p>
      </div>

      <Alert
        message="训练池说明"
        description="训练池数据包含完整的输入(Input)和标准答案(GT)，可直接下载用于模型训练。数据来源于初创池的5:5分流。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

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
            <Button type="primary" icon={<DownloadOutlined />}>
              下载训练集
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="pool_id"
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => {
              setPagination(prev => ({ ...prev, current: page, pageSize: pageSize || 10 }))
            },
          }}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>
    </div>
  )
}

export default TrainingPool
