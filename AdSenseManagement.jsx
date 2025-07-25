import { useState, useEffect } from 'react'
import { DollarSign, Settings, PlusCircle, Edit, Save, X, Trash2, Link, Zap, Clock, Shield, CheckCircle, XCircle } from 'lucide-react'

export function AdSenseManagement({ token }) {
  const [config, setConfig] = useState(null)
  const [adUnits, setAdUnits] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingConfig, setEditingConfig] = useState(false)
  const [configFormData, setConfigFormData] = useState({
    client_id: '', client_secret: '', redirect_uri: '',
    ad_display_interval_minutes: 10, ad_display_duration_seconds: 30,
    fraud_detection_threshold: 0.5, is_active: false
  })
  const [editingAdUnit, setEditingAdUnit] = useState(null)
  const [adUnitFormData, setAdUnitFormData] = useState({
    name: '', ad_unit_id: '', ad_format: 'display', is_active: true
  })
  const [creatingNewAdUnit, setCreatingNewAdUnit] = useState(false)

  const adFormats = ['display', 'in-feed', 'in-article', 'matched-content', 'link']

  useEffect(() => {
    fetchAdSenseData()
  }, [])

  const fetchAdSenseData = async () => {
    setLoading(true)
    setError(null)
    try {
      const configResponse = await fetch('/api/admin/adsense/config', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (configResponse.ok) {
        const configData = await configResponse.json()
        setConfig(configData)
        setConfigFormData({
          client_id: configData.client_id || '',
          client_secret: configData.client_secret || '',
          redirect_uri: configData.redirect_uri || '',
          ad_display_interval_minutes: configData.ad_display_interval_minutes || 10,
          ad_display_duration_seconds: configData.ad_display_duration_seconds || 30,
          fraud_detection_threshold: configData.fraud_detection_threshold || 0.5,
          is_active: configData.is_active
        })
      } else if (configResponse.status === 404) {
        setConfig(null)
      } else {
        throw new Error(`HTTP error! status: ${configResponse.status}`)
      }

      const adUnitsResponse = await fetch('/api/admin/adsense/ad-units', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (adUnitsResponse.ok) {
        const adUnitsData = await adUnitsResponse.json()
        setAdUnits(adUnitsData)
      } else {
        throw new Error(`HTTP error! status: ${adUnitsResponse.status}`)
      }

    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveConfig = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/admin/adsense/config', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(configFormData)
      })
      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.error || `HTTP error! status: ${response.status}`)
      }
      await response.json()
      alert('Configuração do AdSense atualizada com sucesso!')
      fetchAdSenseData()
      setEditingConfig(false)
    } catch (e) {
      setError(e.message)
      alert(`Erro ao atualizar configuração: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAdUnit = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/admin/adsense/ad-units', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(adUnitFormData)
      })
      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.error || `HTTP error! status: ${response.status}`)
      }
      await response.json()
      alert('Unidade de anúncio criada com sucesso!')
      fetchAdSenseData()
      setCreatingNewAdUnit(false)
      setAdUnitFormData({ name: '', ad_unit_id: '', ad_format: 'display', is_active: true })
    } catch (e) {
      setError(e.message)
      alert(`Erro ao criar unidade de anúncio: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateAdUnit = async (adUnitId) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/admin/adsense/ad-units/${adUnitId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(adUnitFormData)
      })
      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.error || `HTTP error! status: ${response.status}`)
      }
      await response.json()
      alert('Unidade de anúncio atualizada com sucesso!')
      fetchAdSenseData()
      setEditingAdUnit(null)
      setAdUnitFormData({ name: '', ad_unit_id: '', ad_format: 'display', is_active: true })
    } catch (e) {
      setError(e.message)
      alert(`Erro ao atualizar unidade de anúncio: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAdUnit = async (adUnitId) => {
    if (!window.confirm('Tem certeza que deseja deletar esta unidade de anúncio?')) {
      return
    }
    setLoading(true)
    try {
      const response = await fetch(`/api/admin/adsense/ad-units/${adUnitId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.error || `HTTP error! status: ${response.status}`)
      }
      alert('Unidade de anúncio deletada com sucesso!')
      fetchAdSenseData()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao deletar unidade de anúncio: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/30 border border-red-500 text-red-300 p-4 rounded-md">
        <p>Erro: {error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* AdSense Configuration */}
      <div className="bg-gray-800 rounded-lg p-6 border border-purple-500/20">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-white flex items-center">
            <Settings className="w-6 h-6 mr-2 text-blue-400" />
            Configuração do Google AdSense
          </h2>
          {!editingConfig ? (
            <button
              onClick={() => setEditingConfig(true)}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md flex items-center space-x-2"
            >
              <Edit size={18} /><span>Editar</span>
            </button>
          ) : (
            <div className="flex space-x-2">
              <button
                onClick={() => setEditingConfig(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md flex items-center space-x-2"
              >
                <X size={18} /><span>Cancelar</span>
              </button>
              <button
                onClick={handleSaveConfig}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md flex items-center space-x-2"
              >
                <Save size={18} /><span>Salvar</span>
              </button>
            </div>
          )}
        </div>

        {editingConfig || !config ? (
          <form className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-400 text-sm mb-1">Client ID</label>
              <input type="text" value={configFormData.client_id} onChange={(e) => setConfigFormData({ ...configFormData, client_id: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-1">Client Secret</label>
              <input type="text" value={configFormData.client_secret} onChange={(e) => setConfigFormData({ ...configFormData, client_secret: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-gray-400 text-sm mb-1">Redirect URI</label>
              <input type="text" value={configFormData.redirect_uri} onChange={(e) => setConfigFormData({ ...configFormData, redirect_uri: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-1">Intervalo de Exibição (minutos)</label>
              <input type="number" value={configFormData.ad_display_interval_minutes} onChange={(e) => setConfigFormData({ ...configFormData, ad_display_interval_minutes: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-1">Duração do Anúncio (segundos)</label>
              <input type="number" value={configFormData.ad_display_duration_seconds} onChange={(e) => setConfigFormData({ ...configFormData, ad_display_duration_seconds: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-1">Limite de Detecção de Fraude</label>
              <input type="number" step="0.01" value={configFormData.fraud_detection_threshold} onChange={(e) => setConfigFormData({ ...configFormData, fraud_detection_threshold: parseFloat(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
            </div>
            <div className="flex items-center md:col-span-2">
              <label className="flex items-center text-gray-400">
                <input type="checkbox" checked={configFormData.is_active} onChange={(e) => setConfigFormData({ ...configFormData, is_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
                <span className="ml-2">Ativar AdSense</span>
              </label>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <p><span className="font-semibold">Client ID:</span> {config.client_id}</p>
            <p><span className="font-semibold">Client Secret:</span> {config.client_secret ? '********' : 'Não configurado'}</p>
            <p><span className="font-semibold">Redirect URI:</span> {config.redirect_uri}</p>
            <p><span className="font-semibold">Intervalo de Exibição:</span> {config.ad_display_interval_minutes} minutos</p>
            <p><span className="font-semibold">Duração do Anúncio:</span> {config.ad_display_duration_seconds} segundos</p>
            <p><span className="font-semibold">Limite de Fraude:</span> {config.fraud_detection_threshold}</p>
            <p className="flex items-center"><span className="font-semibold">Status:</span> {config.is_active ? <><CheckCircle className="w-5 h-5 text-green-500 ml-2" /> Ativo</> : <><XCircle className="w-5 h-5 text-red-500 ml-2" /> Inativo</>}</p>
          </div>
        )}
      </div>

      {/* Ad Units Management */}
      <div className="bg-gray-800 rounded-lg p-6 border border-purple-500/20">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-white flex items-center">
            <Link className="w-6 h-6 mr-2 text-yellow-400" />
            Unidades de Anúncio
          </h2>
          <button
            onClick={() => setCreatingNewAdUnit(true)}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md flex items-center space-x-2"
          >
            <PlusCircle size={18} /><span>Nova Unidade</span>
          </button>
        </div>

        {creatingNewAdUnit && (
          <div className="mb-6 p-4 border border-gray-700 rounded-md">
            <h3 className="text-xl font-bold text-white mb-4">Criar Nova Unidade de Anúncio</h3>
            <form onSubmit={(e) => { e.preventDefault(); handleCreateAdUnit() }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-400 text-sm mb-1">Nome</label>
                <input type="text" value={adUnitFormData.name} onChange={(e) => setAdUnitFormData({ ...adUnitFormData, name: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
              </div>
              <div>
                <label className="block text-gray-400 text-sm mb-1">ID da Unidade de Anúncio</label>
                <input type="text" value={adUnitFormData.ad_unit_id} onChange={(e) => setAdUnitFormData({ ...adUnitFormData, ad_unit_id: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required />
              </div>
              <div>
                <label className="block text-gray-400 text-sm mb-1">Formato do Anúncio</label>
                <select value={adUnitFormData.ad_format} onChange={(e) => setAdUnitFormData({ ...adUnitFormData, ad_format: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" required>
                  {adFormats.map(format => <option key={format} value={format}>{format.charAt(0).toUpperCase() + format.slice(1)}</option>)}
                </select>
              </div>
              <div className="flex items-center">
                <label className="flex items-center text-gray-400">
                  <input type="checkbox" checked={adUnitFormData.is_active} onChange={(e) => setAdUnitFormData({ ...adUnitFormData, is_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
                  <span className="ml-2">Ativo</span>
                </label>
              </div>
              <div className="md:col-span-2 flex justify-end space-x-2">
                <button type="button" onClick={() => setCreatingNewAdUnit(false)} className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md flex items-center space-x-2">
                  <X size={18} /><span>Cancelar</span>
                </button>
                <button type="submit" disabled={loading} className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md flex items-center space-x-2">
                  <Save size={18} /><span>{loading ? 'Criando...' : 'Criar'}</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {adUnits.length === 0 && !creatingNewAdUnit ? (
          <div className="text-center py-8 text-gray-400">
            <Link className="w-12 h-12 mx-auto mb-4" />
            <p>Nenhuma unidade de anúncio configurada.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Nome</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">ID da Unidade</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Formato</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ativo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {adUnits.map((unit) => (
                  <tr key={unit.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {editingAdUnit === unit.id ? (
                        <input type="text" value={adUnitFormData.name} onChange={(e) => setAdUnitFormData({ ...adUnitFormData, name: e.target.value })} className="bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-white" />
                      ) : (
                        <span className="text-white font-medium">{unit.name}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {editingAdUnit === unit.id ? (
                        <input type="text" value={adUnitFormData.ad_unit_id} onChange={(e) => setAdUnitFormData({ ...adUnitFormData, ad_unit_id: e.target.value })} className="bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-white" />
                      ) : (
                        <span className="text-gray-400">{unit.ad_unit_id}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {editingAdUnit === unit.id ? (
                        <select value={adUnitFormData.ad_format} onChange={(e) => setAdUnitFormData({ ...adUnitFormData, ad_format: e.target.value })} className="bg-gray-700 border border-gray-600 rounded-md px-2 py-1 text-white">
                          {adFormats.map(format => <option key={format} value={format}>{format.charAt(0).toUpperCase() + format.slice(1)}</option>)}
                        </select>
                      ) : (
                        <span className="text-gray-400">{unit.ad_format}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {editingAdUnit === unit.id ? (
                        <input type="checkbox" checked={adUnitFormData.is_active} onChange={(e) => setAdUnitFormData({ ...adUnitFormData, is_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
                      ) : (
                        unit.is_active ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {editingAdUnit === unit.id ? (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleUpdateAdUnit(unit.id)}
                            className="text-green-500 hover:text-green-700"
                            title="Salvar"
                          >
                            <Save className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => setEditingAdUnit(null)}
                            className="text-gray-500 hover:text-gray-700"
                            title="Cancelar"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => {
                              setEditingAdUnit(unit.id)
                              setAdUnitFormData({ name: unit.name, ad_unit_id: unit.ad_unit_id, ad_format: unit.ad_format, is_active: unit.is_active })
                            }}
                            className="text-blue-500 hover:text-blue-700"
                            title="Editar"
                          >
                            <Edit className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDeleteAdUnit(unit.id)}
                            className="text-red-500 hover:text-red-700"
                            title="Deletar"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

