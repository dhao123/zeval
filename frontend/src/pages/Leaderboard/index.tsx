import { Card, Table, Select, Tag, Button, Row, Col } from 'antd'
import { TrophyOutlined, FilterOutlined } from '@ant-design/icons'

const columns = [
  {
    title: '排名',
    dataIndex: 'rank',
    key: 'rank',
    width: 80,
    render: (rank: number) => {
      let color = ''
      if (rank === 1) color = '#FFD700'
      else if (rank === 2) color = '#C0C0C0'
      else if (rank === 3) color = '#CD7F32'
      
      return (
        <span style={{ 
          fontSize: 18, 
          fontWeight: 'bold',
          color: color || 'inherit'
        }}>
          {rank <= 3 && <TrophyOutlined style={{ marginRight: 4 }} />}
          {rank}
        </span>
      )
    },
  },
  {
    title: '模型版本',
    dataIndex: 'model_version',
    key: 'model_version',
  },
  {
    title: 'Prompt版本',
    dataIndex: 'prompt_version',
    key: 'prompt_version',
  },
  {
    title: 'RAG版本',
    dataIndex: 'rag_version',
    key: 'rag_version',
  },
  {
    title: 'Skill版本',
    dataIndex: 'skill_version',
    key: 'skill_version',
  },
  {
    title: '数据版本',
    dataIndex: 'data_version',
    key: 'data_version',
  },
  {
    title: '综合得分',
    dataIndex: 'score',
    key: 'score',
    render: (score: number) => (
      <Tag color={score >= 0.9 ? 'green' : score >= 0.8 ? 'blue' : 'orange'}>
        {(score * 100).toFixed(2)}%
      </Tag>
    ),
  },
]

const mockData = [
  {
    id: 1,
    rank: 1,
    model_version: 'gpt-4o-2024-01',
    prompt_version: 'v2.1',
    rag_version: 'v1.0',
    skill_version: 'v3.0',
    data_version: 'eval_set_001',
    score: 0.9234,
  },
  {
    id: 2,
    rank: 2,
    model_version: 'qwen3-plus',
    prompt_version: 'v2.0',
    rag_version: 'v1.0',
    skill_version: 'v3.0',
    data_version: 'eval_set_001',
    score: 0.8912,
  },
  {
    id: 3,
    rank: 3,
    model_version: 'gemini-pro',
    prompt_version: 'v1.5',
    rag_version: 'v1.0',
    skill_version: 'v3.0',
    data_version: 'eval_set_001',
    score: 0.8567,
  },
]

function Leaderboard() {
  return (
    <div>
      <div className="page-header">
        <h2>Leaderboard 排名</h2>
        <p className="subtitle">五维版本体系排名：Model/Prompt/RAG/Skill/Data</p>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={4}>
            <Select
              placeholder="Model版本"
              style={{ width: '100%' }}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="Prompt版本"
              style={{ width: '100%' }}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="RAG版本"
              style={{ width: '100%' }}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="Skill版本"
              style={{ width: '100%' }}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="数据版本"
              style={{ width: '100%' }}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Button icon={<FilterOutlined />} block>
              筛选
            </Button>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={mockData}
          rowKey="id"
        />
      </Card>
    </div>
  )
}

export default Leaderboard
