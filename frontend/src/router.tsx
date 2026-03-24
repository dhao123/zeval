import { createBrowserRouter, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Seeds from './pages/Seeds'
import Standards from './pages/Standards'
import Skills from './pages/Skills'
import Synthesis from './pages/Synthesis'
import DraftPool from './pages/DraftPool'
import Datasets from './pages/Datasets'
import Evaluation from './pages/Evaluation'
import Leaderboard from './pages/Leaderboard'
import Reports from './pages/Reports'
import NotFound from './pages/NotFound'

const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'seeds',
        element: <Seeds />,
      },
      {
        path: 'standards',
        element: <Standards />,
      },
      {
        path: 'skills',
        element: <Skills />,
      },
      {
        path: 'synthesis',
        element: <Synthesis />,
      },
      {
        path: 'draft-pool',
        element: <DraftPool />,
      },
      {
        path: 'datasets',
        element: <Datasets />,
      },
      {
        path: 'evaluation',
        element: <Evaluation />,
      },
      {
        path: 'leaderboard',
        element: <Leaderboard />,
      },
      {
        path: 'reports',
        element: <Reports />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
])

export default router
