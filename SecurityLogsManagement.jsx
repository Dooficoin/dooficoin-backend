import { useState, useEffect } from 'react'
import { Shield, Search, AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-react'

export function SecurityLogsManagement({ token }) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')

  useEffect(() => {
    fetchLogs()
  }, [currentPage, searchTerm, filterType])

  const fetchLogs = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/admin/security-logs?page=${currentPage}&per_page=10&search=${searchTerm}&type=${filterType}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setLogs(data.logs)
      setTotalPages(data.total_pages)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const getLogIcon = (type) => {
    switch (type) {
      case 'fraud': return <AlertTriangle className="w-5 h-5 text-red-500" />
      case 'login_attempt': return <Info className="w-5 h-5 text-blue-500" />
      case 'suspicious_activity': return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      default: return <Info className="w-5 h-5 text-gray-500" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Buscar por mensagem ou usuário..."
            className="w-full px-4 py-2 pl-10 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:border-purple-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:border-purple-500"
        >
          <option value="all">Todos os Tipos</option>
          <option value="fraud">Fraude</option>
          <option value="login_attempt">Tentativa de Login</option>
          <option value="suspicious_activity">Atividade Suspeita</option>
        </select>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-900/30 border border-red-500 text-red-300 p-4 rounded-md">
          <p>Erro: {error}</p>
        </div>
      )}

      {!loading && !error && logs.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <Shield className="w-16 h-16 mx-auto mb-4" />
          <p>Nenhum log de segurança encontrado.</p>
        </div>
      )}

      {!loading && !error && logs.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden border border-purple-500/20">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Usuário ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Mensagem</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">IP</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Timestamp</th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{log.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm flex items-center space-x-2">
                    {getLogIcon(log.log_type)}
                    <span className="capitalize">{log.log_type.replace('_', ' ')}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{log.user_id || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{log.message}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{log.ip_address || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{new Date(log.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="px-6 py-4 bg-gray-700 flex items-center justify-between">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1 || loading}
              className="px-4 py-2 bg-purple-600 text-white rounded-md disabled:opacity-50"
            >
              Anterior
            </button>
            <span className="text-gray-300">Página {currentPage} de {totalPages}</span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages || loading}
              className="px-4 py-2 bg-purple-600 text-white rounded-md disabled:opacity-50"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  )
}


