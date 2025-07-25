#!/usr/bin/env python3
"""
Script para popular o banco de dados com cenários e monstros.
"""

from main import app
from database import db
from models.scenario import Scenario, Monster, ScenarioReward, ScenarioType, MonsterType
from models.item import Item, CollectibleCard, ItemRarity, ItemType

def populate_scenarios():
    with app.app_context():
        # Verificar se já existem cenários
        if Scenario.query.count() > 0:
            print("Cenários já existem no banco de dados.")
            return
        
        # Criar cenários do Brasil
        brasil_scenarios = [
            {
                'name': 'Cristo Redentor',
                'description': 'Lute contra monstros nas alturas do Cristo Redentor no Rio de Janeiro',
                'country': 'Brasil',
                'city': 'Rio de Janeiro',
                'scenario_type': ScenarioType.URBAN,
                'difficulty': 1,
                'min_level': 1,
                'latitude': -22.9519,
                'longitude': -43.2105
            },
            {
                'name': 'Copacabana',
                'description': 'Enfrente criaturas marinhas na famosa praia de Copacabana',
                'country': 'Brasil',
                'city': 'Rio de Janeiro',
                'scenario_type': ScenarioType.BEACH,
                'difficulty': 2,
                'min_level': 5,
                'latitude': -22.9711,
                'longitude': -43.1822
            },
            {
                'name': 'Amazônia',
                'description': 'Explore a floresta amazônica e seus mistérios',
                'country': 'Brasil',
                'city': 'Manaus',
                'scenario_type': ScenarioType.FOREST,
                'difficulty': 3,
                'min_level': 10,
                'latitude': -3.1190,
                'longitude': -60.0217
            }
        ]
        
        # Criar cenários dos EUA
        usa_scenarios = [
            {
                'name': 'Times Square',
                'description': 'Batalhe no coração de Nova York',
                'country': 'Estados Unidos',
                'city': 'Nova York',
                'scenario_type': ScenarioType.URBAN,
                'difficulty': 2,
                'min_level': 5,
                'latitude': 40.7580,
                'longitude': -73.9855
            },
            {
                'name': 'Grand Canyon',
                'description': 'Enfrente monstros no majestoso Grand Canyon',
                'country': 'Estados Unidos',
                'city': 'Arizona',
                'scenario_type': ScenarioType.DESERT,
                'difficulty': 4,
                'min_level': 15,
                'latitude': 36.1069,
                'longitude': -112.1129
            }
        ]
        
        all_scenarios = brasil_scenarios + usa_scenarios
        
        for scenario_data in all_scenarios:
            scenario = Scenario(**scenario_data)
            db.session.add(scenario)
        
        # Criar alguns monstros
        monsters = [
            {
                'name': 'Zumbi Urbano',
                'description': 'Um zumbi que vaga pelas cidades',
                'monster_type': MonsterType.ZOMBIE,
                'health': 50,
                'attack': 10,
                'defense': 5,
                'reward_coins': '0.000000000001',
                'reward_xp': 10
            },
            {
                'name': 'Robô Guardião',
                'description': 'Um robô protetor das áreas urbanas',
                'monster_type': MonsterType.ROBOT,
                'health': 80,
                'attack': 15,
                'defense': 10,
                'reward_coins': '0.000000000002',
                'reward_xp': 15
            },
            {
                'name': 'Fera Selvagem',
                'description': 'Um animal feroz da natureza',
                'monster_type': MonsterType.ANIMAL,
                'health': 60,
                'attack': 12,
                'defense': 8,
                'reward_coins': '0.0000000000015',
                'reward_xp': 12
            }
        ]
        
        for monster_data in monsters:
            monster = Monster(**monster_data)
            db.session.add(monster)
        
        db.session.commit()
        print("Cenários e monstros criados com sucesso!")

if __name__ == '__main__':
    populate_scenarios()

