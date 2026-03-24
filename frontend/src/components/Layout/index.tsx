import { useState } from 'react'
import { Layout as AntLayout, Menu, Avatar, Dropdown, Button } from 'antd'
import {
  DashboardOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  ToolOutlined,
  ExperimentOutlined,
  CheckCircleOutlined,
  BarChartOutlined,
  TrophyOutlined,
  FileSearchOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  PartitionOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content } = AntLayout

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '数据看板',
  },
  {
    key: 'data-management',
    icon: <DatabaseOutlined />,
    label: '数据管理',
    children: [
      { key: '/seeds', icon: <FileTextOutlined />, label: '种子管理' },
      { key: '/standards', icon: <FileTextOutlined />, label: '国标管理' },
      { key: '/skills', icon: <ToolOutlined />, label: '规则管理' },
    ],
  },
  {
    key: 'synthesis',
    icon: <ExperimentOutlined />,
    label: '数据合成',
    children: [
      { key: '/synthesis', icon: <ExperimentOutlined />, label: '合成任务' },
    ],
  },
  {
    key: 'data-pools',
    icon: <PartitionOutlined />,
    label: '数据池',
    children: [
      { key: '/draft-pool', icon: <CheckCircleOutlined />, label: '初创池' },
      { key: '/training-pool', icon: <DatabaseOutlined />, label: '训练池' },
      { key: '/evaluation-pool', icon: <BarChartOutlined />, label: '评测池' },
    ],
  },
  {
    key: 'evaluation',
    icon: <BarChartOutlined />,
    label: '评测',
    children: [
      { key: '/evaluation', icon: <BarChartOutlined />, label: '评测任务' },
      { key: '/leaderboard', icon: <TrophyOutlined />, label: 'Leaderboard' },
      { key: '/reports', icon: <FileSearchOutlined />, label: '评测报告' },
    ],
  },
]

const userMenuItems = [
  {
    key: 'profile',
    icon: <UserOutlined />,
    label: '个人中心',
  },
  {
    key: 'logout',
    icon: <LogoutOutlined />,
    label: '退出登录',
  },
]

function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      navigate('/login')
    }
  }

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      {/* 左侧侧边栏 - 可收缩 */}
      <Sider 
        width={240} 
        theme="dark"
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        trigger={null}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
        }}
      >
        {/* Logo区域 */}
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: collapsed ? 'center' : 'center',
          color: '#fff',
          fontSize: collapsed ? 14 : 18,
          fontWeight: 'bold',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          padding: collapsed ? '0 8px' : '0 16px',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {collapsed ? 'ZKH' : 'ZKH Benchmark'}
        </div>
        
        {/* 菜单 */}
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
          inlineCollapsed={collapsed}
        />
      </Sider>

      {/* 右侧内容区域 */}
      <AntLayout style={{ marginLeft: collapsed ? 80 : 240, transition: 'all 0.2s' }}>
        {/* 固定Header */}
        <Header 
          style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            padding: '0 24px',
            background: '#fff',
            boxShadow: '0 1px 4px rgba(0,21,41,0.08)',
            position: 'fixed',
            top: 0,
            right: 0,
            left: collapsed ? 80 : 240,
            zIndex: 99,
            transition: 'all 0.2s',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* 收缩按钮 */}
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{ fontSize: 16 }}
            />
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 500 }}>
              震坤行 Benchmark 评测平台
            </h1>
          </div>
          
          <Dropdown
            menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
            placement="bottomRight"
          >
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>管理员</span>
            </div>
          </Dropdown>
        </Header>

        {/* 内容区域 - 需要padding-top避开固定Header */}
        <Content 
          style={{ 
            margin: '88px 24px 24px', 
            padding: 24, 
            background: '#fff', 
            borderRadius: 4,
            minHeight: 'calc(100vh - 112px)',
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
