import { Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import ChatPage from './components/chat/ChatPage'
import PropertiesPage from './components/domain/PropertiesPage'
import TenantsPage from './components/domain/TenantsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<ChatPage />} />
        <Route path="/chat/:sessionId" element={<ChatPage />} />
        <Route path="/properties" element={<PropertiesPage />} />
        <Route path="/tenants" element={<TenantsPage />} />
      </Route>
    </Routes>
  )
}
