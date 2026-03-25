import { useState, useEffect, useCallback, useMemo } from 'react'
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
  Select,
  DatePicker,
  Button,
  Space,
  Cascader,
} from 'antd'
import {
  DatabaseOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
  BarChartOutlined,
  RiseOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { DefaultOptionType } from 'antd/es/cascader'
import axios from '../../utils/request'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'

const { Text } = Typography
const { RangePicker } = DatePicker

// API 基础URL
// request.ts 的 baseURL 已经包含 /api/v1，所以这里不需要再加前缀
const API_PREFIX = ''

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

// 趋势数据点（双轴组合图）
interface TrendDataPoint {
  date: string
  total: number  // 折线图：总数据量
  category_counts: Record<string, number>  // 柱状图：各一级类目数据量
}

// 趋势响应
interface TrendResponse {
  trend: TrendDataPoint[]
  summary: Record<string, number>
  categories: string[]  // 一级类目列表
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

// 趋势图表组件 - 使用 ECharts 双轴组合图
const TrendChart = ({
  data,
  categories,
  loading,
}: {
  data: TrendDataPoint[]
  categories: string[]
  loading: boolean
}) => {
  const option = useMemo(() => {
    const dates = data.map((item) => item.date)
    
    // 为每个一级类目准备堆叠柱状图数据
    const categoryColors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96']
    
    const barSeries = categories.map((cat, index) => ({
      name: cat,
      type: 'bar',
      stack: 'total',
      data: data.map((item) => item.category_counts?.[cat] || 0),
      itemStyle: { color: categoryColors[index % categoryColors.length] },
      emphasis: { focus: 'series' },
    }))

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
      },
      legend: {
        data: [...categories, '总数据量'],
        top: 10,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisPointer: { type: 'shadow' },
      },
      yAxis: [
        {
          type: 'value',
          name: '类目数据量',
          position: 'left',
          minInterval: 1,
        },
        {
          type: 'value',
          name: '总数据量',
          position: 'right',
          minInterval: 1,
        },
      ],
      series: [
        ...barSeries,
        {
          name: '总数据量',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          data: data.map((item) => item.total),
          itemStyle: { color: '#ff7875' },
          lineStyle: { width: 3 },
          symbol: 'circle',
          symbolSize: 8,
        },
      ],
    }

    return option
  }, [data, categories])

  if (loading) {
    return (
      <div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin tip="加载趋势数据..." />
      </div>
    )
  }

  if (data.length === 0 || categories.length === 0) {
    return (
      <div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
        暂无数据
      </div>
    )
  }

  return (
    <div style={{ height: 350 }}>
      <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
    </div>
  )
}

function Dashboard() {
  const [loading, setLoading] = useState(false)
  const [trendLoading, setTrendLoading] = useState(false)
  const [data, setData] = useState<DashboardData | null>(null)
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([])
  const [trendCategories, setTrendCategories] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  
  // 筛选器状态
  const [timeRange, setTimeRange] = useState<number>(7)
  const [customDates, setCustomDates] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string[]>([])
  const [categoryOptions, setCategoryOptions] = useState<DefaultOptionType[]>([])

  // 获取类目选项（级联选择器）
  const fetchCategoryOptions = useCallback(async () => {
    try {
      const data = await axios.get<ApiResponse<{ items: Category[]; total: number }>>(
        `${API_PREFIX}/categories?include_stats=false&limit=1000`
      ) as any
      if (data.code === 0) {
        const categories = data.data.items || []
        // 构建级联选项
        const options: DefaultOptionType[] = []
        const l1Map = new Map<string, DefaultOptionType>()
        
        categories.forEach((cat: Category) => {
          if (!l1Map.has(cat.l1_name)) {
            const l1Option: DefaultOptionType = {
              value: cat.l1_name,
              label: cat.l1_name,
              children: [],
            }
            l1Map.set(cat.l1_name, l1Option)
            options.push(l1Option)
          }
          
          const l1Option = l1Map.get(cat.l1_name)!
          let l2Option = (l1Option.children as DefaultOptionType[])?.find(
            (c) => c.value === cat.l2_name
          )
          
          if (!l2Option) {
            l2Option = {
              value: cat.l2_name,
              label: cat.l2_name,
              children: [],
            }
            l1Option.children = [...(l1Option.children || []), l2Option]
          }
          
          let l3Option = (l2Option.children as DefaultOptionType[])?.find(
            (c) => c.value === cat.l3_name
          )
          
          if (!l3Option) {
            l3Option = {
              value: cat.l3_name,
              label: cat.l3_name,
              children: [],
            }
            l2Option.children = [...(l2Option.children || []), l3Option]
          }
          
          const l4Exists = (l3Option.children as DefaultOptionType[])?.some(
            (c) => c.value === cat.l4_name
          )
          if (!l4Exists) {
            l3Option.children = [
              ...(l3Option.children || []),
              { value: cat.l4_name, label: cat.l4_name },
            ]
          }
        })
        
        setCategoryOptions(options)
      }
    } catch (err) {
      console.error('Failed to fetch category options:', err)
    }
  }, [])

  // 获取仪表盘基础数据
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await axios.get<ApiResponse<DashboardData>>(
        `${API_PREFIX}/categories/dashboard`
      ) as any

      if (data.code === 0) {
        setData(data.data)
      } else {
        setError(data.message || '获取数据失败')
      }
    } catch (err: any) {
      console.error('Fetch dashboard error:', err)
      setError(err.message || '获取数据失败，请检查网络连接')
    } finally {
      setLoading(false)
    }
  }, [])

  // 获取趋势数据
  const fetchTrendData = useCallback(async () => {
    setTrendLoading(true)
    try {
      const params = new URLSearchParams()
      
      // 时间范围
      if (customDates && customDates[0] && customDates[1]) {
        params.append('start_date', customDates[0].format('YYYY-MM-DD'))
        params.append('end_date', customDates[1].format('YYYY-MM-DD'))
      } else {
        params.append('days', String(timeRange))
      }
      
      // 类目筛选
      if (selectedCategory.length >= 1) {
        params.append('category_l1', selectedCategory[0])
      }
      if (selectedCategory.length >= 2) {
        params.append('category_l2', selectedCategory[1])
      }
      if (selectedCategory.length >= 3) {
        params.append('category_l3', selectedCategory[2])
      }
      if (selectedCategory.length >= 4) {
        params.append('category_l4', selectedCategory[3])
      }

      const data = await axios.get<ApiResponse<TrendResponse>>(
        `${API_PREFIX}/dashboard/trend?${params.toString()}`
      ) as any

      if (data.code === 0) {
        setTrendData(data.data.trend)
        setTrendCategories(data.data.categories || [])
      }
    } catch (err) {
      console.error('Fetch trend error:', err)
    } finally {
      setTrendLoading(false)
    }
  }, [timeRange, customDates, selectedCategory])

  useEffect(() => {
    fetchData()
    fetchCategoryOptions()
  }, [fetchData, fetchCategoryOptions])

  // 时间范围变化时自动获取趋势数据
  useEffect(() => {
    fetchTrendData()
  }, [fetchTrendData])

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

  // 处理时间范围变化
  const handleTimeRangeChange = (value: number) => {
    setTimeRange(value)
    setCustomDates(null)
  }

  // 处理自定义日期变化
  const handleCustomDateChange = (dates: any) => {
    if (dates && dates[0] && dates[1]) {
      setCustomDates([dates[0], dates[1]])
    } else {
      setCustomDates(null)
    }
  }

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
        {/* 第一行：核心指标卡 */}
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
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card>
              <Statistic
                title="训练池总量"
                value={data?.total_training || 0}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card>
              <Statistic
                title="评测池总量"
                value={data?.total_evaluation || 0}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={5}>
            <Card>
              <Statistic
                title="总数据量"
                value={data?.total_data || 0}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 第二行：全局数据增量趋势 */}
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card
              title={
                <Space>
                  <RiseOutlined style={{ color: '#1890ff' }} />
                  <span>数据增长趋势</span>
                </Space>
              }
              extra={
                <Space>
                  <Cascader
                    options={categoryOptions}
                    onChange={(value) => setSelectedCategory(value as string[])}
                    placeholder="筛选类目"
                    style={{ width: 200 }}
                    allowClear
                    changeOnSelect
                  />
                  <Select
                    value={timeRange}
                    onChange={handleTimeRangeChange}
                    style={{ width: 120 }}
                    options={[
                      { label: '最近7天', value: 7 },
                      { label: '最近14天', value: 14 },
                      { label: '最近30天', value: 30 },
                    ]}
                  />
                  <RangePicker
                    value={customDates}
                    onChange={handleCustomDateChange}
                    style={{ width: 240 }}
                    placeholder={['开始日期', '结束日期']}
                  />
                  <Button
                    type="primary"
                    icon={<SearchOutlined />}
                    onClick={fetchTrendData}
                    loading={trendLoading}
                  >
                    查询
                  </Button>
                </Space>
              }
            >
              <TrendChart data={trendData} categories={trendCategories} loading={trendLoading} />
              <div style={{ marginTop: 16, padding: '12px 16px', background: '#f6ffed', borderRadius: 6 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  <strong>数据关系说明：</strong>
                  总数据量 = 初创池(草稿态) + 训练池 + 评测池；
                  初创池(已确认) = 训练池 + 评测池
                </Text>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 第三行：类目统计详情 */}
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
