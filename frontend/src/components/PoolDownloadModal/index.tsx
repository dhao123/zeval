import { useState, useEffect } from 'react'
import { 
  Modal, 
  Form, 
  InputNumber, 
  TreeSelect,
  Radio,
  Space,
  Typography,
  Alert,
  message,
  Progress,
  Tag
} from 'antd'
import { DownloadOutlined, FileExcelOutlined, FileTextOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Text } = Typography

interface PoolDownloadModalProps {
  open: boolean
  onClose: () => void
  poolType: 'training' | 'evaluation'
  defaultCategory?: string
}

interface CategoryNode {
  title: string
  value: string
  key: string
  children?: CategoryNode[]
}

export function PoolDownloadModal({ 
  open, 
  onClose, 
  poolType,
  defaultCategory 
}: PoolDownloadModalProps) {
  const [form] = Form.useForm()
  const [downloading, setDownloading] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState(0)
  const [categoryTree, setCategoryTree] = useState<CategoryNode[]>([])
  const [totalCount, setTotalCount] = useState(0)

  // 获取类目树
  const fetchCategoryTree = async () => {
    try {
      const response = await axios.get('/api/v1/categories?limit=1000')
      if (response.data.code === 0) {
        const categories = response.data.data.items || []
        // 构建树形结构
        const tree = buildCategoryTree(categories)
        setCategoryTree(tree)
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error)
    }
  }

  // 获取总数
  const fetchTotalCount = async (categoryL4?: string) => {
    try {
      const params = new URLSearchParams()
      if (categoryL4) params.append('category_l4', categoryL4)
      const response = await axios.get(`/api/v1/data-pools/${poolType}?${params.toString()}&page=1&size=1`)
      if (response.data.code === 0) {
        setTotalCount(response.data.pagination?.total || 0)
      }
    } catch (error) {
      console.error('Failed to fetch total count:', error)
    }
  }

  useEffect(() => {
    if (open) {
      fetchCategoryTree()
      fetchTotalCount(defaultCategory)
      form.setFieldsValue({
        category: defaultCategory || undefined,
        limit: 5000,
        format: 'json'
      })
    }
  }, [open, defaultCategory])

  // 构建类目树
  const buildCategoryTree = (categories: any[]): CategoryNode[] => {
    const l1Map = new Map<string, CategoryNode>()
    
    categories.forEach((cat) => {
      const l1Key = cat.l1_name
      if (!l1Map.has(l1Key)) {
        l1Map.set(l1Key, {
          title: cat.l1_name,
          value: cat.l1_name,
          key: `l1-${cat.l1_name}`,
          children: []
        })
      }
      
      const l1Node = l1Map.get(l1Key)!
      let l2Node = l1Node.children?.find(c => c.title === cat.l2_name)
      
      if (!l2Node) {
        l2Node = {
          title: cat.l2_name,
          value: `${cat.l1_name}/${cat.l2_name}`,
          key: `l2-${cat.l1_name}-${cat.l2_name}`,
          children: []
        }
        l1Node.children!.push(l2Node)
      }
      
      let l3Node = l2Node.children?.find(c => c.title === cat.l3_name)
      
      if (!l3Node) {
        l3Node = {
          title: cat.l3_name,
          value: `${cat.l1_name}/${cat.l2_name}/${cat.l3_name}`,
          key: `l3-${cat.l1_name}-${cat.l2_name}-${cat.l3_name}`,
          children: []
        }
        l2Node.children!.push(l3Node)
      }
      
      l3Node.children!.push({
        title: cat.l4_name,
        value: cat.l4_name,
        key: `l4-${cat.l4_name}`
      })
    })
    
    return Array.from(l1Map.values())
  }

  const handleCategoryChange = (value: string) => {
    fetchTotalCount(value)
  }

  const handleDownload = async () => {
    try {
      const values = await form.validateFields()
      setDownloading(true)
      setDownloadProgress(0)

      const params = new URLSearchParams({
        pool_type: poolType,
        format: values.format,
        limit: String(values.limit || 5000),
      })

      // 如果选择了类目，添加到参数
      if (values.category) {
        params.append('category_l4', values.category)
      }

      // 添加随机种子参数，确保随机性
      params.append('random', 'true')

      const response = await axios.get(`/api/v1/datasets/download?${params.toString()}`, {
        responseType: 'blob',
        onDownloadProgress: (progressEvent: any) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setDownloadProgress(progress)
          }
        }
      })

      // 创建下载链接
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      const categoryName = values.category || 'all'
      const timestamp = new Date().toISOString().split('T')[0]
      link.href = url
      link.download = `${poolType}_${categoryName}_${values.limit || 5000}_${timestamp}.${values.format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      message.success('下载完成')
      onClose()
    } catch (error: any) {
      console.error('Download error:', error)
      message.error(error.response?.data?.detail || '下载失败')
    } finally {
      setDownloading(false)
      setDownloadProgress(0)
    }
  }

  const poolName = poolType === 'training' ? '训练集' : '评测集'
  const poolColor = poolType === 'training' ? 'green' : 'blue'

  return (
    <Modal
      title={
        <Space>
          <DownloadOutlined />
          <span>下载{poolName}</span>
          <Tag color={poolColor}>{poolType === 'training' ? 'Training' : 'Evaluation'}</Tag>
        </Space>
      }
      open={open}
      onCancel={onClose}
      onOk={handleDownload}
      confirmLoading={downloading}
      width={600}
      okText={downloading ? '下载中...' : '开始下载'}
      cancelText="取消"
      maskClosable={!downloading}
      closable={!downloading}
    >
      <Alert
        message="下载说明"
        description={
          <>
            <div>• 不选择类目时，默认下载全部类目的数据</div>
            <div>• 不填写数量时，默认下载 5000 条数据</div>
            <div>• 数据将随机抽取，确保样本代表性</div>
            <div>• {poolType === 'training' ? '训练集包含 Input + GT（标准答案）' : '评测集仅包含 Input（GT 隐藏）'}</div>
          </>
        }
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          limit: 5000,
          format: 'json'
        }}
      >
        <Form.Item
          name="category"
          label="选择类目（可选）"
          extra="不选择则下载全部类目数据"
        >
          <TreeSelect
            treeData={categoryTree}
            placeholder="请选择类目（留空表示全部）"
            allowClear
            showSearch
            treeDefaultExpandAll={false}
            treeNodeFilterProp="title"
            onChange={handleCategoryChange}
            dropdownStyle={{ maxHeight: 300 }}
          />
        </Form.Item>

        <Form.Item
          name="limit"
          label="下载数量（可选）"
          extra={`不填写则默认下载 5000 条，当前类目共 ${totalCount} 条数据`}
          rules={[
            { type: 'number', min: 1, max: 100000, message: '数量范围 1-100000' }
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="请输入下载数量，默认 5000"
            min={1}
            max={100000}
            step={1000}

          />
        </Form.Item>

        <Form.Item
          name="format"
          label="文件格式"
          rules={[{ required: true }]}
        >
          <Radio.Group>
            <Space>
              <Radio.Button value="json">
                <Space>
                  <FileTextOutlined />
                  JSON
                </Space>
              </Radio.Button>
              <Radio.Button value="csv">
                <Space>
                  <FileExcelOutlined />
                  CSV
                </Space>
              </Radio.Button>
            </Space>
          </Radio.Group>
        </Form.Item>
      </Form>

      {downloading && (
        <div style={{ marginTop: 16 }}>
          <Text>正在下载...</Text>
          <Progress percent={downloadProgress} status="active" />
        </div>
      )}
    </Modal>
  )
}

export default PoolDownloadModal
