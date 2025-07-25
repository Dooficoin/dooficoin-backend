import { useState, useEffect } from 'react'
import { Package, Search, PlusCircle, Edit, Save, X, Trash2, Image, DollarSign, Tag, Layers, Scale, Droplet, Maximize2, Hash, CheckCircle, XCircle } from 'lucide-react'

export function ItemsManagement({ token }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [editingItem, setEditingItem] = useState(null)
  const [editFormData, setEditFormData] = useState({
    name: '', description: '', item_type: 'weapon', rarity: 'common',
    base_price: '0', current_price: '0', required_level: 1, required_phase: 1,
    is_tradeable: true, is_sellable: true, attributes: '{}', drop_rate: 0.1,
    max_stack: 1, image_url: '', is_active: true
  })
  const [creatingNew, setCreatingNew] = useState(false)

  const itemTypes = ['weapon', 'armor', 'accessory', 'collectible', 'consumable', 'special']
  const itemRarities = ['common', 'rare', 'epic', 'legendary', 'mythic']

  useEffect(() => {
    fetchItems()
  }, [currentPage, searchTerm])

  const fetchItems = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/admin/items?page=${currentPage}&per_page=10&name=${searchTerm}`,
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
      setItems(data.items)
      setTotalPages(data.total_pages)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEditClick = (item) => {
    setEditingItem(item.id)
    setEditFormData({
      name: item.name, description: item.description, item_type: item.item_type,
      rarity: item.rarity, base_price: item.base_price, current_price: item.current_price,
      required_level: item.required_level, required_phase: item.required_phase,
      is_tradeable: item.is_tradeable, is_sellable: item.is_sellable,
      attributes: JSON.stringify(item.attributes || {}), drop_rate: item.drop_rate,
      max_stack: item.max_stack, image_url: item.image_url, is_active: item.is_active
    })
  }

  const handleCreateClick = () => {
    setCreatingNew(true)
    setEditFormData({
      name: '', description: '', item_type: 'weapon', rarity: 'common',
      base_price: '0', current_price: '0', required_level: 1, required_phase: 1,
      is_tradeable: true, is_sellable: true, attributes: '{}', drop_rate: 0.1,
      max_stack: 1, image_url: '', is_active: true
    })
  }

  const handleCancelEdit = () => {
    setEditingItem(null)
    setCreatingNew(false)
    setEditFormData({
      name: '', description: '', item_type: 'weapon', rarity: 'common',
      base_price: '0', current_price: '0', required_level: 1, required_phase: 1,
      is_tradeable: true, is_sellable: true, attributes: '{}', drop_rate: 0.1,
      max_stack: 1, image_url: '', is_active: true
    })
  }

  const handleSave = async (itemId = null) => {
    setLoading(true)
    setError(null)
    try {
      const method = itemId ? 'PUT' : 'POST'
      const url = itemId ? `/api/admin/items/${itemId}` : '/api/admin/items'
      
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
      alert(`Item ${itemId ? 'atualizado' : 'criado'} com sucesso!`)
      fetchItems()
      handleCancelEdit()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao ${itemId ? 'atualizar' : 'criar'} item: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (itemId) => {
    if (!window.confirm('Tem certeza que deseja deletar este item?')) {
      return
    }
    setLoading(true)
    try {
      const response = await fetch(`/api/admin/items/${itemId}`,
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
      alert('Item deletado com sucesso!')
      fetchItems()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao deletar item: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const renderForm = (data, isNew = false) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-purple-500/20 mb-6">
      <h3 className="text-xl font-bold text-white mb-4">{isNew ? 'Criar Novo Item' : `Editar Item: ${data.name}`}</h3>
      <form onSubmit={(e) => { e.preventDefault(); handleSave(isNew ? null : editingItem) }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-gray-400 text-sm mb-1">Nome</label>
          <input type="text" name="name" value={data.name} onChange={(e) => setEditFormData({ ...data, name: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Descrição</label>
          <textarea name="description" value={data.description} onChange={(e) => setEditFormData({ ...data, description: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" rows="2"></textarea>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Tipo</label>
          <select name="item_type" value={data.item_type} onChange={(e) => setEditFormData({ ...data, item_type: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required>
            {itemTypes.map(type => <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Raridade</label>
          <select name="rarity" value={data.rarity} onChange={(e) => setEditFormData({ ...data, rarity: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required>
            {itemRarities.map(rarity => <option key={rarity} value={rarity}>{rarity.charAt(0).toUpperCase() + rarity.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Preço Base</label>
          <input type="text" name="base_price" value={data.base_price} onChange={(e) => setEditFormData({ ...data, base_price: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Preço Atual</label>
          <input type="text" name="current_price" value={data.current_price} onChange={(e) => setEditFormData({ ...data, current_price: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Nível Requerido</label>
          <input type="number" name="required_level" value={data.required_level} onChange={(e) => setEditFormData({ ...data, required_level: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Fase Requerida</label>
          <input type="number" name="required_phase" value={data.required_phase} onChange={(e) => setEditFormData({ ...data, required_phase: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div className="md:col-span-2">
          <label className="block text-gray-400 text-sm mb-1">Atributos (JSON)</label>
          <textarea name="attributes" value={data.attributes} onChange={(e) => setEditFormData({ ...data, attributes: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" rows="3"></textarea>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Taxa de Drop</label>
          <input type="number" step="0.01" name="drop_rate" value={data.drop_rate} onChange={(e) => setEditFormData({ ...data, drop_rate: parseFloat(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Max Stack</label>
          <input type="number" name="max_stack" value={data.max_stack} onChange={(e) => setEditFormData({ ...data, max_stack: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div className="md:col-span-2">
          <label className="block text-gray-400 text-sm mb-1">URL da Imagem</label>
          <input type="text" name="image_url" value={data.image_url} onChange={(e) => setEditFormData({ ...data, image_url: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
        </div>
        <div className="flex items-center space-x-4 md:col-span-2">
          <label className="flex items-center text-gray-400">
            <input type="checkbox" name="is_tradeable" checked={data.is_tradeable} onChange={(e) => setEditFormData({ ...data, is_tradeable: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
            <span className="ml-2">Negociável</span>
          </label>
          <label className="flex items-center text-gray-400">
            <input type="checkbox" name="is_sellable" checked={data.is_sellable} onChange={(e) => setEditFormData({ ...data, is_sellable: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
            <span className="ml-2">Vendável</span>
          </label>
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
            placeholder="Buscar por nome do item..."
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
          <span>Novo Item</span>
        </button>
      </div>

      {creatingNew && renderForm(editFormData, true)}
      {editingItem && renderForm(editFormData)}

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

      {!loading && !error && items.length === 0 && !creatingNew && (
        <div className="text-center py-12 text-gray-400">
          <Package className="w-16 h-16 mx-auto mb-4" />
          <p>Nenhum item encontrado.</p>
        </div>
      )}

      {!loading && !error && items.length > 0 && !creatingNew && !editingItem && (
        <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden border border-purple-500/20">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Raridade</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Preço</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Nível Req.</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Fase Req.</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ativo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-700">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{item.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">{item.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{item.item_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: item.rarity_color }}>{item.rarity_display}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-400">{parseFloat(item.current_price).toFixed(6)} DOOF</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{item.required_level}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{item.required_phase}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {item.is_active ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEditClick(item)}
                        className="text-blue-500 hover:text-blue-700"
                        title="Editar"
                      >
                        <Edit className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
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

