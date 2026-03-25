import { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import styles from './index.module.less'

// API 基础URL（登录不需要使用 request.ts，因为 request.ts 会检查 token）
const API_BASE_URL = '/api/v1'

// 后端直接返回 Token 对象（没有包装在 code/message/data 中）
interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

function Login() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const response = await axios.post<LoginResponse>(
        `${API_BASE_URL}/auth/login`,
        {
          username: values.username,
          password: values.password,
        }
      )

      const data = response.data
      // 后端直接返回 Token 对象（没有包装在 code/message/data 中）
      if (data.access_token) {
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        message.success('登录成功')
        navigate('/dashboard')
      } else {
        message.error('登录失败')
      }
    } catch (error: any) {
      console.error('Login error:', error)
      message.error(error.response?.data?.message || '登录失败，请检查用户名和密码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <Card className={styles.card} title="震坤行 Benchmark 评测平台">
        <Form
          name="login"
          onFinish={handleSubmit}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Login
