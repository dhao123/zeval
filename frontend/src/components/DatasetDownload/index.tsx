import { useState } from 'react'
import { 
  Button, 
  Modal, 
  Form, 
  Select, 
  Radio, 
  Progress, 
  message, 
  Space,
  Typography,
  Alert,
  Spin,
  Tag
} from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import axios from '@/utils/request'

const { Text } = Typography

interface DatasetDownloadProps {
  category: string
  buttonText?: string
  buttonType?: 'primary' | 'default' | 'link'
  buttonSize?: 'small' | 'middle' | 'large'
}

interface DatasetInfo {
  category: string
  versions: string[]
  latest_version: string
  formats: string[]
  pools: {
    training?: {
      record_count: number
      file_size: number
      fields: string[]
      updated_at: string
    }
    evaluation?: {
      record_count: number
      file_size: number
      fields: string[]
      updated_at: string
    }
  }
}

export function DatasetDownload({
  category,
  buttonText = '下载数据集',
  buttonType = 'primary',
  buttonSize = 'middle'
}: DatasetDownloadProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState(0)
  const [exporting, setExporting] = useState(false)
  
  const [form] = Form.useForm()

  // Fetch dataset info when modal opens
  const fetchDatasetInfo = async () => {
    setLoading(true)
    try {
      const response: any = await axios.get(`/datasets/info?category_l4=${category}&pool_type=both`)
      if (response.code === 0) {
        setDatasetInfo(response.data)
      } else {
        message.error(response.message || '获取数据集信息失败')
      }
    } catch (error) {
      console.error('Fetch dataset info error:', error)
      message.error('获取数据集信息失败')
    } finally {
      setLoading(false)
    }
  }

  const handleOpen = () => {
    setIsModalOpen(true)
    fetchDatasetInfo()
  }

  const handleClose = () => {
    if (!downloading && !exporting) {
      setIsModalOpen(false)
      setDatasetInfo(null)
      setDownloadProgress(0)
      form.resetFields()
    }
  }

  // Direct download for small files
  const handleDirectDownload = async (values: any) => {
    const { pool_type, format, version } = values
    
    setDownloading(true)
    setDownloadProgress(0)
    
    try {
      const params = new URLSearchParams({
        category_l4: category,
        pool_type,
        format,
        version: version || datasetInfo?.latest_version || 'v1.0.0'
      })
      
      const response = await axios.get(`/datasets/download?${params.toString()}`, {
        responseType: 'blob',
        onDownloadProgress: (progressEvent: any) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setDownloadProgress(progress)
          }
        }
      })
      
      // Create download link
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${category}_${pool_type}_${version || 'latest'}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      message.success('下载完成')
      handleClose()
    } catch (error: any) {
      console.error('Download error:', error)
      message.error(error.response?.data?.detail || '下载失败')
    } finally {
      setDownloading(false)
      setDownloadProgress(0)
    }
  }

  // Async export for large files
  const handleAsyncExport = async (values: any) => {
    const { pool_type, format, version } = values
    
    setExporting(true)
    
    try {
      const response: any = await axios.post('/datasets/export', {
        category_l4: category,
        pool_type,
        format,
        version: version || datasetInfo?.latest_version
      })
      
      if (response.code === 0) {
        // Export task created
        message.success('导出任务已创建，请稍候')
        pollExportStatus(response.data.task_id)
      } else {
        message.error(response.message || '创建导出任务失败')
        setExporting(false)
      }
    } catch (error) {
      console.error('Export error:', error)
      message.error('创建导出任务失败')
      setExporting(false)
    }
  }

  // Poll export task status
  const pollExportStatus = async (taskId: string) => {
    const poll = async () => {
      try {
        const response: any = await axios.get(`/datasets/export/${taskId}/status`)
        
        if (response.code === 0) {
          const { status, progress } = response.data
          
          setDownloadProgress(progress)
          
          if (status === 'completed') {
            // Download the file
            const fileResponse = await axios.get(`/datasets/export/${taskId}/download`, {
              responseType: 'blob'
            })
            
            const blob = new Blob([fileResponse.data])
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = `${category}_exported.${form.getFieldValue('format')}`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
            
            message.success('导出完成')
            setExporting(false)
            handleClose()
          } else if (status === 'failed') {
            message.error('导出失败')
            setExporting(false)
          } else {
            setTimeout(() => poll(), 2000)
          }
        }
      } catch (error) {
        console.error('Poll status error:', error)
        setTimeout(() => poll(), 5000)
      }
    }
    
    poll()
  }

  // Smart download: auto-detect file size and choose method
  const handleDownload = async () => {
    try {
      const values = await form.validateFields()
      const { pool_type, format } = values
      
      // Get pool info to check file size
      const poolInfo = datasetInfo?.pools?.[pool_type as keyof typeof datasetInfo.pools]
      const estimatedSize = poolInfo?.file_size || 0
      
      // Parquet format always uses async export
      if (format === 'parquet') {
        handleAsyncExport(values)
        return
      }
      
      // Large files (>100MB) use async export
      if (estimatedSize > 100 * 1024 * 1024) {
        Modal.confirm({
          title: '文件较大',
          content: `预计文件大小为 ${formatFileSize(estimatedSize)}，建议使用后台导出功能。导出完成后将自动下载。`,
          okText: '后台导出',
          cancelText: '直接下载',
          onOk: () => handleAsyncExport(values),
          onCancel: () => handleDirectDownload(values)
        })
        return
      }
      
      // Small files use direct download
      handleDirectDownload(values)
    } catch (error) {
      console.error('Form validation error:', error)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <>
      <Button 
        type={buttonType}
        size={buttonSize}
        icon={<DownloadOutlined />}
        onClick={handleOpen}
      >
        {buttonText}
      </Button>

      <Modal
        title="下载数据集"
        open={isModalOpen}
        onCancel={handleClose}
        width={600}
        footer={null}
        maskClosable={!downloading && !exporting}
        closable={!downloading && !exporting}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <p>加载数据集信息...</p>
          </div>
        ) : datasetInfo ? (
          <>
            <Alert
              message="数据集说明"
              description={
                <>
                  <Text>训练集：包含 Input 和 GT（标准答案）</Text>
                  <br />
                  <Text>评测集：仅包含 Input（GT 隐藏，用于公平评测）</Text>
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
                pool_type: 'training',
                format: 'json',
                version: datasetInfo.latest_version
              }}
            >
              <Form.Item
                name="pool_type"
                label="选择数据集"
                rules={[{ required: true }]}
              >
                <Radio.Group>
                  <Space direction="vertical">
                    <Radio value="training">
                      <Space>
                        <Text strong>训练集</Text>
                        <Text type="secondary">
                          ({datasetInfo.pools?.training?.record_count || 0} 条, {' '}
                          {formatFileSize(datasetInfo.pools?.training?.file_size || 0)})
                        </Text>
                      </Space>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        包含字段: {datasetInfo.pools?.training?.fields?.join(', ')}
                      </Text>
                    </Radio>
                    <Radio value="evaluation">
                      <Space>
                        <Text strong>评测集</Text>
                        <Text type="secondary">
                          ({datasetInfo.pools?.evaluation?.record_count || 0} 条, {' '}
                          {formatFileSize(datasetInfo.pools?.evaluation?.file_size || 0)})
                        </Text>
                      </Space>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        包含字段: {datasetInfo.pools?.evaluation?.fields?.join(', ')}
                      </Text>
                    </Radio>
                  </Space>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                name="format"
                label="文件格式"
                rules={[{ required: true }]}
                extra="Parquet格式适合大数据量分析，将自动使用后台导出"
              >
                <Radio.Group>
                  <Radio.Button value="json">JSON</Radio.Button>
                  <Radio.Button value="csv">CSV</Radio.Button>
                  <Radio.Button value="parquet">Parquet</Radio.Button>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                name="version"
                label="版本"
                rules={[{ required: true }]}
              >
                <Select style={{ width: 200 }}>
                  {datasetInfo.versions.map((v: string) => (
                    <Select.Option key={v} value={v}>
                      {v} {v === datasetInfo.latest_version && <Tag color="blue" style={{ marginLeft: 8 }}>最新</Tag>}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              {(downloading || exporting) && (
                <div style={{ marginBottom: 16 }}>
                  <Text>
                    {downloading ? '正在下载...' : '正在导出...'}
                  </Text>
                  <Progress percent={downloadProgress} status="active" />
                </div>
              )}

              <Form.Item>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<DownloadOutlined />}
                    onClick={handleDownload}
                    loading={downloading || exporting}
                    disabled={downloading || exporting}
                  >
                    {downloading ? '下载中' : exporting ? '导出中' : '开始下载'}
                  </Button>
                  <Button onClick={handleClose} disabled={downloading || exporting}>
                    取消
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </>
        ) : (
          <Alert
            message="无法获取数据集信息"
            description="请检查网络连接或稍后重试"
            type="error"
          />
        )}
      </Modal>
    </>
  )
}

export default DatasetDownload
