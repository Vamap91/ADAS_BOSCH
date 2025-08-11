"""
Módulo de Gerenciamento da Base de Dados de Veículos
Sistema de Calibração ADAS - Vehicle Database Module
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import hashlib
import streamlit as st

class DataValidator:
   """
   Classe para validação e limpeza de dados de veículos
   """
   
   def __init__(self):
       self.validation_rules = {
           'FipeID': {
               'required': True,
               'type': 'numeric',
               'min_value': 1000,
               'max_value': 9999999
           },
           'BrandName': {
               'required': True,
               'type': 'string',
               'min_length': 2,
               'max_length': 50
           },
           'VehicleName': {
               'required': True,
               'type': 'string',
               'min_length': 5,
               'max_length': 200
           },
           'VehicleModelYear': {
               'required': True,
               'type': 'numeric',
               'min_value': 2000,
               'max_value': 2030
           },
           'ADAS': {
               'required': True,
               'type': 'categorical',
               'allowed_values': ['Sim', 'Não', 'sim', 'não']
           }
       }
       
       self.known_brands = [
           'BMW', 'MERCEDES-BENZ', 'AUDI', 'VOLKSWAGEN', 'VOLVO',
           'TOYOTA', 'FORD', 'HYUNDAI', 'JEEP', 'LAND ROVER',
           'PEUGEOT', 'RENAULT', 'FIAT', 'NISSAN', 'HONDA',
           'MAZDA', 'SUBARU', 'MITSUBISHI', 'LEXUS', 'INFINITI',
           'PORSCHE', 'FERRARI', 'LAMBORGHINI', 'BENTLEY',
           'ROLLS-ROYCE', 'SCANIA', 'VOLVO CAMINHOES'
       ]
   
   def validate_dataframe(self, df: pd.DataFrame) -> Dict:
       """
       Valida DataFrame completo e retorna relatório de validação
       """
       validation_report = {
           'timestamp': datetime.now().isoformat(),
           'total_rows': len(df),
           'validation_passed': True,
           'errors': [],
           'warnings': [],
           'statistics': {},
           'data_quality_score': 0
       }
       
       try:
           # Validações básicas de estrutura
           self._validate_structure(df, validation_report)
           
           # Validações de dados
           self._validate_data_integrity(df, validation_report)
           
           # Validações específicas de domínio
           self._validate_domain_rules(df, validation_report)
           
           # Calcular score de qualidade
           validation_report['data_quality_score'] = self._calculate_quality_score(validation_report)
           
       except Exception as e:
           validation_report['errors'].append(f"Erro durante validação: {str(e)}")
           validation_report['validation_passed'] = False
       
       return validation_report
   
   def _validate_structure(self, df: pd.DataFrame, report: Dict):
       """Valida estrutura básica do DataFrame"""
       required_columns = [
           'FipeID', 'BrandName', 'VehicleName', 'VehicleModelYear', 'ADAS'
       ]
       
       missing_columns = [col for col in required_columns if col not in df.columns]
       if missing_columns:
           report['errors'].append(f"Colunas obrigatórias ausentes: {missing_columns}")
           report['validation_passed'] = False
       
       # Verificar se DataFrame não está vazio
       if df.empty:
           report['errors'].append("DataFrame está vazio")
           report['validation_passed'] = False
       
       # Estatísticas básicas
       report['statistics']['total_columns'] = len(df.columns)
       report['statistics']['memory_usage_mb'] = round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
   
   def _validate_data_integrity(self, df: pd.DataFrame, report: Dict):
       """Valida integridade dos dados"""
       
       # Verificar duplicatas por FIPE ID
       if 'FipeID' in df.columns:
           duplicate_fipe = df['FipeID'].duplicated().sum()
           if duplicate_fipe > 0:
               report['warnings'].append(f"Encontrados {duplicate_fipe} FIPE IDs duplicados")
           
           # Verificar FIPE IDs inválidos
           invalid_fipe = df['FipeID'].isna().sum()
           if invalid_fipe > 0:
               report['errors'].append(f"{invalid_fipe} registros com FIPE ID inválido")
       
       # Verificar dados obrigatórios ausentes
       for column, rules in self.validation_rules.items():
           if column in df.columns and rules.get('required'):
               missing_count = df[column].isna().sum()
               if missing_count > 0:
                   report['warnings'].append(f"Coluna '{column}': {missing_count} valores ausentes")
       
       # Estatísticas de qualidade
       total_cells = len(df) * len(df.columns)
       missing_cells = df.isna().sum().sum()
       report['statistics']['missing_data_percentage'] = round((missing_cells / total_cells) * 100, 2)
   
   def _validate_domain_rules(self, df: pd.DataFrame, report: Dict):
       """Valida regras específicas do domínio automotivo"""
       
       # Validar marcas conhecidas
       if 'BrandName' in df.columns:
           unknown_brands = []
           for brand in df['BrandName'].dropna().unique():
               if brand.upper().strip() not in [b.upper() for b in self.known_brands]:
                   unknown_brands.append(brand)
           
           if unknown_brands:
               report['warnings'].append(f"Marcas não reconhecidas: {unknown_brands[:10]}")  # Mostrar apenas 10
       
       # Validar anos de modelo
       if 'VehicleModelYear' in df.columns:
           current_year = datetime.now().year
           future_years = df[df['VehicleModelYear'] > current_year + 2]
           if not future_years.empty:
               report['warnings'].append(f"Encontrados {len(future_years)} veículos com anos muito futuros")
           
           old_years = df[df['VehicleModelYear'] < 2000]
           if not old_years.empty:
               report['warnings'].append(f"Encontrados {len(old_years)} veículos com anos muito antigos")
       
       # Validar valores de ADAS
       if 'ADAS' in df.columns:
           valid_adas_values = ['Sim', 'Não', 'sim', 'não']
           invalid_adas = df[~df['ADAS'].isin(valid_adas_values + [np.nan])]
           if not invalid_adas.empty:
               report['errors'].append(f"Encontrados {len(invalid_adas)} valores inválidos na coluna ADAS")
       
       # Estatísticas do domínio
       if 'ADAS' in df.columns:
           adas_count = (df['ADAS'] == 'Sim').sum()
           report['statistics']['vehicles_with_adas'] = adas_count
           report['statistics']['adas_percentage'] = round((adas_count / len(df)) * 100, 2)
       
       if 'BrandName' in df.columns:
           report['statistics']['unique_brands'] = df['BrandName'].nunique()
           report['statistics']['top_brands'] = df['BrandName'].value_counts().head(5).to_dict()
   
   def _calculate_quality_score(self, report: Dict) -> float:
       """Calcula score de qualidade dos dados (0-100)"""
       score = 100.0
       
       # Penalizar por erros
       error_count = len(report['errors'])
       score -= error_count * 20  # -20 pontos por erro
       
       # Penalizar por avisos
       warning_count = len(report['warnings'])
       score -= warning_count * 5  # -5 pontos por aviso
       
       # Penalizar por dados ausentes
       missing_percentage = report['statistics'].get('missing_data_percentage', 0)
       score -= missing_percentage * 2  # -2 pontos por % de dados ausentes
       
       return max(0, min(100, score))
   
   def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
       """
       Limpa e normaliza DataFrame
       """
       df_clean = df.copy()
       
       try:
           # Normalizar nomes de marcas
           if 'BrandName' in df_clean.columns:
               df_clean['BrandName'] = df_clean['BrandName'].str.strip().str.upper()
               
               # Padronizar nomes conhecidos
               brand_mappings = {
                   'MERCEDES': 'MERCEDES-BENZ',
                   'MERCEDES BENZ': 'MERCEDES-BENZ',
                   'VW': 'VOLKSWAGEN',
                   'RANGE ROVER': 'LAND ROVER'
               }
               
               for old_name, new_name in brand_mappings.items():
                   df_clean['BrandName'] = df_clean['BrandName'].replace(old_name, new_name)
           
           # Normalizar valores de ADAS
           if 'ADAS' in df_clean.columns:
               df_clean['ADAS'] = df_clean['ADAS'].str.strip().str.capitalize()
               df_clean['ADAS'] = df_clean['ADAS'].replace({'sim': 'Sim', 'não': 'Não', 'nao': 'Não'})
           
           # Limpar nomes de veículos
           if 'VehicleName' in df_clean.columns:
               df_clean['VehicleName'] = df_clean['VehicleName'].str.strip()
           
           # Normalizar anos
           if 'VehicleModelYear' in df_clean.columns:
               df_clean['VehicleModelYear'] = pd.to_numeric(df_clean['VehicleModelYear'], errors='coerce')
           
           # Normalizar FIPE IDs
           if 'FipeID' in df_clean.columns:
               df_clean['FipeID'] = pd.to_numeric(df_clean['FipeID'], errors='coerce')
           
           # Criar campo de busca otimizado
           if all(col in df_clean.columns for col in ['BrandName', 'VehicleName']):
               df_clean['search_text'] = (
                   df_clean['BrandName'].fillna('') + ' ' + 
                   df_clean['VehicleName'].fillna('') + ' ' + 
                   df_clean.get('Abreviação de descrição', pd.Series([''] * len(df_clean))).fillna('')
               ).str.upper().str.strip()
           
       except Exception as e:
           print(f"Erro durante limpeza dos dados: {e}")
       
       return df_clean

class VehicleIndex:
   """
   Classe para criação e gerenciamento de índices de busca
   """
   
   def __init__(self, df: pd.DataFrame):
       self.df = df
       self.indexes = {}
       self.create_indexes()
   
   def create_indexes(self):
       """Cria índices otimizados para busca"""
       try:
           # Índice por FIPE ID
           if 'FipeID' in self.df.columns:
               self.indexes['fipe'] = self.df.set_index('FipeID').to_dict('index')
           
           # Índice por marca
           if 'BrandName' in self.df.columns:
               self.indexes['brand'] = {}
               for brand in self.df['BrandName'].dropna().unique():
                   brand_vehicles = self.df[self.df['BrandName'] == brand]
                   self.indexes['brand'][brand] = brand_vehicles.to_dict('records')
           
           # Índice por ano
           if 'VehicleModelYear' in self.df.columns:
               self.indexes['year'] = {}
               for year in self.df['VehicleModelYear'].dropna().unique():
                   year_vehicles = self.df[self.df['VehicleModelYear'] == year]
                   self.indexes['year'][int(year)] = year_vehicles.to_dict('records')
           
           # Índice por tipo de ADAS
           if 'ADAS' in self.df.columns:
               self.indexes['adas'] = {}
               for adas_status in self.df['ADAS'].dropna().unique():
                   adas_vehicles = self.df[self.df['ADAS'] == adas_status]
                   self.indexes['adas'][adas_status] = adas_vehicles.to_dict('records')
           
       except Exception as e:
           print(f"Erro ao criar índices: {e}")
   
   def get_by_fipe(self, fipe_id: int) -> Optional[Dict]:
       """Busca rápida por FIPE ID"""
       return self.indexes.get('fipe', {}).get(fipe_id)
   
   def get_by_brand(self, brand: str) -> List[Dict]:
       """Busca rápida por marca"""
       return self.indexes.get('brand', {}).get(brand.upper(), [])
   
   def get_by_year(self, year: int) -> List[Dict]:
       """Busca rápida por ano"""
       return self.indexes.get('year', {}).get(year, [])
   
   def get_stats(self) -> Dict:
       """Retorna estatísticas dos índices"""
       return {
           'total_vehicles': len(self.df),
           'fipe_index_size': len(self.indexes.get('fipe', {})),
           'brands_count': len(self.indexes.get('brand', {})),
           'years_count': len(self.indexes.get('year', {})),
           'adas_categories': list(self.indexes.get('adas', {}).keys())
       }

class VehicleDatabase:
   """
   Classe principal para gerenciamento da base de dados de veículos
   """
   
   def __init__(self, config: Dict = None):
       self.config = config or {
           'encoding': 'utf-8',
           'separator': ';',
           'cache_duration_hours': 24,
           'auto_validate': True,
           'auto_clean': True
       }
       
       self.df = None
       self.validator = DataValidator()
       self.index = None
       self.last_loaded = None
       self.validation_report = None
       self.load_stats = {}
   
   def load_from_csv(self, file_path: str = None, uploaded_file = None) -> bool:
       """
       Carrega dados de arquivo CSV
       """
       load_start_time = datetime.now()
       
       try:
           if uploaded_file is not None:
               # Carregar de arquivo enviado (Streamlit)
               self.df = pd.read_csv(
                   uploaded_file,
                   encoding=self.config['encoding'],
                   sep=self.config['separator']
               )
               source = "uploaded_file"
           elif file_path:
               # Carregar de arquivo local
               self.df = pd.read_csv(
                   file_path,
                   encoding=self.config['encoding'],
                   sep=self.config['separator']
               )
               source = file_path
           else:
               # Criar dados de demonstração
               self.df = self._create_demo_data()
               source = "demo_data"
           
           # Validar dados se configurado
           if self.config.get('auto_validate', True):
               self.validation_report = self.validator.validate_dataframe(self.df)
               
               if not self.validation_report['validation_passed']:
                   print("⚠️ Avisos encontrados durante validação:")
                   for error in self.validation_report['errors']:
                       print(f"  - {error}")
           
           # Limpar dados se configurado
           if self.config.get('auto_clean', True):
               self.df = self.validator.clean_dataframe(self.df)
           
           # Criar índices
           self.index = VehicleIndex(self.df)
           
           # Registrar estatísticas de carregamento
           load_time = (datetime.now() - load_start_time).total_seconds()
           self.load_stats = {
               'source': source,
               'load_time_seconds': round(load_time, 3),
               'total_rows': len(self.df),
               'total_columns': len(self.df.columns),
               'memory_usage_mb': round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
               'loaded_at': datetime.now().isoformat()
           }
           
           self.last_loaded = datetime.now()
           
           return True
           
       except Exception as e:
           print(f"❌ Erro ao carregar dados: {str(e)}")
           return False
   
   def _create_demo_data(self) -> pd.DataFrame:
       """Cria dados de demonstração"""
       demo_data = {
           'FipeID': [92983, 95432, 87621, 73291, 84512, 91234, 76543, 88901, 92345, 85678],
           'VehicleModelYear': [2024, 2023, 2024, 2025, 2023, 2024, 2023, 2025, 2024, 2023],
           'BrandName': ['BMW', 'VOLKSWAGEN', 'MERCEDES-BENZ', 'AUDI', 'TOYOTA', 
                        'VOLVO', 'FORD', 'HYUNDAI', 'JEEP', 'LAND ROVER'],
           'VehicleName': [
               '118i M Sport 1.5 TB 12V Aut. 5p',
               'Polo TSI 1.0 200 Aut. 5p',
               'A-Class A200 1.3 TB Aut.',
               'A3 Sedan 1.4 TFSI Aut.',
               'Corolla 2.0 XEi Aut.',
               'XC60 T5 Momentum AWD Aut.',
               'Territory 1.5 EcoBoost GTDi Aut.',
               'Tucson 1.6 GLS TB Aut.',
               'Compass 1.3 T270 Turbo Aut.',
               'Discovery Sport HSE 2.0 TD4 Aut.'
           ],
           'Abreviação de descrição': [
               '118i M Sport', 'Polo TSI', 'A200', 'A3 Sedan', 'Corolla XEi',
               'XC60 T5', 'Territory EcoBoost', 'Tucson GLS', 'Compass T270', 'Discovery Sport'
           ],
           'ADAS': ['Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim'],
           'ADAS no Parabrisa': ['Sim', 'Sim', 'Sim', 'Sim', 'Não', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim'],
           'Adas no Parachoque': ['Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim'],
           'Tipo de Regulagem': [
               'Dinamica', 'Estatica', 'Dinamica', 'Estatica/Dinamica', 'Dinamica',
               'Dinamica', 'Estatica', 'Dinamica', 'Estatica', 'Dinamica'
           ],
           'Camera no Retrovisor': ['Não', 'Sim', 'Sim', 'Não', 'Sim', 'Sim', 'Não', 'Sim', 'Sim', 'Sim'],
           'Faróis Matrix': ['Não', 'Não', 'Sim', 'Sim', 'Não', 'Sim', 'Não', 'Não', 'Sim', 'Sim']
       }
       
       return pd.DataFrame(demo_data)
   
   def get_vehicle_by_fipe(self, fipe_id: int) -> Optional[Dict]:
       """Busca veículo por FIPE ID"""
       if self.index:
           return self.index.get_by_fipe(fipe_id)
       return None
   
   def get_vehicles_by_brand(self, brand: str) -> List[Dict]:
       """Busca veículos por marca"""
       if self.index:
           return self.index.get_by_brand(brand)
       return []
   
   def get_vehicles_by_year(self, year: int) -> List[Dict]:
       """Busca veículos por ano"""
       if self.index:
           return self.index.get_by_year(year)
       return []
   
   def get_adas_statistics(self) -> Dict:
       """Retorna estatísticas de ADAS"""
       if self.df is None or self.df.empty:
           return {}
       
       stats = {}
       
       # Estatísticas gerais de ADAS
       if 'ADAS' in self.df.columns:
           adas_count = (self.df['ADAS'] == 'Sim').sum()
           stats['total_vehicles'] = len(self.df)
           stats['vehicles_with_adas'] = adas_count
           stats['adas_percentage'] = round((adas_count / len(self.df)) * 100, 2)
       
       # Estatísticas por tipo de calibração
       if 'Tipo de Regulagem' in self.df.columns:
           calibration_stats = self.df['Tipo de Regulagem'].value_counts().to_dict()
           stats['calibration_types'] = calibration_stats
       
       # Estatísticas por localização de ADAS
       if 'ADAS no Parabrisa' in self.df.columns:
           windshield_adas = (self.df['ADAS no Parabrisa'] == 'Sim').sum()
           stats['windshield_adas_count'] = windshield_adas
       
       if 'Adas no Parachoque' in self.df.columns:
           bumper_adas = (self.df['Adas no Parachoque'] == 'Sim').sum()
           stats['bumper_adas_count'] = bumper_adas
       
       # Top marcas com ADAS
       if 'BrandName' in self.df.columns and 'ADAS' in self.df.columns:
           brands_with_adas = self.df[self.df['ADAS'] == 'Sim']['BrandName'].value_counts().head(10)
           stats['top_brands_with_adas'] = brands_with_adas.to_dict()
       
       return stats
   
   def export_summary_report(self) -> Dict:
       """Exporta relatório resumido da base de dados"""
       report = {
           'generated_at': datetime.now().isoformat(),
           'database_info': self.load_stats,
           'validation_report': self.validation_report,
           'adas_statistics': self.get_adas_statistics(),
           'index_statistics': self.index.get_stats() if self.index else {},
           'data_sample': self.df.head(3).to_dict('records') if self.df is not None else []
       }
       
       return report
   
   def backup_to_json(self, file_path: str) -> bool:
       """Faz backup da base de dados em formato JSON"""
       try:
           if self.df is None:
               return False
           
           backup_data = {
               'metadata': {
                   'created_at': datetime.now().isoformat(),
                   'total_records': len(self.df),
                   'columns': list(self.df.columns),
                   'source': self.load_stats.get('source', 'unknown')
               },
               'data': self.df.to_dict('records')
           }
           
           with open(file_path, 'w', encoding='utf-8') as f:
               json.dump(backup_data, f, ensure_ascii=False, indent=2)
           
           return True
           
       except Exception as e:
           print(f"Erro ao fazer backup: {e}")
           return False
   
   def is_data_fresh(self) -> bool:
       """Verifica se os dados estão atualizados"""
       if not self.last_loaded:
           return False
       
       cache_duration = timedelta(hours=self.config.get('cache_duration_hours', 24))
       return datetime.now() - self.last_loaded < cache_duration
   
   def refresh_indexes(self):
       """Atualiza índices após modificações nos dados"""
       if self.df is not None:
           self.index = VehicleIndex(self.df)

# Função de teste
def test_vehicle_database():
   """Função para testar o sistema de base de dados"""
   print("=== TESTE VEHICLE DATABASE ===")
   
   # Criar instância
   db = VehicleDatabase()
   
   # Carregar dados de demonstração
   success = db.load_from_csv()
   print(f"Carregamento: {'✅ Sucesso' if success else '❌ Falha'}")
   
   if success:
       # Testar busca por FIPE
       bmw = db.get_vehicle_by_fipe(92983)
       print(f"Busca por FIPE 92983: {'✅ Encontrado' if bmw else '❌ Não encontrado'}")
       
       # Testar estatísticas
       stats = db.get_adas_statistics()
       print(f"Estatísticas ADAS: {stats.get('vehicles_with_adas', 0)} veículos")
       
       # Testar relatório
       report = db.export_summary_report()
       print(f"Relatório gerado: {len(report)} seções")
   
   return db

if __name__ == "__main__":
   test_vehicle_database()
