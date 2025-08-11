"""
Módulo de Sistema de Busca Inteligente
Sistema de Calibração ADAS - Intelligent Search Module
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Tuple, Any
from fuzzywuzzy import fuzz, process
import hashlib
from datetime import datetime, timedelta
import json
import os

class SearchCache:
   """
   Sistema de cache para otimizar buscas repetidas
   """
   
   def __init__(self, cache_duration_hours: int = 24):
       self.cache = {}
       self.cache_duration = timedelta(hours=cache_duration_hours)
       self.cache_file = "cache/search_cache.json"
       self.load_cache()
   
   def load_cache(self):
       """Carrega cache do arquivo"""
       try:
           if os.path.exists(self.cache_file):
               with open(self.cache_file, 'r', encoding='utf-8') as f:
                   cache_data = json.load(f)
                   # Converter timestamps de volta para datetime
                   for key, value in cache_data.items():
                       if 'timestamp' in value:
                           value['timestamp'] = datetime.fromisoformat(value['timestamp'])
                   self.cache = cache_data
       except Exception as e:
           print(f"Erro ao carregar cache de busca: {e}")
           self.cache = {}
   
   def save_cache(self):
       """Salva cache no arquivo"""
       try:
           os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
           # Converter datetime para string para serialização JSON
           cache_to_save = {}
           for key, value in self.cache.items():
               cache_copy = value.copy()
               if 'timestamp' in cache_copy:
                   cache_copy['timestamp'] = cache_copy['timestamp'].isoformat()
               cache_to_save[key] = cache_copy
           
           with open(self.cache_file, 'w', encoding='utf-8') as f:
               json.dump(cache_to_save, f, ensure_ascii=False, indent=2)
       except Exception as e:
           print(f"Erro ao salvar cache de busca: {e}")
   
   def get_cache_key(self, query: str, filters: Dict = None) -> str:
       """Gera chave única para cache"""
       cache_string = f"{query.lower().strip()}"
       if filters:
           cache_string += f"_{json.dumps(filters, sort_keys=True)}"
       return hashlib.md5(cache_string.encode()).hexdigest()
   
   def get(self, query: str, filters: Dict = None) -> Optional[List[Dict]]:
       """Recupera resultado do cache se válido"""
       cache_key = self.get_cache_key(query, filters)
       
       if cache_key in self.cache:
           cache_entry = self.cache[cache_key]
           cache_time = cache_entry.get('timestamp')
           
           if cache_time and datetime.now() - cache_time < self.cache_duration:
               return cache_entry.get('results')
           else:
               # Remove cache expirado
               del self.cache[cache_key]
       
       return None
   
   def set(self, query: str, results: List[Dict], filters: Dict = None):
       """Salva resultado no cache"""
       cache_key = self.get_cache_key(query, filters)
       self.cache[cache_key] = {
           'results': results,
           'timestamp': datetime.now(),
           'query': query,
           'filters': filters
       }
       self.save_cache()

class TextNormalizer:
   """
   Classe para normalização de texto para busca
   """
   
   @staticmethod
   def normalize_text(text: str) -> str:
       """Normaliza texto removendo acentos e caracteres especiais"""
       if not isinstance(text, str):
           return ""
       
       text = text.upper().strip()
       
       # Mapeamento de acentos
       accent_map = {
           'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
           'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
           'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
           'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
           'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
           'Ç': 'C', 'Ñ': 'N'
       }
       
       for accented, normal in accent_map.items():
           text = text.replace(accented, normal)
       
       # Remove caracteres especiais extras
       text = re.sub(r'[^\w\s]', ' ', text)
       text = re.sub(r'\s+', ' ', text)
       
       return text.strip()
   
   @staticmethod
   def extract_numbers(text: str) -> List[str]:
       """Extrai números do texto"""
       return re.findall(r'\d+', text)
   
   @staticmethod
   def extract_brands(text: str) -> List[str]:
       """Extrai possíveis marcas do texto"""
       known_brands = [
           'BMW', 'MERCEDES', 'MERCEDES-BENZ', 'AUDI', 'VOLKSWAGEN', 'VW',
           'VOLVO', 'TOYOTA', 'FORD', 'HYUNDAI', 'JEEP', 'LAND ROVER',
           'PEUGEOT', 'RENAULT', 'FIAT', 'NISSAN', 'HONDA', 'MAZDA',
           'SUBARU', 'MITSUBISHI', 'LEXUS', 'INFINITI', 'ACURA',
           'PORSCHE', 'FERRARI', 'LAMBORGHINI', 'BENTLEY', 'ROLLS-ROYCE'
       ]
       
       text_normalized = TextNormalizer.normalize_text(text)
       found_brands = []
       
       for brand in known_brands:
           if brand in text_normalized:
               found_brands.append(brand)
       
       return found_brands

class IntelligentSearch:
   """
   Sistema de busca inteligente para veículos ADAS
   """
   
   def __init__(self, vehicle_database):
       self.db = vehicle_database
       self.cache = SearchCache()
       self.normalizer = TextNormalizer()
       self.search_analytics = {
           'total_searches': 0,
           'cache_hits': 0,
           'last_searches': []
       }
   
   def search(self, query: str, filters: Dict = None, max_results: int = 10) -> Tuple[List[Dict], Dict]:
       """
       Método principal de busca
       
       Args:
           query: Termo de busca
           filters: Filtros adicionais (marca, ano, etc.)
           max_results: Número máximo de resultados
       
       Returns:
           Tuple com (resultados, estatísticas)
       """
       self.search_analytics['total_searches'] += 1
       search_start_time = datetime.now()
       
       # Verificar cache primeiro
       cached_results = self.cache.get(query, filters)
       if cached_results:
           self.search_analytics['cache_hits'] += 1
           return cached_results, {
               'search_time_ms': 0,
               'total_results': len(cached_results),
               'cache_hit': True,
               'search_method': 'cache'
           }
       
       # Normalizar query
       normalized_query = self.normalizer.normalize_text(query)
       
       if not normalized_query.strip():
           return [], {'error': 'Query vazia após normalização'}
       
       # Determinar tipo de busca
       search_results = []
       search_method = 'combined'
       
       # 1. Busca por FIPE ID (mais específica)
       if normalized_query.isdigit():
           fipe_results = self._search_by_fipe(normalized_query)
           if fipe_results:
               search_results = fipe_results
               search_method = 'fipe_id'
           
       # 2. Se não encontrou por FIPE, busca textual
       if not search_results:
           search_results = self._search_by_text(normalized_query, filters, max_results)
           search_method = 'text_search'
       
       # Aplicar filtros adicionais
       if filters:
           search_results = self._apply_filters(search_results, filters)
       
       # Limitar resultados
       search_results = search_results[:max_results]
       
       # Salvar no cache
       self.cache.set(query, search_results, filters)
       
       # Calcular estatísticas
       search_time = (datetime.now() - search_start_time).total_seconds() * 1000
       
       # Registrar busca
       self._log_search(query, len(search_results), search_method)
       
       stats = {
           'search_time_ms': round(search_time, 2),
           'total_results': len(search_results),
           'cache_hit': False,
           'search_method': search_method,
           'query_normalized': normalized_query
       }
       
       return search_results, stats
   
   def _search_by_fipe(self, fipe_id: str) -> List[Dict]:
       """Busca exata por código FIPE"""
       try:
           fipe_int = int(fipe_id)
           df = self.db.df
           
           if df is None or df.empty:
               return []
           
           # Busca exata
           matches = df[df['FipeID'] == fipe_int]
           
           if not matches.empty:
               return [self._row_to_result_dict(row, 100) for _, row in matches.iterrows()]
           
       except (ValueError, KeyError):
           pass
       
       return []
   
   def _search_by_text(self, query: str, filters: Dict = None, max_results: int = 10) -> List[Dict]:
       """Busca textual inteligente"""
       df = self.db.df
       
       if df is None or df.empty:
           return []
       
       results = []
       
       # Extrair informações da query
       numbers = self.normalizer.extract_numbers(query)
       brands = self.normalizer.extract_brands(query)
       
       for idx, row in df.iterrows():
           score = self._calculate_relevance_score(query, row, numbers, brands)
           
           if score > 60:  # Threshold de relevância
               result = self._row_to_result_dict(row, score)
               results.append(result)
       
       # Ordenar por relevância
       results.sort(key=lambda x: x.get('search_score', 0), reverse=True)
       
       return results[:max_results]
   
   def _calculate_relevance_score(self, query: str, row: pd.Series, numbers: List[str], brands: List[str]) -> float:
       """Calcula score de relevância para um veículo"""
       score = 0
       
       try:
           # Score base por marca
           brand_name = str(row.get('BrandName', '')).upper()
           if brand_name in query.upper():
               score += 50
           
           # Score por marcas extraídas
           for brand in brands:
               if brand in brand_name:
                   score += 40
           
           # Score por modelo (fuzzy matching)
           vehicle_name = str(row.get('VehicleName', ''))
           if vehicle_name:
               model_score = fuzz.partial_ratio(query.upper(), vehicle_name.upper())
               score += model_score * 0.6
           
           # Score por abreviação
           abbreviation = str(row.get('Abreviação de descrição', ''))
           if abbreviation and abbreviation != 'nan':
               abbrev_score = fuzz.ratio(query.upper(), abbreviation.upper())
               score += abbrev_score * 0.4
           
           # Score por ano (se número presente na query)
           if numbers:
               vehicle_year = str(row.get('VehicleModelYear', ''))
               for num in numbers:
                   if num in vehicle_year:
                       score += 30
           
           # Score por FIPE ID parcial
           fipe_id = str(row.get('FipeID', ''))
           for num in numbers:
               if len(num) >= 3 and num in fipe_id:
                   score += 25
           
           # Bonus para veículos com ADAS
           if row.get('ADAS') == 'Sim':
               score += 10
           
           # Score por texto combinado (busca geral)
           combined_text = f"{brand_name} {vehicle_name} {abbreviation}".upper()
           if combined_text.strip():
               combined_score = fuzz.partial_ratio(query.upper(), combined_text)
               score += combined_score * 0.3
       
       except Exception as e:
           print(f"Erro ao calcular score: {e}")
           return 0
       
       return min(score, 100)  # Máximo 100
   
   def _row_to_result_dict(self, row: pd.Series, score: float) -> Dict:
       """Converte linha do DataFrame para dicionário de resultado"""
       return {
           'fipe_id': row.get('FipeID'),
           'year': row.get('VehicleModelYear'),
           'brand': row.get('BrandName'),
           'model': row.get('VehicleName'),
           'abbreviation': row.get('Abreviação de descrição'),
           'has_adas': row.get('ADAS') == 'Sim',
           'windshield_adas': row.get('ADAS no Parabrisa') == 'Sim',
           'bumper_adas': row.get('Adas no Parachoque') == 'Sim',
           'calibration_type': row.get('Tipo de Regulagem'),
           'rearview_camera': row.get('Camera no Retrovisor') == 'Sim',
           'matrix_lights': row.get('Faróis Matrix') == 'Sim',
           'search_score': round(score, 2)
       }
   
   def _apply_filters(self, results: List[Dict], filters: Dict) -> List[Dict]:
       """Aplica filtros adicionais aos resultados"""
       filtered_results = results.copy()
       
       for filter_key, filter_value in filters.items():
           if filter_key == 'brand' and filter_value:
               filtered_results = [r for r in filtered_results 
                                 if filter_value.upper() in r.get('brand', '').upper()]
           
           elif filter_key == 'year' and filter_value:
               filtered_results = [r for r in filtered_results 
                                 if str(filter_value) == str(r.get('year', ''))]
           
           elif filter_key == 'has_adas' and filter_value is not None:
               filtered_results = [r for r in filtered_results 
                                 if r.get('has_adas') == filter_value]
           
           elif filter_key == 'calibration_type' and filter_value:
               filtered_results = [r for r in filtered_results 
                                 if filter_value.lower() in r.get('calibration_type', '').lower()]
       
       return filtered_results
   
   def _log_search(self, query: str, results_count: int, method: str):
       """Registra busca para analytics"""
       search_log = {
           'timestamp': datetime.now().isoformat(),
           'query': query,
           'results_count': results_count,
           'method': method
       }
       
       self.search_analytics['last_searches'].insert(0, search_log)
       self.search_analytics['last_searches'] = self.search_analytics['last_searches'][:50]  # Manter apenas 50
   
   def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
       """Gera sugestões de busca baseadas na query parcial"""
       df = self.db.df
       
       if df is None or df.empty or len(partial_query) < 2:
           return []
       
       suggestions = set()
       partial_normalized = self.normalizer.normalize_text(partial_query)
       
       # Sugestões de marcas
       unique_brands = df['BrandName'].dropna().unique()
       for brand in unique_brands:
           if partial_normalized in self.normalizer.normalize_text(brand):
               suggestions.add(brand)
       
       # Sugestões de modelos populares
       if len(suggestions) < limit:
           popular_models = df['Abreviação de descrição'].dropna().value_counts().head(20)
           for model in popular_models.index:
               if partial_normalized in self.normalizer.normalize_text(model):
                   suggestions.add(model)
       
       return list(suggestions)[:limit]
   
   def get_analytics(self) -> Dict:
       """Retorna estatísticas de uso do sistema de busca"""
       cache_hit_rate = (self.search_analytics['cache_hits'] / 
                        max(self.search_analytics['total_searches'], 1)) * 100
       
       return {
           'total_searches': self.search_analytics['total_searches'],
           'cache_hits': self.search_analytics['cache_hits'],
           'cache_hit_rate': round(cache_hit_rate, 2),
           'recent_searches': self.search_analytics['last_searches'][:10]
       }
   
   def advanced_search(self, criteria: Dict) -> List[Dict]:
       """
       Busca avançada com múltiplos critérios
       
       Args:
           criteria: {
               'brand': 'BMW',
               'year_range': [2020, 2024],
               'has_adas': True,
               'calibration_type': 'Dinamica',
               'features': ['windshield_adas', 'matrix_lights']
           }
       """
       df = self.db.df
       
       if df is None or df.empty:
           return []
       
       # Aplicar filtros progressivamente
       filtered_df = df.copy()
       
       # Filtro por marca
       if criteria.get('brand'):
           brand_filter = criteria['brand'].upper()
           filtered_df = filtered_df[
               filtered_df['BrandName'].str.upper().str.contains(brand_filter, na=False)
           ]
       
       # Filtro por ano
       if criteria.get('year_range'):
           min_year, max_year = criteria['year_range']
           filtered_df = filtered_df[
               (filtered_df['VehicleModelYear'] >= min_year) &
               (filtered_df['VehicleModelYear'] <= max_year)
           ]
       
       # Filtro por ADAS
       if criteria.get('has_adas') is not None:
           adas_value = 'Sim' if criteria['has_adas'] else 'Não'
           filtered_df = filtered_df[filtered_df['ADAS'] == adas_value]
       
       # Filtro por tipo de calibração
       if criteria.get('calibration_type'):
           cal_type = criteria['calibration_type']
           filtered_df = filtered_df[
               filtered_df['Tipo de Regulagem'].str.contains(cal_type, case=False, na=False)
           ]
       
       # Converter para lista de dicionários
       results = []
       for _, row in filtered_df.iterrows():
           result = self._row_to_result_dict(row, 95)  # Score alto para busca avançada
           results.append(result)
       
       return results[:50]  # Limitar a 50 resultados

class SearchOptimizer:
   """
   Classe para otimização de performance de busca
   """
   
   def __init__(self, search_engine: IntelligentSearch):
       self.search_engine = search_engine
       self.performance_data = []
   
   def benchmark_search(self, test_queries: List[str]) -> Dict:
       """Executa benchmark do sistema de busca"""
       results = {
           'total_queries': len(test_queries),
           'total_time': 0,
           'average_time': 0,
           'fastest_query': None,
           'slowest_query': None,
           'cache_performance': {}
       }
       
       times = []
       
       for query in test_queries:
           start_time = datetime.now()
           search_results, stats = self.search_engine.search(query)
           end_time = datetime.now()
           
           query_time = (end_time - start_time).total_seconds() * 1000
           times.append(query_time)
           
           self.performance_data.append({
               'query': query,
               'time_ms': query_time,
               'results_count': len(search_results),
               'cache_hit': stats.get('cache_hit', False)
           })
       
       if times:
           results['total_time'] = sum(times)
           results['average_time'] = sum(times) / len(times)
           results['fastest_query'] = min(times)
           results['slowest_query'] = max(times)
       
       return results
   
   def get_optimization_suggestions(self) -> List[str]:
       """Retorna sugestões para otimização"""
       suggestions = []
       
       if not self.performance_data:
           return ["Execute benchmark primeiro para obter sugestões"]
       
       # Analisar performance
       avg_time = sum(p['time_ms'] for p in self.performance_data) / len(self.performance_data)
       cache_hits = sum(1 for p in self.performance_data if p['cache_hit'])
       cache_rate = (cache_hits / len(self.performance_data)) * 100
       
       if avg_time > 500:  # 500ms
           suggestions.append("Tempo médio de busca alto - considere otimizar algoritmos")
       
       if cache_rate < 30:
           suggestions.append("Taxa de cache baixa - considere aumentar duração do cache")
       
       slow_queries = [p for p in self.performance_data if p['time_ms'] > avg_time * 2]
       if slow_queries:
           suggestions.append(f"Encontradas {len(slow_queries)} queries lentas - otimizar busca textual")
       
       return suggestions

# Função de teste
def test_search_system():
   """Função para testar o sistema de busca"""
   # Simular dados de teste
   test_data = {
       'FipeID': [92983, 95432, 87621],
       'BrandName': ['BMW', 'VOLKSWAGEN', 'MERCEDES-BENZ'],
       'VehicleName': ['118i M Sport 1.5 TB 12V Aut. 5p', 'Polo TSI 1.0 200 Aut. 5p', 'A-Class A200 1.3 TB Aut.'],
       'Abreviação de descrição': ['118i M Sport', 'Polo TSI', 'A200'],
       'VehicleModelYear': [2024, 2023, 2024],
       'ADAS': ['Sim', 'Sim', 'Sim'],
       'Tipo de Regulagem': ['Dinamica', 'Estatica', 'Dinamica']
   }
   
   class MockDB:
       def __init__(self):
           self.df = pd.DataFrame(test_data)
   
   mock_db = MockDB()
   search_engine = IntelligentSearch(mock_db)
   
   # Testar busca
   results, stats = search_engine.search("BMW 118i")
   print(f"Teste BMW 118i: {len(results)} resultados em {stats['search_time_ms']}ms")
   
   return search_engine

if __name__ == "__main__":
   test_search_system()
