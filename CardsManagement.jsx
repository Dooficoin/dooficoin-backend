import { useState, useEffect } from 'react'
import { Sparkles, Search, PlusCircle, Edit, Save, X, Trash2, Image, Palette, Hash, CheckCircle, XCircle } from 'lucide-react'

export function CardsManagement({ token }) {
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [editingCard, setEditingCard] = useState(null)
  const [editFormData, setEditFormData] = useState({
    name: '', description: '', card_series: '', card_number: 1, rarity: 'common',
    available_in_phase: 1, drop_rate: 0.05, image_url: '', background_color: '#FFFFFF', is_active: true
  })
  const [creatingNew, setCreatingNew] = useState(false)

  const cardRarities = ['common', 'rare', 'epic', 'legendary', 'mythic']

  useEffect(() => {
    fetchCards()
  }, [currentPage, searchTerm])

  const fetchCards = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/admin/cards?page=${currentPage}&per_page=10&name=${searchTerm}`,
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
      setCards(data.cards)
      setTotalPages(data.total_pages)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEditClick = (card) => {
    setEditingCard(card.id)
    setEditFormData({
      name: card.name, description: card.description, card_series: card.card_series, card_number: card.card_number,
      rarity: card.rarity, available_in_phase: card.available_in_phase, drop_rate: card.drop_rate,
      image_url: card.image_url, background_color: card.background_color, is_active: card.is_active
    })
  }

  const handleCreateClick = () => {
    setCreatingNew(true)
    setEditFormData({
      name: '', description: '', card_series: '', card_number: 1, rarity: 'common',
      available_in_phase: 1, drop_rate: 0.05, image_url: '', background_color: '#FFFFFF', is_active: true
    })
  }

  const handleCancelEdit = () => {
    setEditingCard(null)
    setCreatingNew(false)
    setEditFormData({
      name: '', description: '', card_series: '', card_number: 1, rarity: 'common',
      available_in_phase: 1, drop_rate: 0.05, image_url: '', background_color: '#FFFFFF', is_active: true
    })
  }

  const handleSave = async (cardId = null) => {
    setLoading(true)
    setError(null)
    try {
      const method = cardId ? 'PUT' : 'POST'
      const url = cardId ? `/api/admin/cards/${cardId}` : '/api/admin/cards'
      
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
      alert(`Carta ${cardId ? 'atualizada' : 'criada'} com sucesso!`)
      fetchCards()
      handleCancelEdit()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao ${cardId ? 'atualizar' : 'criar'} carta: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (cardId) => {
    if (!window.confirm('Tem certeza que deseja deletar esta carta?')) {
      return
    }
    setLoading(true)
    try {
      const response = await fetch(`/api/admin/cards/${cardId}`,
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
      alert('Carta deletada com sucesso!')
      fetchCards()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao deletar carta: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const renderForm = (data, isNew = false) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-purple-500/20 mb-6">
      <h3 className="text-xl font-bold text-white mb-4">{isNew ? 'Criar Nova Carta' : `Editar Carta: ${data.name}`}</h3>
      <form onSubmit={(e) => { e.preventDefault(); handleSave(isNew ? null : editingCard) }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-gray-400 text-sm mb-1">Nome</label>
          <input type="text" name="name" value={data.name} onChange={(e) => setEditFormData({ ...data, name: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Descrição</label>
          <textarea name="description" value={data.description} onChange={(e) => setEditFormData({ ...data, description: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" rows="2"></textarea>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Série da Carta</label>
          <input type="text" name="card_series" value={data.card_series} onChange={(e) => setEditFormData({ ...data, card_series: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Número da Carta</label>
          <input type="number" name="card_number" value={data.card_number} onChange={(e) => setEditFormData({ ...data, card_number: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Raridade</label>
          <select name="rarity" value={data.rarity} onChange={(e) => setEditFormData({ ...data, rarity: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required>
            {cardRarities.map(rarity => <option key={rarity} value={rarity}>{rarity.charAt(0).toUpperCase() + rarity.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Disponível na Fase</label>
          <input type="number" name="available_in_phase" value={data.available_in_phase} onChange={(e) => setEditFormData({ ...data, available_in_phase: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Taxa de Drop</label>
          <input type="number" step="0.01" name="drop_rate" value={data.drop_rate} onChange={(e) => setEditFormData({ ...data, drop_rate: parseFloat(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Cor de Fundo</label>
          <input type="color" name="background_color" value={data.background_color} onChange={(e) => setEditFormData({ ...data, background_color: e.target.value })} className="w-full h-10 px-1 py-1 bg-gray-700 border border-gray-600 rounded-md text-white" />
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
            placeholder="Buscar por nome da carta..."
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
          <span>Nova Carta</span>
        </button>
      </div>

      {creatingNew && renderForm(editFormData, true)}
      {editingCard && renderForm(editFormData)}

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

      {!loading && !error && cards.length === 0 && !creatingNew && (
        <div className="text-center py-12 text-gray-400">
          <Sparkles className="w-16 h-16 mx-auto mb-4" />
          <p>Nenhuma carta encontrada.</p>
        </div>
      )}

      {!loading && !error && cards.length > 0 && !creatingNew && !editingCard && (
        <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden border border-purple-500/20">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Série</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Número</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Raridade</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Fase Disp.</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ativo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {cards.map((card) => (
                <tr key={card.id} className="hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{card.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">{card.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{card.card_series}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{card.card_number}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: card.rarity_color }}>{card.rarity_display}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{card.available_in_phase}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {card.is_active ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEditClick(card)}
                        className="text-blue-500 hover:text-blue-700"
                        title="Editar"
                      >
                        <Edit className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(card.id)}
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

