import { useState, useEffect } from 'react'
import { Ghost, Search, PlusCircle, Edit, Save, X, Trash2, Heart, Swords, Shield, Zap, Award, DollarSign, Image, CheckCircle, XCircle } from 'lucide-react'

export function MonstersManagement({ token }) {
  const [monsters, setMonsters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [editingMonster, setEditingMonster] = useState(null)
  const [editFormData, setEditFormData] = useState({
    name: '', description: '', monster_type: 'zombie', health: 100, attack: 10,
    defense: 5, speed: 5, xp_reward: 10, dooficoin_reward: '0.00000000000000000000000000000000001',
    image_url: '', is_active: true, scenario_id: null
  })
  const [creatingNew, setCreatingNew] = useState(false)

  const monsterTypes = ['zombie', 'animal', 'robot', 'mutant', 'elemental']

  useEffect(() => {
    fetchMonsters()
  }, [currentPage, searchTerm])

  const fetchMonsters = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/admin/monsters?page=${currentPage}&per_page=10&name=${searchTerm}`,
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
      setMonsters(data.monsters)
      setTotalPages(data.total_pages)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEditClick = (monster) => {
    setEditingMonster(monster.id)
    setEditFormData({
      name: monster.name, description: monster.description, monster_type: monster.monster_type,
      health: monster.health, attack: monster.attack, defense: monster.defense, speed: monster.speed,
      xp_reward: monster.xp_reward, dooficoin_reward: monster.dooficoin_reward,
      image_url: monster.image_url, is_active: monster.is_active, scenario_id: monster.scenario_id
    })
  }

  const handleCreateClick = () => {
    setCreatingNew(true)
    setEditFormData({
      name: '', description: '', monster_type: 'zombie', health: 100, attack: 10,
      defense: 5, speed: 5, xp_reward: 10, dooficoin_reward: '0.00000000000000000000000000000000001',
      image_url: '', is_active: true, scenario_id: null
    })
  }

  const handleCancelEdit = () => {
    setEditingMonster(null)
    setCreatingNew(false)
    setEditFormData({
      name: '', description: '', monster_type: 'zombie', health: 100, attack: 10,
      defense: 5, speed: 5, xp_reward: 10, dooficoin_reward: '0.00000000000000000000000000000000001',
      image_url: '', is_active: true, scenario_id: null
    })
  }

  const handleSave = async (monsterId = null) => {
    setLoading(true)
    setError(null)
    try {
      const method = monsterId ? 'PUT' : 'POST'
      const url = monsterId ? `/api/admin/monsters/${monsterId}` : '/api/admin/monsters'
      
      const response = await fetch(url, {
        method: method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editFormData)
      })
      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.error || `HTTP error! status: ${response.status}`)
      }
      await response.json()
      alert(`Monstro ${monsterId ? 'atualizado' : 'criado'} com sucesso!`)
      fetchMonsters()
      handleCancelEdit()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao ${monsterId ? 'atualizar' : 'criar'} monstro: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (monsterId) => {
    if (!window.confirm('Tem certeza que deseja deletar este monstro?')) {
      return
    }
    setLoading(true)
    try {
      const response = await fetch(`/api/admin/monsters/${monsterId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )
      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.error || `HTTP error! status: ${response.status}`)
      }
      alert('Monstro deletado com sucesso!')
      fetchMonsters()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao deletar monstro: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const renderForm = (data, isNew = false) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-purple-500/20 mb-6">
      <h3 className="text-xl font-bold text-white mb-4">{isNew ? 'Criar Novo Monstro' : `Editar Monstro: ${data.name}`}</h3>
      <form onSubmit={(e) => { e.preventDefault(); handleSave(isNew ? null : editingMonster) }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-gray-400 text-sm mb-1">Nome</label>
          <input type="text" name="name" value={data.name} onChange={(e) => setEditFormData({ ...data, name: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Descrição</label>
          <textarea name="description" value={data.description} onChange={(e) => setEditFormData({ ...data, description: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" rows="2"></textarea>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Tipo de Monstro</label>
          <select name="monster_type" value={data.monster_type} onChange={(e) => setEditFormData({ ...data, monster_type: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required>
            {monsterTypes.map(type => <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Vida</label>
          <input type="number" name="health" value={data.health} onChange={(e) => setEditFormData({ ...data, health: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Ataque</label>
          <input type="number" name="attack" value={data.attack} onChange={(e) => setEditFormData({ ...data, attack: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Defesa</label>
          <input type="number" name="defense" value={data.defense} onChange={(e) => setEditFormData({ ...data, defense: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Velocidade</label>
          <input type="number" name="speed" value={data.speed} onChange={(e) => setEditFormData({ ...data, speed: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Recompensa XP</label>
          <input type="number" name="xp_reward" value={data.xp_reward} onChange={(e) => setEditFormData({ ...data, xp_reward: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Recompensa DoofiCoin</label>
          <input type="text" name="dooficoin_reward" value={data.dooficoin_reward} onChange={(e) => setEditFormData({ ...data, dooficoin_reward: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">ID do Cenário (Opcional)</label>
          <input type="number" name="scenario_id" value={data.scenario_id || ''} onChange={(e) => setEditFormData({ ...data, scenario_id: e.target.value ? parseInt(e.target.value) : null })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div className="md:col-span-2">
          <label className="block text-gray-400 text-sm mb-1">URL da Imagem</label>
          <input type="text" name="image_url" value={data.image_url} onChange={(e) => setEditFormData({ ...data, image_url: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div className="flex items-center space-x-4 md:col-span-2">
          <label className="flex items-center text-gray-400">
            <input type="checkbox" name="is_active" checked={data.is_active} onChange={(e) => setEditFormData({ ...data, is_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
            <span className="ml-2">Ativo</span>
          </label>
        </div>
        <div className="md:col-span-2 flex justify-end space-x-2">
          <button type="button" onClick={handleCancelEdit} className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md flex items-center space-x-2">
            <X size={18} /><span>Cancelar</span>
          </button>
          <button type="submit" disabled={loading} className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md flex items-center space-x-2 disabled:opacity-50">
            <Save size={18} /><span>{loading ? 'Salvando...' : 'Salvar'}</span>
          </button>
        </div>
      </form>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="relative flex-1 mr-4">
          <input
            type="text"
            placeholder="Buscar por nome do monstro..."
            className="w-full px-4 py-2 pl-10 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:border-purple-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
        </div>
        <button
          onClick={handleCreateClick}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md flex items-center space-x-2"
        >
          <PlusCircle size={20} />
          <span>Novo Monstro</span>
        </button>
      </div>

      {creatingNew && renderForm(editFormData, true)}
      {editingMonster && renderForm(editFormData)}

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

      {!loading && !error && monsters.length === 0 && !creatingNew && (
        <div className="text-center py-12 text-gray-400">
          <Ghost className="w-16 h-16 mx-auto mb-4" />
          <p>Nenhum monstro encontrado.</p>
        </div>
      )}

      {!loading && !error && monsters.length > 0 && !creatingNew && !editingMonster && (
        <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden border border-purple-500/20">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Vida</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ataque</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Defesa</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">XP</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">DOOF</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ativo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {monsters.map((monster) => (
                <tr key={monster.id} className="hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{monster.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">{monster.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{monster.monster_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-red-400 flex items-center"><Heart className="w-4 h-4 mr-1" />{monster.health}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-400 flex items-center"><Swords className="w-4 h-4 mr-1" />{monster.attack}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-400 flex items-center"><Shield className="w-4 h-4 mr-1" />{monster.defense}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-400 flex items-center"><Award className="w-4 h-4 mr-1" />{monster.xp_reward}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-400 flex items-center"><DollarSign className="w-4 h-4 mr-1" />{parseFloat(monster.dooficoin_reward).toFixed(12)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {monster.is_active ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEditClick(monster)}
                        className="text-blue-500 hover:text-blue-700"
                        title="Editar"
                      >
                        <Edit className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(monster.id)}
                        className="text-red-500 hover:text-red-700"
                        title="Deletar"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
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

