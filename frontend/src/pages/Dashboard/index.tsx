import { Card, Row, Col, Statistic } from 'antd'
import {
  DatabaseOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons'

function Dashboard() {
  return (
    <div>
      <div className="page-header">
        <h2>数据看板</h2>
        <p className="subtitle">平台数据概览</p>
      </div>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="种子数据"
              value={1128}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="合成数据"
              value={5640}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="评测任务"
              value={42}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Leaderboard排名"
              value={15}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="近期评测趋势">
            <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
              图表区域
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="数据分布">
            <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>
              图表区域
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
