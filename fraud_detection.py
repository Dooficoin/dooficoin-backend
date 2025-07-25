import time
import math
from datetime import datetime, timedelta
from collections import defaultdict, deque
from flask import current_app

# Dicionário para armazenar ações dos jogadores para análise de padrões
player_actions = defaultdict(lambda: deque(maxlen=100))
# Dicionário para armazenar estatísticas de jogadores
player_stats = {}
# Dicionário para armazenar alertas de fraude
fraud_alerts = []

class FraudDetector:
    """Classe para detecção de fraudes no jogo."""
    
    @staticmethod
    def record_player_action(player_id, action_type, details=None):
        """
        Registra uma ação do jogador para análise posterior.
        
        Args:
            player_id: ID do jogador
            action_type: Tipo de ação (ex: 'kill_monster', 'self_eliminate', 'buy_item')
            details: Detalhes adicionais sobre a ação (opcional)
        """
        action = {
            'timestamp': time.time(),
            'datetime': datetime.utcnow().isoformat(),
            'action_type': action_type,
            'details': details or {}
        }
        
        player_actions[player_id].append(action)
        
        # Atualizar estatísticas do jogador
        if player_id not in player_stats:
            player_stats[player_id] = {
                'action_counts': defaultdict(int),
                'last_actions': {},
                'suspicious_activity': 0,  # Pontuação de suspeita
                'warnings_issued': 0
            }
        
        player_stats[player_id]['action_counts'][action_type] += 1
        player_stats[player_id]['last_actions'][action_type] = time.time()
        
        # Verificar se há padrões suspeitos após registrar a ação
        FraudDetector.check_for_suspicious_patterns(player_id)
    
    @staticmethod
    def check_for_suspicious_patterns(player_id):
        """
        Verifica se há padrões suspeitos nas ações do jogador.
        
        Args:
            player_id: ID do jogador a ser verificado
        
        Returns:
            bool: True se padrões suspeitos foram detectados, False caso contrário
        """
        if player_id not in player_stats:
            return False
        
        suspicious = False
        stats = player_stats[player_id]
        actions = list(player_actions[player_id])
        
        # Verificar frequência muito alta de ações (possível bot)
        if len(actions) >= 5:
            # Calcular o tempo médio entre as últimas 5 ações
            recent_actions = actions[-5:]
            timestamps = [a['timestamp'] for a in recent_actions]
            
            if len(timestamps) >= 2:
                time_diffs = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
                avg_time_diff = sum(time_diffs) / len(time_diffs)
                
                # Se o tempo médio entre ações for muito pequeno (menos de 1 segundo)
                # e consistente (baixo desvio padrão), pode ser um bot
                if avg_time_diff < 1.0:
                    std_dev = math.sqrt(sum((x - avg_time_diff) ** 2 for x in time_diffs) / len(time_diffs))
                    if std_dev < 0.2:  # Tempo muito consistente
                        suspicious = True
                        stats['suspicious_activity'] += 10
                        FraudDetector.create_fraud_alert(player_id, 'bot_activity', {
                            'avg_time_between_actions': avg_time_diff,
                            'std_dev': std_dev,
                            'action_types': [a['action_type'] for a in recent_actions]
                        })
        
        # Verificar padrões específicos de fraude para diferentes tipos de ações
        
        # 1. Auto-eliminações muito frequentes
        if stats['action_counts'].get('self_eliminate', 0) > 50:
            # Verificar se as auto-eliminações são a maioria das ações
            total_actions = sum(stats['action_counts'].values())
            if stats['action_counts']['self_eliminate'] / total_actions > 0.8:
                suspicious = True
                stats['suspicious_activity'] += 5
                FraudDetector.create_fraud_alert(player_id, 'excessive_self_elimination', {
                    'count': stats['action_counts']['self_eliminate'],
                    'percentage': stats['action_counts']['self_eliminate'] / total_actions
                })
        
        # 2. Ganho de moedas muito rápido
        if 'earn_coins' in stats['action_counts'] and stats['action_counts']['earn_coins'] > 20:
            coin_actions = [a for a in actions if a['action_type'] == 'earn_coins']
            if len(coin_actions) >= 10:
                # Calcular a taxa de ganho de moedas
                total_coins = sum(a['details'].get('amount', 0) for a in coin_actions)
                time_span = coin_actions[-1]['timestamp'] - coin_actions[0]['timestamp']
                if time_span > 0:
                    coins_per_second = total_coins / time_span
                    # Definir um limite razoável com base na mecânica do jogo
                    if coins_per_second > 0.0000000001:  # Ajustar conforme necessário
                        suspicious = True
                        stats['suspicious_activity'] += 15
                        FraudDetector.create_fraud_alert(player_id, 'abnormal_coin_gain', {
                            'coins_per_second': coins_per_second,
                            'total_coins': total_coins,
                            'time_span_seconds': time_span
                        })
        
        # 3. Padrão de compras suspeito
        if 'buy_item' in stats['action_counts'] and stats['action_counts']['buy_item'] > 5:
            buy_actions = [a for a in actions if a['action_type'] == 'buy_item']
            if len(buy_actions) >= 5:
                # Verificar compras em sequência muito rápida
                buy_timestamps = [a['timestamp'] for a in buy_actions]
                for i in range(1, len(buy_timestamps)):
                    if buy_timestamps[i] - buy_timestamps[i-1] < 0.5:  # Menos de meio segundo entre compras
                        suspicious = True
                        stats['suspicious_activity'] += 8
                        FraudDetector.create_fraud_alert(player_id, 'rapid_purchases', {
                            'purchases': [(a['details'].get('item_id'), a['details'].get('price')) for a in buy_actions[-5:]]
                        })
                        break
        
        # Tomar ações com base na pontuação de suspeita
        if stats['suspicious_activity'] >= 20 and stats['warnings_issued'] == 0:
            # Primeira advertência
            stats['warnings_issued'] += 1
            # Em um sistema real, você poderia enviar uma mensagem ao jogador
            print(f"WARNING: Player {player_id} has been flagged for suspicious activity.")
        
        if stats['suspicious_activity'] >= 50:
            # Considerar ações mais severas, como suspensão temporária
            print(f"CRITICAL: Player {player_id} has exceeded the fraud threshold and may be suspended.")
            # Em um sistema real, você poderia suspender a conta automaticamente
            # ou notificar um administrador para revisão manual
        
        return suspicious
    
    @staticmethod
    def create_fraud_alert(player_id, alert_type, details):
        """
        Cria um alerta de fraude para revisão por administradores.
        
        Args:
            player_id: ID do jogador
            alert_type: Tipo de alerta (ex: 'bot_activity', 'excessive_self_elimination')
            details: Detalhes específicos do alerta
        """
        alert = {
            'timestamp': time.time(),
            'datetime': datetime.utcnow().isoformat(),
            'player_id': player_id,
            'alert_type': alert_type,
            'details': details,
            'reviewed': False
        }
        
        fraud_alerts.append(alert)
        
        # Em um ambiente de produção, você poderia salvar isso em um banco de dados
        # e possivelmente enviar notificações para administradores
        print(f"FRAUD ALERT: {alert}")
        
        return alert
    
    @staticmethod
    def get_player_risk_score(player_id):
        """
        Calcula uma pontuação de risco para um jogador com base em seu histórico.
        
        Args:
            player_id: ID do jogador
        
        Returns:
            float: Pontuação de risco (0-100, onde maior é mais arriscado)
        """
        if player_id not in player_stats:
            return 0
        
        stats = player_stats[player_id]
        
        # Iniciar com a pontuação de atividade suspeita
        risk_score = min(stats['suspicious_activity'], 100)
        
        # Considerar outros fatores que podem aumentar ou diminuir o risco
        
        # Fator 1: Tempo de jogo (jogadores mais antigos são geralmente mais confiáveis)
        if player_actions[player_id]:
            first_action_time = min(a['timestamp'] for a in player_actions[player_id])
            account_age_days = (time.time() - first_action_time) / (24 * 3600)
            if account_age_days > 30:  # Conta com mais de 30 dias
                risk_score -= 10
            elif account_age_days < 1:  # Conta muito nova
                risk_score += 10
        
        # Fator 2: Diversidade de ações (bots tendem a repetir as mesmas ações)
        unique_actions = len(stats['action_counts'])
        if unique_actions <= 2:  # Muito poucas ações diferentes
            risk_score += 15
        elif unique_actions >= 8:  # Muitas ações diferentes
            risk_score -= 10
        
        # Garantir que a pontuação esteja no intervalo 0-100
        return max(0, min(100, risk_score))
    
    @staticmethod
    def get_fraud_alerts(reviewed=None, limit=50):
        """
        Obtém alertas de fraude para revisão.
        
        Args:
            reviewed: Se True, retorna apenas alertas revisados. Se False, apenas não revisados.
                     Se None, retorna todos os alertas.
            limit: Número máximo de alertas a retornar
        
        Returns:
            list: Lista de alertas de fraude
        """
        if reviewed is None:
            return sorted(fraud_alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]
        else:
            return sorted([a for a in fraud_alerts if a['reviewed'] == reviewed], 
                         key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    @staticmethod
    def mark_alert_as_reviewed(alert_id, admin_id, action_taken=None):
        """
        Marca um alerta como revisado por um administrador.
        
        Args:
            alert_id: ID do alerta (índice na lista fraud_alerts)
            admin_id: ID do administrador que revisou
            action_taken: Descrição da ação tomada (opcional)
        
        Returns:
            bool: True se o alerta foi encontrado e marcado, False caso contrário
        """
        if 0 <= alert_id < len(fraud_alerts):
            fraud_alerts[alert_id]['reviewed'] = True
            fraud_alerts[alert_id]['reviewed_by'] = admin_id
            fraud_alerts[alert_id]['review_time'] = time.time()
            fraud_alerts[alert_id]['review_datetime'] = datetime.utcnow().isoformat()
            
            if action_taken:
                fraud_alerts[alert_id]['action_taken'] = action_taken
            
            return True
        
        return False

