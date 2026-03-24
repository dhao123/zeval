import { Card, Button, Select, Radio, Alert, Descriptions, Table } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'

const statsColumns = [
  {
    title: '类目',
    dataIndex: 'category',
    key: 'category',
  },
  {
    title: '训练集',
    dataIndex: 'train',
    key: 'train',
  },
  {
    title: '评测集',
    dataIndex: 'eval',
    key: 'eval',
  },
  {
    title: '总计',
    dataIndex: 'total',
    key: 'total',
  },
]

const statsData = [
  { key: '1', category: '管材', train: 500, eval: 500, total: 1000 },
  { key: '2', category: '阀门', train: 300, eval: 300, total: 600 },
  { key: '3', category: '管件', train: 200, eval: 200, total: 400 },
]

function Datasets() {
  return (
    <div>
      <div className="page-header">
        <h2>数据集下载</h2>
        <p className="subtitle">下载训练集(含GT)和评测集(仅Input)</p>
      </div>

      <Card title="数据分布概览" style={{ marginBottom: 24 }}>
        <Table
          columns={statsColumns}
          dataSource={statsData}
          pagination={false}
          summary={() => (
            <Table.Summary.Row>
              <Table.Summary.Cell index={0}><strong>总计</strong></Table.Summary.Cell>
              <Table.Summary.Cell index={1}><strong>1000</strong></Table.Summary.Cell>
              <Table.Summary.Cell index={2}><strong>1000</strong></Table.Summary.Cell>
              <Table.Summary.Cell index={3}><strong>2000</strong></Table.Summary.Cell>
            </Table.Summary.Row>
          )}
        />
      </Card>

      <Card title="下载数据集">
        <Alert
          message="数据可见性说明"
          description="训练集包含Input和GT(标准答案)，评测集仅包含Input，GT对普通用户不可见。"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Descriptions bordered column={1}>
          <Descriptions.Item label="数据集类型">
            <Radio.Group defaultValue="training">
              <Radio.Button value="training">训练集 (含GT)</Radio.Button>
              <Radio.Button value="evaluation">评测集 (仅Input)</Radio.Button>
            </Radio.Group>
          </Descriptions.Item>
          
          <Descriptions.Item label="类目筛选">
            <Select
              placeholder="选择类目（默认全部）"
              style={{ width: 300 }}
              allowClear
              options={[
                { label: '全部类目', value: 'all' },
                { label: '管材', value: '管材' },
                { label: '阀门', value: '阀门' },
                { label: '管件', value: '管件' },
              ]}
            />
          </Descriptions.Item>
          
          <Descriptions.Item label="导出格式">
            <Radio.Group defaultValue="excel">
              <Radio.Button value="excel">Excel</Radio.Button>
              <Radio.Button value="json">JSON</Radio.Button>
              <Radio.Button value="csv">CSV</Radio.Button>
            </Radio.Group>
          </Descriptions.Item>
        </Descriptions>

        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <Button type="primary" size="large" icon={<DownloadOutlined />}>
            下载数据集
          </Button>
        </div>
      </Card>
    </div>
  )
}

export default Datasets
