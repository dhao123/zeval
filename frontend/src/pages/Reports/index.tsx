import { Card, Tabs, Row, Col, Statistic, Progress, Table, Tag, Button, Space } from 'antd'
import { DownloadOutlined, FileTextOutlined, BarChartOutlined } from '@ant-design/icons'

const { TabPane } = Tabs

const fieldAccuracyColumns = [
  {
    title: '字段名',
    dataIndex: 'field',
    key: 'field',
  },
  {
    title: '准确率',
    dataIndex: 'accuracy',
    key: 'accuracy',
    render: (acc: number) => (
      <Progress percent={Math.round(acc * 100)} size="small" />
    ),
  },
  {
    title: '正确数/总数',
    dataIndex: 'counts',
    key: 'counts',
  },
]

const fieldAccuracyData = [
  { key: '1', field: '材质', accuracy: 0.95, counts: '950/1000' },
  { key: '2', field: '规格', accuracy: 0.92, counts: '920/1000' },
  { key: '3', field: '压力等级', accuracy: 0.88, counts: '880/1000' },
  { key: '4', field: '用途', accuracy: 0.85, counts: '850/1000' },
]

const badcaseColumns = [
  {
    title: 'Case ID',
    dataIndex: 'case_id',
    key: 'case_id',
  },
  {
    title: '输入',
    dataIndex: 'input',
    key: 'input',
    ellipsis: true,
  },
  {
    title: '预测结果',
    dataIndex: 'prediction',
    key: 'prediction',
  },
  {
    title: '标准答案',
    dataIndex: 'ground_truth',
    key: 'ground_truth',
  },
  {
    title: '错误类型',
    dataIndex: 'error_type',
    key: 'error_type',
    render: (type: string) => <Tag color="red">{type}</Tag>,
  },
]

const badcaseData = [
  {
    key: '1',
    case_id: 'case_001',
    input: 'UPVC管 DN20 PN2.5',
    prediction: '{"材质": "PVC", "规格": "DN20"}',
    ground_truth: '{"材质": "UPVC", "规格": "DN20", "压力": "PN2.5"}',
    error_type: '字段缺失',
  },
]

function Reports() {
  return (
    <div>
      <div className="page-header">
        <h2>评测报告</h2>
        <p className="subtitle">多维度评测分析和可视化</p>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title="综合得分"
                value={85.67}
                suffix="%"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="准确率 (Accuracy)"
                value={85.67}
                suffix="%"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="精确率 (Precision)"
                value={87.23}
                suffix="%"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="召回率 (Recall)"
                value={84.12}
                suffix="%"
              />
            </Card>
          </Col>
        </Row>
      </Card>

      <Card
        title="详细报告"
        extra={
          <Space>
            <Button icon={<FileTextOutlined />}>导出PDF</Button>
            <Button icon={<DownloadOutlined />}>导出Excel</Button>
          </Space>
        }
      >
        <Tabs defaultActiveKey="1">
          <TabPane tab="总体概览" key="1">
            <Row gutter={16}>
              <Col span={12}>
                <Card title="得分趋势">
                  <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                    得分趋势图表
                  </div>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="错误归因">
                  <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                    错误归因饼图
                  </div>
                </Card>
              </Col>
            </Row>
          </TabPane>
          
          <TabPane tab="属性分析" key="2">
            <Card title="各字段准确率">
              <Table
                columns={fieldAccuracyColumns}
                dataSource={fieldAccuracyData}
                pagination={false}
              />
            </Card>
          </TabPane>
          
          <TabPane tab="Badcase分析" key="3">
            <Card title="典型错误Case">
              <Table
                columns={badcaseColumns}
                dataSource={badcaseData}
              />
            </Card>
          </TabPane>
          
          <TabPane tab="趋势分析" key="4">
            <Card title="历史得分变化">
              <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
                历史趋势折线图
              </div>
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default Reports
