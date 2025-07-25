import { useState, useEffect } from 'react'
import { Settings, Save, X, CheckCircle, XCircle, DollarSign, Clock, Shield, Users, Map, Ghost, Package, Sparkles } from 'lucide-react'

export function AdminSettings({ token }) {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editFormData, setEditFormData] = useState({
    pvp_coin_percentage: 0.20,
    self_kill_coin_reward: '0.00000000000001',
    monster_kill_health_fill_count: 100,
    monster_kill_power_fill_count: 100,
    level_up_player_kill_count: 90,
    level_up_monster_kill_count: 500,
    initial_monsters_per_phase: 300,
    monster_increase_per_phase_percentage: 0.25,
    mining_initial_dooficoin: '0.0000000000000000000000000000000000101',
    mining_time_double_threshold: '0.0000000000000000000000000000000000101',
    mining_time_multiplier: 2,
    ad_display_interval_minutes: 10,
    ad_display_duration_seconds: 30,
    fraud_detection_threshold: 0.5,
    is_adsense_active: false,
    is_pvp_active: true,
    is_mining_active: true,
    is_shop_active: true,
    is_inventory_active: true,
    is_scenarios_active: true,
    is_leaderboard_active: true,
    is_collectible_cards_active: true,
  })

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/admin/settings', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setSettings(data)
      setEditFormData(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSettings = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/admin/settings', {
        method: 'PUT',
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
      alert('Configurações atualizadas com sucesso!')
      fetchSettings()
    } catch (e) {
      setError(e.message)
      alert(`Erro ao atualizar configurações: ${e.message}`)
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
      <div className="bg-gray-800 rounded-lg p-6 border border-purple-500/20">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-white flex items-center">
            <Settings className="w-6 h-6 mr-2 text-blue-400" />
            Configurações Gerais do Jogo
          </h2>
          <button
            onClick={handleSaveSettings}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md flex items-center space-x-2"
          >
            <Save size={18} /><span>Salvar Configurações</span>
          </button>
        </div>

        <form className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Game Mechanics */}
          <div className="col-span-full text-lg font-semibold text-purple-400 mt-4 mb-2">Mecânicas do Jogo</div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">% Moedas PvP</label>
            <input type="number" step="0.01" value={editFormData.pvp_coin_percentage} onChange={(e) => setEditFormData({ ...editFormData, pvp_coin_percentage: parseFloat(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Recompensa Auto-Morte (DOOF)</label>
            <input type="text" value={editFormData.self_kill_coin_reward} onChange={(e) => setEditFormData({ ...editFormData, self_kill_coin_reward: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Monstros para Encher Vida</label>
            <input type="number" value={editFormData.monster_kill_health_fill_count} onChange={(e) => setEditFormData({ ...editFormData, monster_kill_health_fill_count: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Monstros para Encher Poder</label>
            <input type="number" value={editFormData.monster_kill_power_fill_count} onChange={(e) => setEditFormData({ ...editFormData, monster_kill_power_fill_count: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Jogadores para Subir Nível</label>
            <input type="number" value={editFormData.level_up_player_kill_count} onChange={(e) => setEditFormData({ ...editFormData, level_up_player_kill_count: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Monstros para Subir Nível</label>
            <input type="number" value={editFormData.level_up_monster_kill_count} onChange={(e) => setEditFormData({ ...editFormData, level_up_monster_kill_count: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Monstros Iniciais por Fase</label>
            <input type="number" value={editFormData.initial_monsters_per_phase} onChange={(e) => setEditFormData({ ...editFormData, initial_monsters_per_phase: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Aumento de Monstros por Fase (%)</label>
            <input type="number" step="0.01" value={editFormData.monster_increase_per_phase_percentage} onChange={(e) => setEditFormData({ ...editFormData, monster_increase_per_phase_percentage: parseFloat(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>

          {/* Mining Settings */}
          <div className="col-span-full text-lg font-semibold text-purple-400 mt-4 mb-2">Configurações de Mineração</div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">DOOF Inicial Mineração</label>
            <input type="text" value={editFormData.mining_initial_dooficoin} onChange={(e) => setEditFormData({ ...editFormData, mining_initial_dooficoin: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Limite para Dobrar Tempo Mineração</label>
            <input type="text" value={editFormData.mining_time_double_threshold} onChange={(e) => setEditFormData({ ...editFormData, mining_time_double_threshold: e.target.value })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Multiplicador de Tempo Mineração</label>
            <input type="number" value={editFormData.mining_time_multiplier} onChange={(e) => setEditFormData({ ...editFormData, mining_time_multiplier: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>

          {/* AdSense Settings */}
          <div className="col-span-full text-lg font-semibold text-purple-400 mt-4 mb-2">Configurações de Anúncios (AdSense)</div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Intervalo de Exibição (minutos)</label>
            <input type="number" value={editFormData.ad_display_interval_minutes} onChange={(e) => setEditFormData({ ...editFormData, ad_display_interval_minutes: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Duração do Anúncio (segundos)</label>
            <input type="number" value={editFormData.ad_display_duration_seconds} onChange={(e) => setEditFormData({ ...editFormData, ad_display_duration_seconds: parseInt(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>
          <div>
            <label className="block text-gray-400 text-sm mb-1">Limite de Detecção de Fraude</label>
            <input type="number" step="0.01" value={editFormData.fraud_detection_threshold} onChange={(e) => setEditFormData({ ...editFormData, fraud_detection_threshold: parseFloat(e.target.value) })} className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white" />
          </div>

          {/* Feature Toggles */}
          <div className="col-span-full text-lg font-semibold text-purple-400 mt-4 mb-2">Ativar/Desativar Funcionalidades</div>
          <div className="flex flex-col space-y-2">
            <label className="flex items-center text-gray-400">
              <input type="checkbox" name="is_adsense_active" checked={editFormData.is_adsense_active} onChange={(e) => setEditFormData({ ...editFormData, is_adsense_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
              <span className="ml-2 flex items-center"><DollarSign className="w-4 h-4 mr-1" /> Ativar AdSense</span>
            </label>
            <label className="flex items-center text-gray-400">
              <input type="checkbox" name="is_pvp_active" checked={editFormData.is_pvp_active} onChange={(e) => setEditFormData({ ...editFormData, is_pvp_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
              <span className="ml-2 flex items-center"><Users className="w-4 h-4 mr-1" /> Ativar PvP</span>
            </label>
            <label className="flex items-center text-gray-400">
              <input type="checkbox" name="is_mining_active" checked={editFormData.is_mining_active} onChange={(e) => setEditFormData({ ...editFormData, is_mining_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
              <span className="ml-2 flex items-center"><Clock className="w-4 h-4 mr-1" /> Ativar Mineração</span>
            </label>
            <label className="flex items-center text-gray-400">
              <input type="checkbox" name="is_shop_active" checked={editFormData.is_shop_active} onChange={(e) => setEditFormData({ ...editFormData, is_shop_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
              <span className="ml-2 flex items-center"><ShoppingBag className="w-4 h-4 mr-1" /> Ativar Loja</span>
            </label>
            <label className="flex items-center text-gray-400">
              <input type="checkbox" name="is_inventory_active" checked={editFormData.is_inventory_active} onChange={(e) => setEditFormData({ ...editFormData, is_inventory_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
              <span className="ml-2 flex items-center"><Package className="w-4 h-4 mr-1" /> Ativar Inventário</span>
            </label>
            <label className="flex items-center text-gray-400">
              <input type="checkbox" name="is_scenarios_active" checked={editFormData.is_scenarios_active} onChange={(e) => setEditFormData({ ...editFormData, is_scenarios_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
              <span className="ml-2 flex items-center"><Map className="w-4 h-4 mr-1" /> Ativar Cenários</span>
            </label>
            <label className="flex items-center text-gray-400">
              <input type="checkbox" name="is_leaderboard_active" checked={editFormData.is_leaderboard_active} onChange={(e) => setEditFormData({ ...editFormData, is_leaderboard_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
              <span className="ml-2 flex items-center"><Trophy className="w-4 h-4 mr-1" /> Ativar Ranking</span>
            </label>
            <label className="flex items-center text-gray-400">
              <input type="checkbox" name="is_collectible_cards_active" checked={editFormData.is_collectible_cards_active} onChange={(e) => setEditFormData({ ...editFormData, is_collectible_cards_active: e.target.checked })} className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded" />
              <span className="ml-2 flex items-center"><Sparkles className="w-4 h-4 mr-1" /> Ativar Cartas Colecionáveis</span>
            </label>
          </div>
        </form>
      </div>
    </div>
  )
}

