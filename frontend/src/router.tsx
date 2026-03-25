import { createBrowserRouter, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Seeds from './pages/Seeds'
import Standards from './pages/Standards'
import Skills from './pages/Skills'
import Synthesis from './pages/Synthesis'
import DraftPool from './pages/DraftPool'
import TrainingPool from './pages/TrainingPool'
import EvaluationPool from './pages/EvaluationPool'
import Datasets from './pages/Datasets'
import Evaluation from './pages/Evaluation'
import Leaderboard from './pages/Leaderboard'
import Reports from './pages/Reports'
import NotFound from './pages/NotFound'

/**
 * Router configuration (AITest compatible)
 * 
 * Auth routes:
 * - /api-auth/*  -> Proxied to company SSO service (handled by vite proxy)
 * - /login       -> Redirect to /api-auth/login
 * 
 * Protected routes: All routes under Layout require authentication
 */
const router = createBrowserRouter([
  // Legacy login route (redirect to SSO auth route)
  {
    path: '/login',
    element: <Navigate to="/api-auth/login" replace />,
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
        path: 'training-pool',
        element: <TrainingPool />,
      },
      {
        path: 'evaluation-pool',
        element: <EvaluationPool />,
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
