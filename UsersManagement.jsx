import { useState, useEffect } from 'react'
import { User, Search, Ban, CheckCircle, Edit, Save, X, Trash2, Mail } from 'lucide-react'

export function UsersManagement({ token }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [editingUser, setEditingUser] = useState(null)
  const [editFormData, setEditFormData] = useState({
    username: '',
    email: '',
    is_admin: false,
    is_active: false
  })

  useEffect(() => {
    fetchUsers()
  }, [currentPage, searchTerm])

  const fetchUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/admin/users?page=${currentPage}&per_page=10&username=${searchTerm}`,
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
      setUsers(data.users)
      setTotalPages(data.total_pages)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEditClick = (user) => {
    setEditingUser(user.id)
    setEditFormData({
      username: user.username,
      email: user.email,
      is_admin: user.is_admin,
      is_active: user.is_active
    })
  }

  const handleCancelEdit = () => {
    setEditingUser(null)
    setEditFormData({
      username: '',
      email: '',
      is_admin: false,
      is_active: false
    })
  }

  const handleSaveEdit = async (userId) => {
    setLoading(true)
    try {
      const response = await fetch(`/api/admin/users/${userId}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(editFormData)
        }
      )
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      await response.json()
      alert('Usuário atualizado com sucesso!')
      fetchUsers()
      handleCancelEdit()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao atualizar usuário: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleBanUnban = async (userId, action) => {
    if (!window.confirm(`Tem certeza que deseja ${action === 'ban' ? 'banir' : 'desbanir'} este usuário?`)) {
      return
    }
    setLoading(true)
    try {
      const response = await fetch(`/api/admin/users/${userId}/${action}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      await response.json()
      alert(`Usuário ${action === 'ban' ? 'banido' : 'desbanido'} com sucesso!`)
      fetchUsers()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao ${action === 'ban' ? 'banir' : 'desbanir'} usuário: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Buscar por nome de usuário..."
            className="w-full px-4 py-2 pl-10 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:border-purple-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
        </div>
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

      {!loading && !error && users.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <Users className="w-16 h-16 mx-auto mb-4" />
          <p>Nenhum usuário encontrado.</p>
        </div>
      )}

      {!loading && !error && users.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden border border-purple-500/20">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Usuário</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Admin</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ativo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{user.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {editingUser === user.id ? (
                      <input
                        type="text"
                        name="username"
                        value={editFormData.username}
                        onChange={(e) => setEditFormData({ ...editFormData, username: e.target.value })}
                        className="bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-white"
                      />
                    ) : (
                      <span className="text-white font-medium">{user.username}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {editingUser === user.id ? (
                      <input
                        type="email"
                        name="email"
                        value={editFormData.email}
                        onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
                        className="bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-white"
                      />
                    ) : (
                      <span className="text-gray-400">{user.email}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {editingUser === user.id ? (
                      <input
                        type="checkbox"
                        name="is_admin"
                        checked={editFormData.is_admin}
                        onChange={(e) => setEditFormData({ ...editFormData, is_admin: e.target.checked })}
                        className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded"
                      />
                    ) : (
                      user.is_admin ? <CheckCircle className="w-5 h-5 text-green-500" /> : <X className="w-5 h-5 text-red-500" />
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {editingUser === user.id ? (
                      <input
                        type="checkbox"
                        name="is_active"
                        checked={editFormData.is_active}
                        onChange={(e) => setEditFormData({ ...editFormData, is_active: e.target.checked })}
                        className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded"
                      />
                    ) : (
                      user.is_active ? <CheckCircle className="w-5 h-5 text-green-500" /> : <Ban className="w-5 h-5 text-red-500" />
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {editingUser === user.id ? (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleSaveEdit(user.id)}
                          className="text-green-500 hover:text-green-700"
                          title="Salvar"
                        >
                          <Save className="w-5 h-5" />
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="text-gray-500 hover:text-gray-700"
                          title="Cancelar"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleEditClick(user)}
                          className="text-blue-500 hover:text-blue-700"
                          title="Editar"
                        >
                          <Edit className="w-5 h-5" />
                        </button>
                        {user.is_active ? (
                          <button
                            onClick={() => handleBanUnban(user.id, 'ban')}
                            className="text-red-500 hover:text-red-700"
                            title="Banir"
                          >
                            <Ban className="w-5 h-5" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleBanUnban(user.id, 'unban')}
                            className="text-green-500 hover:text-green-700"
                            title="Desbanir"
                          >
                            <CheckCircle className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                    )}
                  </td>
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


