import { useState, useEffect, useCallback, useMemo } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Select, 
  Space, 
  Tag, 
  Input, 
  Upload, 
  Modal, 
  Form, 
  message,
  Popconfirm,
  Tooltip,
  Alert,
  Descriptions,
  Row,
  Col,
  Typography,
  Divider,
  AutoComplete,
  Statistic
} from 'antd'
import { 
  CheckOutlined, 
  CloseOutlined, 
  EditOutlined, 
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  PartitionOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  CompressOutlined,
  ExclamationCircleOutlined,
  DatabaseOutlined,
  RiseOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import axios from 'axios'
import { Line } from '@ant-design/plots'
import dayjs from 'dayjs'
import { formatBeijingTime } from '@/utils/date'

const { Text, Paragraph } = Typography

// API 基础URL
const API_BASE_URL = '/api/v1'
const USE_TEST_API = true

const getApiPath = (path: string) => {
  if (USE_TEST_API && path.startsWith('/draft-pool')) {
    if (path === '/draft-pool' || path.startsWith('/draft-pool?')) {
      return path.replace('/draft-pool', '/draft-pool/test/list')
    }
    if (path.startsWith('/draft-pool/export')) {
      return path.replace('/draft-pool/export', '/draft-pool/test/export')
    }
    return path.replace('/draft-pool/', '/draft-pool/test/')
  }
  return path
}

// 定义与种子数据同构的接口
interface SyntheticData {
  id: number
  synthetic_id: string
  input: string
  gt: Record<string, any>
  category_l1?: string
  category_l2?: string
  category_l3?: string
  category_l4?: string
  category_path?: string
  status: 'draft' | 'confirmed' | 'rejected'
  pool_location?: 'training' | 'evaluation' | null  // 所在池位置（后端查询）
  ai_check_passed: boolean
  seed_id?: string
  standard_id?: string
  skill_id?: string
  route_batch_id?: string
  version: string
  hash: string
  created_by?: number
  confirmed_by?: number
  confirmed_at?: string
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
const calculateDailyIncrement = (data: SyntheticData[], days: number = 7) => {
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

// 所在池映射 - 根据状态和分流情况判断
// 所在池映射 - 优先使用后端返回的 pool_location
const getPoolLocation = (record: SyntheticData): { label: string; color: string } => {
  if (record.status === 'draft') {
    return { label: '初创池', color: 'default' }
  }
  if (record.status === 'rejected') {
    return { label: '-', color: 'default' }
  }
  if (record.status === 'confirmed') {
    // 使用后端查询的精确池位置
    if (record.pool_location === 'training') {
      return { label: '训练池', color: 'green' }
    }
    if (record.pool_location === 'evaluation') {
      return { label: '评测池', color: 'blue' }
    }
    // 已确认但尚未分流到池子
    if (record.route_batch_id) {
      return { label: '已确认(查询中)', color: 'orange' }
    }
    return { label: '已确认(待分流)', color: 'orange' }
  }
  return { label: '-', color: 'default' }
}

const statusMap: Record<string, { label: string; color: string }> = {
  draft: { label: '草稿', color: 'default' },
  confirmed: { label: '已确认', color: 'green' },
  rejected: { label: '已拒绝', color: 'red' },
}

// GT展示组件 - 全貌展示
const GTDisplay = ({ gt, compact = false }: { gt: Record<string, any>; compact?: boolean }) => {
  const entries = Object.entries(gt)
  
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

// Input展示组件 - 全貌展示
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

// 四级类目展示组件
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

function DraftPool() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<SyntheticData[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [expandedRowKeys, setExpandedRowKeys] = useState<React.Key[]>([])
  const [showFullContent, setShowFullContent] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  })
  
  const [filters, setFilters] = useState({
    keyword: '',
    category_l4: undefined as string | undefined,
    status: undefined as string | undefined,
  })
  
  // 类目选项（用于AutoComplete）
  const [categoryOptions, setCategoryOptions] = useState<{value: string, label: string}[]>([])
  
  // 时间范围选择
  const [timeRange, setTimeRange] = useState(7)
  
  // 获取类目选项
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
  
  // 初始加载类目选项
  useEffect(() => {
    fetchCategoryOptions()
  }, [fetchCategoryOptions])
  
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [confirmModalVisible, setConfirmModalVisible] = useState(false)
  const [batchDeleteModalVisible, setBatchDeleteModalVisible] = useState(false)
  const [currentRecord, setCurrentRecord] = useState<SyntheticData | null>(null)
  const [confirmAction, setConfirmAction] = useState<'confirm' | 'reject'>('confirm')
  const [routeResult, setRouteResult] = useState<any>(null)
  const [confirmLoading, setConfirmLoading] = useState(false)
  const [batchDeleteLoading, setBatchDeleteLoading] = useState(false)
  
  const [form] = Form.useForm()

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('page', String(pagination.current))
      params.append('size', String(pagination.pageSize))
      
      if (filters.category_l4) params.append('category_l4', filters.category_l4)
      if (filters.status) params.append('status', filters.status)
      if (filters.keyword) params.append('keyword', filters.keyword)

      const response = await axios.get<ApiResponse<SyntheticData[]>>(
        `${API_BASE_URL}${getApiPath('/draft-pool')}?${params.toString()}`
      )
      
      if (response.data.code === 0) {
        setData(response.data.data || [])
        if (response.data.pagination) {
          setPagination(prev => ({
            ...prev,
            total: response.data.pagination!.total,
          }))
        }
      } else {
        message.error(response.data.message || '获取数据失败')
      }
    } catch (error: any) {
      console.error('Fetch data error:', error)
      message.error(error.response?.data?.message || '获取数据失败，请检查网络连接')
    } finally {
      setLoading(false)
    }
  }, [pagination.current, pagination.pageSize, filters])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // 计算日增量数据
  const dailyData = useMemo(() => {
    return calculateDailyIncrement(data, timeRange)
  }, [data, timeRange])

  // 平滑折线图配置
  const lineConfig = useMemo(() => ({
    data: dailyData,
    xField: 'date',
    yField: 'count',
    smooth: true,
    color: '#fa8c16',
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
      fill: 'l(270) 0:#ffffff 0.5:#ffd8bf 1:#fa8c16',
      opacity: 0.3,
    },
    point: {
      size: 4,
      shape: 'circle',
      style: {
        fill: '#fa8c16',
        stroke: '#fff',
        lineWidth: 2,
      },
    },
    tooltip: {
      showMarkers: true,
    },
  }), [dailyData])

  // 可展开的行内容 - 展示完整信息
  const expandedRowRender = (record: SyntheticData) => {
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
              <CategoryDisplay 
                l1={record.category_l1}
                l2={record.category_l2}
                l3={record.category_l3}
                l4={record.category_l4}
              />
            </div>
          </Col>
          <Col span={8}>
            <Text strong style={{ fontSize: 13 }}>🏷️ 元数据</Text>
            <div style={{ marginTop: 8, fontSize: 12 }}>
              <div>ID: <Text copyable>{record.synthetic_id}</Text></div>
              <div>版本: {record.version}</div>
              <div>所在池: <Tag color={getPoolLocation(record).color}>{getPoolLocation(record).label}</Tag></div>
              <div>状态: <Tag color={statusMap[record.status]?.color}>{statusMap[record.status]?.label}</Tag></div>
            </div>
          </Col>
          <Col span={8}>
            <Text strong style={{ fontSize: 13 }}>⏰ 时间信息</Text>
            <div style={{ marginTop: 8, fontSize: 12 }}>
              <div>创建: {formatBeijingTime(record.created_at)}</div>
              {record.confirmed_at && <div>确认: {formatBeijingTime(record.confirmed_at)}</div>}
              {record.route_batch_id && (
                <div>分流批次: <Tag color="green">{record.route_batch_id}</Tag></div>
              )}
            </div>
          </Col>
        </Row>
      </div>
    )
  }

  // 表格列定义 - 优化Input和GT展示
  const columns: ColumnsType<SyntheticData> = [
    {
      title: 'ID',
      dataIndex: 'synthetic_id',
      key: 'synthetic_id',
      width: 160,
      render: (text: string, record: SyntheticData) => (
        <Space direction="vertical" size={0}>
          <Text copyable style={{ fontSize: 12 }}>{text}</Text>
          {record.route_batch_id && (
            <Tooltip title={`已分流: ${record.route_batch_id}`}>
              <PartitionOutlined style={{ color: '#52c41a', fontSize: 12 }} />
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: '输入 (Input)',
      dataIndex: 'input',
      key: 'input',
      width: showFullContent ? 350 : 200,
      render: (text: string) => <InputDisplay input={text} />,
    },
    {
      title: '标准答案 (GT)',
      dataIndex: 'gt',
      key: 'gt',
      width: showFullContent ? 400 : 250,
      render: (gt: Record<string, any>) => <GTDisplay gt={gt} compact={!showFullContent} />,
    },
    {
      title: '四级类目',
      key: 'category',
      width: 180,
      render: (_: any, record: SyntheticData) => (
        <CategoryDisplay 
          l1={record.category_l1}
          l2={record.category_l2}
          l3={record.category_l3}
          l4={record.category_l4}
        />
      ),
    },

    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      align: 'center',
      render: (status: string) => {
        const { label, color } = statusMap[status] || { label: status, color: 'default' }
        return <Tag color={color}>{label}</Tag>
      },
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 160,
      render: (_: any, record: SyntheticData) => {
        const isDraft = record.status === 'draft'
        
        return (
          <Space size="small">
            <Tooltip title="查看详情">
              <Button 
                type="text" 
                icon={<EyeOutlined />} 
                onClick={() => handleViewDetail(record)}
              />
            </Tooltip>
            
            {isDraft && (
              <Tooltip title="编辑">
                <Button 
                  type="text" 
                  icon={<EditOutlined />} 
                  onClick={() => handleEdit(record)}
                />
              </Tooltip>
            )}
            
            {isDraft && (
              <Tooltip title="确认">
                <Button 
                  type="text" 
                  style={{ color: '#52c41a' }}
                  icon={<CheckOutlined />} 
                  onClick={() => handleConfirmSingle(record, 'confirm')}
                />
              </Tooltip>
            )}
            
            {isDraft && (
              <Tooltip title="拒绝">
                <Button 
                  type="text" 
                  danger
                  icon={<CloseOutlined />} 
                  onClick={() => handleConfirmSingle(record, 'reject')}
                />
              </Tooltip>
            )}
            
            {isDraft && (
              <Tooltip title="删除">
                <Popconfirm
                  title="确定删除这条数据吗？"
                  onConfirm={() => handleDelete(record.synthetic_id)}
                >
                  <Button 
                    type="text" 
                    danger
                    icon={<DeleteOutlined />} 
                  />
                </Popconfirm>
              </Tooltip>
            )}
          </Space>
        )
      },
    },
  ]

  const handleViewDetail = (record: SyntheticData) => {
    setCurrentRecord(record)
    setDetailModalVisible(true)
  }

  const handleEdit = (record: SyntheticData) => {
    setCurrentRecord(record)
    form.setFieldsValue({
      input: record.input,
      gt: JSON.stringify(record.gt, null, 2),
      category_l4: record.category_l4,
    })
    setEditModalVisible(true)
  }

  const handleSaveEdit = async (values: any) => {
    if (!currentRecord) return
    
    try {
      let gt: Record<string, any>
      try {
        gt = JSON.parse(values.gt)
      } catch {
        message.error('GT必须是有效的JSON格式')
        return
      }
      
      const data = {
        input: values.input,
        gt,
        category_l4: values.category_l4,
      }
      
      const response = await axios.put<ApiResponse<SyntheticData>>(
        `${API_BASE_URL}${getApiPath(`/draft-pool/${currentRecord.synthetic_id}`)}`,
        data
      )
      
      if (response.data.code === 0) {
        message.success('保存成功')
        setEditModalVisible(false)
        fetchData()
      } else {
        message.error(response.data.message || '保存失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '保存失败')
    }
  }

  const handleConfirmSingle = (record: SyntheticData, action: 'confirm' | 'reject') => {
    setCurrentRecord(record)
    setConfirmAction(action)
    setRouteResult(null)
    setConfirmModalVisible(true)
  }

  const handleConfirm = async (reason?: string) => {
    if (!currentRecord) return
    
    setConfirmLoading(true)
    try {
      const response = await axios.post<ApiResponse<any>>(
        `${API_BASE_URL}${getApiPath(`/draft-pool/${currentRecord.synthetic_id}/confirm`)}`,
        { action: confirmAction, reason }
      )
      
      if (response.data.code === 0) {
        const result = response.data.data
        
        if (confirmAction === 'confirm' && result.route_result) {
          setRouteResult(result.route_result)
          message.success('确认成功！已自动执行5:5分流')
        } else {
          message.success('已拒绝')
          setConfirmModalVisible(false)
        }
        
        fetchData()
      } else {
        message.error(response.data.message || '操作失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '操作失败')
    } finally {
      setConfirmLoading(false)
    }
  }

  const handleBatchConfirm = async (action: 'confirm' | 'reject') => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择数据')
      return
    }
    
    try {
      const response = await axios.post<ApiResponse<any>>(
        `${API_BASE_URL}${getApiPath('/draft-pool/batch-confirm')}`,
        { 
          synthetic_ids: selectedRowKeys,
          action,
          reason: action === 'reject' ? '批量拒绝' : undefined
        }
      )
      
      if (response.data.code === 0) {
        message.success(`批量${action === 'confirm' ? '确认' : '拒绝'}成功`)
        setSelectedRowKeys([])
        fetchData()
      } else {
        message.error(response.data.message || '批量操作失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '批量操作失败')
    }
  }

  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的数据')
      return
    }
    setBatchDeleteModalVisible(true)
  }

  const handleConfirmBatchDelete = async () => {
    setBatchDeleteLoading(true)
    try {
      // 逐个删除选中的数据
      let successCount = 0
      let failCount = 0
      
      for (const syntheticId of selectedRowKeys) {
        try {
          const response = await axios.delete<ApiResponse<any>>(
            `${API_BASE_URL}${getApiPath(`/draft-pool/${syntheticId}`)}`
          )
          if (response.data.code === 0) {
            successCount++
          } else {
            failCount++
          }
        } catch {
          failCount++
        }
      }
      
      if (successCount > 0) {
        message.success(`成功删除 ${successCount} 条数据`)
        setSelectedRowKeys([])
        fetchData()
      }
      if (failCount > 0) {
        message.error(`${failCount} 条数据删除失败`)
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '批量删除失败')
    } finally {
      setBatchDeleteLoading(false)
      setBatchDeleteModalVisible(false)
    }
  }

  const handleDelete = async (synthetic_id: string) => {
    try {
      const response = await axios.delete<ApiResponse<any>>(
        `${API_BASE_URL}${getApiPath(`/draft-pool/${synthetic_id}`)}`
      )
      
      if (response.data.code === 0) {
        message.success('删除成功')
        fetchData()
      } else {
        message.error(response.data.message || '删除失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.message || '删除失败')
    }
  }

  const handleUpload = async (file: File) => {
    console.log('开始上传文件:', file.name, file.type, file.size)
    
    const formData = new FormData()
    formData.append('file', file)
    
    const uploadUrl = `${API_BASE_URL}${getApiPath("/draft-pool/upload")}`
    console.log('上传URL:', uploadUrl)
    
    try {
      const response = await axios.post<ApiResponse<any>>(
        uploadUrl,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
      
      console.log('上传响应:', response.data)
      
      if (response.data.code === 0) {
        const result = response.data.data
        message.success(
          `上传成功：${result.success}条成功，${result.duplicated}条重复，${result.failed}条失败`
        )
        fetchData()
      } else {
        message.error(response.data.message || '上传失败')
      }
    } catch (error: any) {
      console.error('上传错误:', error)
      console.error('错误响应:', error.response)
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '上传失败'
      message.error(`上传失败: ${errorMsg}`)
    }
    return false
  }

  const handleExport = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.category_l4) params.append('category_l4', filters.category_l4)
      if (filters.status) params.append('status', filters.status)
      
      const response = await axios.get(
        `${API_BASE_URL}${getApiPath('/draft-pool/export/download')}?${params.toString()}`,
        { responseType: 'blob' }
      )
      
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `synthetic_data_${new Date().toISOString().slice(0, 10)}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      message.success('导出成功')
    } catch (error: any) {
      message.error(error.response?.data?.message || '导出失败')
    }
  }

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: readonly React.Key[]) => setSelectedRowKeys([...keys]),
    getCheckboxProps: (record: SyntheticData) => ({
      disabled: record.status !== 'draft',
    }),
  }

  return (
    <div>
      <div className="page-header">
        <h2>初创池</h2>
        <p className="subtitle">AI合成数据的人工审核确认，确认后自动5:5分流至训练池和评测池</p>
      </div>

      <Alert
        message="5:5分流说明"
        description="点击【确认】后，系统会自动按四级类目分组，每组内随机打乱并按5:5比例分割，分别进入训练池（含GT）和评测池（GT隐藏）。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card style={{ height: 180 }}>
            <Statistic
              title="初创池数据量"
              value={pagination.total}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col span={18}>
          <Card 
            style={{ height: 180 }}
            title={
              <Space>
                <RiseOutlined style={{ color: '#fa8c16' }} />
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
        <div className="table-actions" style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
            <Select
              placeholder="状态"
              style={{ width: 120 }}
              value={filters.status}
              onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
              allowClear
              options={[
                { label: '草稿', value: 'draft' },
                { label: '已确认', value: 'confirmed' },
                { label: '已拒绝', value: 'rejected' },
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
          </Space>
          
          <Space wrap>
            <Button 
              icon={showFullContent ? <CompressOutlined /> : <FullscreenOutlined />}
              onClick={() => setShowFullContent(!showFullContent)}
            >
              {showFullContent ? '紧凑视图' : '展开视图'}
            </Button>
            
            <Upload
              accept=".xlsx,.xls,.csv"
              showUploadList={false}
              beforeUpload={handleUpload}
            >
              <Button icon={<UploadOutlined />}>批量上传</Button>
            </Upload>
            
            <Button 
              danger
              disabled={selectedRowKeys.length === 0}
              onClick={() => handleBatchDelete()}
              icon={<DeleteOutlined />}
            >
              批量删除 ({selectedRowKeys.length})
            </Button>
            
            <Button icon={<DownloadOutlined />} onClick={handleExport}>
              导出数据
            </Button>
            
            <Button 
              type="primary" 
              disabled={selectedRowKeys.length === 0}
              onClick={() => handleBatchConfirm('confirm')}
              icon={<PartitionOutlined />}
            >
              批量分流 ({selectedRowKeys.length})
            </Button>
          </Space>
        </div>

        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="synthetic_id"
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

      {/* 编辑弹窗 */}
      <Modal
        title="编辑合成数据"
        open={editModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setEditModalVisible(false)}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveEdit}
        >
          <Form.Item
            label="输入 (Input)"
            name="input"
            rules={[{ required: true, message: '请输入input' }]}
          >
            <Input.TextArea rows={3} />
          </Form.Item>
          
          <Form.Item
            label="标准答案 (GT) - JSON格式"
            name="gt"
            rules={[{ required: true, message: '请输入GT' }]}
          >
            <Input.TextArea rows={6} placeholder='{"材质": "UPVC", "规格": "DN20"}' />
          </Form.Item>
          
          <Form.Item
            label="四级类目"
            name="category_l4"
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title="合成数据详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {currentRecord && (
          <div style={{ padding: 16 }}>
            <Row gutter={24}>
              <Col span={12}>
                <div style={{ marginBottom: 24 }}>
                  <Text strong style={{ fontSize: 16, color: '#1890ff' }}>📝 Input (输入)</Text>
                  <div style={{ 
                    marginTop: 12, 
                    padding: 16, 
                    background: '#e6f7ff', 
                    borderRadius: 8,
                    border: '1px solid #91d5ff'
                  }}>
                    <Text style={{ fontSize: 14 }}>{currentRecord.input}</Text>
                  </div>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: 24 }}>
                  <Text strong style={{ fontSize: 16, color: '#52c41a' }}>✓ GT (标准答案)</Text>
                  <div style={{ marginTop: 12 }}>
                    <GTDisplay gt={currentRecord.gt} />
                  </div>
                </div>
              </Col>
            </Row>
            
            <Divider />
            
            <Descriptions bordered column={2}>
              <Descriptions.Item label="ID" span={2}>{currentRecord.synthetic_id}</Descriptions.Item>
              <Descriptions.Item label="一级类目">{currentRecord.category_l1 || '-'}</Descriptions.Item>
              <Descriptions.Item label="二级类目">{currentRecord.category_l2 || '-'}</Descriptions.Item>
              <Descriptions.Item label="三级类目">{currentRecord.category_l3 || '-'}</Descriptions.Item>
              <Descriptions.Item label="四级类目">{currentRecord.category_l4 || '-'}</Descriptions.Item>
              <Descriptions.Item label="所在池">
                <Tag color={getPoolLocation(currentRecord).color}>
                  {getPoolLocation(currentRecord).label}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusMap[currentRecord.status]?.color}>
                  {statusMap[currentRecord.status]?.label}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">{formatBeijingTime(currentRecord.created_at)}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{formatBeijingTime(currentRecord.updated_at)}</Descriptions.Item>
            </Descriptions>
          </div>
        )}
      </Modal>

      {/* 确认/拒绝弹窗 */}
      <Modal
        title={confirmAction === 'confirm' ? '确认合成数据' : '拒绝合成数据'}
        open={confirmModalVisible}
        onCancel={() => {
          setConfirmModalVisible(false)
          setRouteResult(null)
        }}
        footer={
          routeResult ? (
            <Button onClick={() => {
              setConfirmModalVisible(false)
              setRouteResult(null)
            }}>
              关闭
            </Button>
          ) : (
            <Space>
              <Button onClick={() => setConfirmModalVisible(false)}>取消</Button>
              <Button 
                type={confirmAction === 'confirm' ? 'primary' : 'default'}
                danger={confirmAction === 'reject'}
                onClick={() => handleConfirm()}
                loading={confirmLoading}
              >
                {confirmAction === 'confirm' ? '确认并分流' : '拒绝'}
              </Button>
            </Space>
          )
        }
      >
        {currentRecord && !routeResult && (
          <div>
            <Row gutter={16}>
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong>📝 Input:</Text>
                  <div style={{ 
                    marginTop: 8, 
                    padding: 12, 
                    background: '#f5f5f5', 
                    borderRadius: 4 
                  }}>
                    <Text>{currentRecord.input}</Text>
                  </div>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong>✓ GT:</Text>
                  <div style={{ marginTop: 8 }}>
                    <GTDisplay gt={currentRecord.gt} />
                  </div>
                </div>
              </Col>
            </Row>
            
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="四级类目">{currentRecord.category_l4 || '-'}</Descriptions.Item>
              <Descriptions.Item label="类目路径">{currentRecord.category_path || '-'}</Descriptions.Item>
            </Descriptions>
            
            {confirmAction === 'reject' && (
              <Input.TextArea
                style={{ marginTop: 16 }}
                placeholder="请输入拒绝原因（可选）"
                rows={3}
              />
            )}
            
            {confirmAction === 'confirm' && (
              <Alert
                message="确认后将自动执行5:5分流"
                description="数据将按四级类目分组，每组随机打乱后5:5分割，分别进入训练池和评测池。"
                type="info"
                showIcon
                style={{ marginTop: 16 }}
              />
            )}
          </div>
        )}
        
        {routeResult && (
          <div>
            <Alert
              message="分流成功！"
              type="success"
              showIcon
            />
            <Descriptions bordered column={1} style={{ marginTop: 16 }}>
              <Descriptions.Item label="分流批次">{routeResult.batch_id}</Descriptions.Item>
              <Descriptions.Item label="训练池">{routeResult.training} 条</Descriptions.Item>
              <Descriptions.Item label="评测池">{routeResult.evaluation} 条</Descriptions.Item>
              <Descriptions.Item label="总计">{routeResult.total} 条</Descriptions.Item>
            </Descriptions>
          </div>
        )}
      </Modal>

      {/* 批量删除确认弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ExclamationCircleOutlined style={{ color: '#ff4d4f', fontSize: 22 }} />
            <span>确认批量删除</span>
          </div>
        }
        open={batchDeleteModalVisible}
        onCancel={() => setBatchDeleteModalVisible(false)}
        footer={
          <Space>
            <Button onClick={() => setBatchDeleteModalVisible(false)}>取消</Button>
            <Button 
              type="primary" 
              danger
              onClick={handleConfirmBatchDelete}
              loading={batchDeleteLoading}
            >
              确认删除
            </Button>
          </Space>
        }
      >
        <div style={{ padding: '16px 0' }}>
          <Text style={{ fontSize: 14 }}>
            您确定要删除选中的 <Text strong style={{ color: '#ff4d4f' }}>{selectedRowKeys.length}</Text> 条数据吗？
          </Text>
          <Alert
            message="删除后数据将无法恢复，请谨慎操作！"
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
          <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4, maxHeight: 200, overflow: 'auto' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              待删除的数据ID：
            </Text>
            <div style={{ marginTop: 8 }}>
              {selectedRowKeys.map((id, index) => (
                <Tag key={String(id)} style={{ marginBottom: 4 }}>
                  {index + 1}. {String(id)}
                </Tag>
              ))}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default DraftPool
