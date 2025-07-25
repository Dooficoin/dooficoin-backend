import { useState, useEffect } from 'react'
import { Map, Search, PlusCircle, Edit, Save, X, Trash2, Globe, City, Sun, Cloud, CheckCircle, XCircle } from 'lucide-react'

export function ScenariosManagement({ token }) {
  const [scenarios, setScenarios] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [editingScenario, setEditingScenario] = useState(null)
  const [editFormData, setEditFormData] = useState({
    name: '', description: '', country: '', city: '', location_name: '',
    latitude: '', longitude: '', phase_number: 1, scenario_type: 'forest',
    difficulty_level: 1, initial_monsters: 300, monster_increase_percentage: 0.25,
    ambient_color: '#000000', image_url: '', is_active: true
  })
  const [creatingNew, setCreatingNew] = useState(false)

  const scenarioTypes = ['forest', 'desert', 'mountain', 'city', 'ocean', 'volcano', 'space']

  useEffect(() => {
    fetchScenarios()
  }, [currentPage, searchTerm])

  const fetchScenarios = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/admin/scenarios?page=${currentPage}&per_page=10&name=${searchTerm}`,
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
      setScenarios(data.scenarios)
      setTotalPages(data.total_pages)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEditClick = (scenario) => {
    setEditingScenario(scenario.id)
    setEditFormData({
      name: scenario.name, description: scenario.description, country: scenario.country, city: scenario.city, location_name: scenario.location_name,
      latitude: scenario.latitude, longitude: scenario.longitude, phase_number: scenario.phase_number, scenario_type: scenario.scenario_type,
      difficulty_level: scenario.difficulty_level, initial_monsters: scenario.initial_monsters, monster_increase_percentage: scenario.monster_increase_percentage,
      ambient_color: scenario.ambient_color, image_url: scenario.image_url, is_active: scenario.is_active
    })
  }

  const handleCreateClick = () => {
    setCreatingNew(true)
    setEditFormData({
      name: '', description: '', country: '', city: '', location_name: '',
      latitude: '', longitude: '', phase_number: 1, scenario_type: 'forest',
      difficulty_level: 1, initial_monsters: 300, monster_increase_percentage: 0.25,
      ambient_color: '#000000', image_url: '', is_active: true
    })
  }

  const handleCancelEdit = () => {
    setEditingScenario(null)
    setCreatingNew(false)
    setEditFormData({
      name: '', description: '', country: '', city: '', location_name: '',
      latitude: '', longitude: '', phase_number: 1, scenario_type: 'forest',
      difficulty_level: 1, initial_monsters: 300, monster_increase_percentage: 0.25,
      ambient_color: '#000000', image_url: '', is_active: true
    })
  }

  const handleSave = async (scenarioId = null) => {
    setLoading(true)
    setError(null)
    try {
      const method = scenarioId ? 'PUT' : 'POST'
      const url = scenarioId ? `/api/admin/scenarios/${scenarioId}` : '/api/admin/scenarios'
      
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
      alert(`Cenário ${scenarioId ? 'atualizado' : 'criado'} com sucesso!`)
      fetchScenarios()
      handleCancelEdit()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao ${scenarioId ? 'atualizar' : 'criar'} cenário: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (scenarioId) => {
    if (!window.confirm('Tem certeza que deseja deletar este cenário?')) {
      return
    }
    setLoading(true)
    try {
      const response = await fetch(`/api/admin/scenarios/${scenarioId}`,
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
      alert('Cenário deletado com sucesso!')
      fetchScenarios()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao deletar cenário: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const renderForm = (data, isNew = false) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-purple-500/20 mb-6">
      <h3 className="text-xl font-bold text-white mb-4">{isNew ? 'Criar Novo Cenário' : `Editar Cenário: ${data.name}`}</h3>
      <form onSubmit={(e) => { e.preventDefault(); handleSave(isNew ? null : editingScenario) }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-gray-400 text-sm mb-1">Nome</label>
          <input type="text" name="name" value={data.name} onChange={(e) => setEditFormData({ ...data, name: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Descrição</label>
          <textarea name="description" value={data.description} onChange={(e) => setEditFormData({ ...data, description: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" rows="2"></textarea>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">País</label>
          <input type="text" name="country" value={data.country} onChange={(e) => setEditFormData({ ...data, country: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Cidade</label>
          <input type="text" name="city" value={data.city} onChange={(e) => setEditFormData({ ...data, city: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Nome do Local</label>
          <input type="text" name="location_name" value={data.location_name} onChange={(e) => setEditFormData({ ...data, location_name: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Latitude</label>
          <input type="text" name="latitude" value={data.latitude} onChange={(e) => setEditFormData({ ...data, latitude: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Longitude</label>
          <input type="text" name="longitude" value={data.longitude} onChange={(e) => setEditFormData({ ...data, longitude: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Número da Fase</label>
          <input type="number" name="phase_number" value={data.phase_number} onChange={(e) => setEditFormData({ ...data, phase_number: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Tipo de Cenário</label>
          <select name="scenario_type" value={data.scenario_type} onChange={(e) => setEditFormData({ ...data, scenario_type: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required>
            {scenarioTypes.map(type => <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Nível de Dificuldade</label>
          <input type="number" name="difficulty_level" value={data.difficulty_level} onChange={(e) => setEditFormData({ ...data, difficulty_level: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Monstros Iniciais</label>
          <input type="number" name="initial_monsters" value={data.initial_monsters} onChange={(e) => setEditFormData({ ...data, initial_monsters: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Aumento de Monstros (%)</label>
          <input type="number" step="0.01" name="monster_increase_percentage" value={data.monster_increase_percentage} onChange={(e) => setEditFormData({ ...data, monster_increase_percentage: parseFloat(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Cor Ambiente</label>
          <input type="text" name="ambient_color" value={data.ambient_color} onChange={(e) => setEditFormData({ ...data, ambient_color: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
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
            placeholder="Buscar por nome do cenário..."
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
          <span>Novo Cenário</span>
        </button>
      </div>

      {creatingNew && renderForm(editFormData, true)}
      {editingScenario && renderForm(editFormData)}

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

      {!loading && !error && scenarios.length === 0 && !creatingNew && (
        <div className="text-center py-12 text-gray-400">
          <Map className="w-16 h-16 mx-auto mb-4" />
          <p>Nenhum cenário encontrado.</p>
        </div>
      )}

      {!loading && !error && scenarios.length > 0 && !creatingNew && !editingScenario && (
        <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden border border-purple-500/20">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">País</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Cidade</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Fase</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Dificuldade</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ativo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {scenarios.map((scenario) => (
                <tr key={scenario.id} className="hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{scenario.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">{scenario.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{scenario.country}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{scenario.city}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{scenario.phase_number}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{scenario.scenario_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{scenario.difficulty_level}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {scenario.is_active ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEditClick(scenario)}
                        className="text-blue-500 hover:text-blue-700"
                        title="Editar"
                      >
                        <Edit className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(scenario.id)}
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

