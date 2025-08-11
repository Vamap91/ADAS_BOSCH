"""
Módulos do Sistema de Calibração ADAS

Este pacote contém os módulos principais para o funcionamento
do sistema inteligente de calibração de ADAS.

Módulos disponíveis:
- vehicle_db: Gerenciamento da base de dados de veículos
- search: Sistema de busca inteligente
- bosch_api: Integração com APIs e dados da Bosch
"""

__version__ = "1.0.0"
__author__ = "Sistema ADAS criado por Vinicius Paschoa"

# Importações principais dos módulos
try:
   from .vehicle_db import VehicleDatabase, DataValidator
   from .search import IntelligentSearch, SearchCache
   from .bosch_api import BoschIntegration, CalibrationInstructions
except ImportError:
   # Fallback caso algum módulo não esteja disponível
   pass

# Configurações globais do sistema
SYSTEM_CONFIG = {
   "database": {
       "encoding": "utf-8",
       "separator": ";",
       "cache_duration_hours": 24
   },
   "search": {
       "min_score_threshold": 60,
       "max_results": 10,
       "fuzzy_threshold": 70
   },
   "bosch": {
       "base_url": "https://help.boschdiagnostics.com/DAS3000",
       "cache_file": "cache/bosch_cache.json",
       "timeout_seconds": 15
   }
}

# Logs de inicialização
def get_system_info():
   """Retorna informações do sistema"""
   return {
       "version": __version__,
       "modules": ["vehicle_db", "search", "bosch_api"],
       "config": SYSTEM_CONFIG
   }
