import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from .data_processor import DataProcessor
from .bosch_scraper import BoschScraper

class SearchEngine:
    def __init__(self, csv_path: str, json_path: str):
        self.csv_path = csv_path
        self.json_path = json_path
        self.df = None
        self.bosch_mapping = None
        self.load_data()
    
    def load_data(self):
        """Carrega dados processados e mapeamento Bosch"""
        try:
            # Carregar dados CSV
            self.df = pd.read_csv(self.csv_path)
            print(f"Dados carregados: {len(self.df)} registros")
            
            # Carregar mapeamento Bosch
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.bosch_mapping = json.load(f)
            print("Mapeamento Bosch carregado")
            
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
    
    def search_by_fipe(self, fipe_id: str) -> List[Dict]:
        """Busca veículo por código FIPE"""
        if self.df is None:
            return []
        
        try:
            fipe_int = int(fipe_id)
            results = self.df[self.df['FipeID'] == fipe_int]
            return self._enrich_results(results.to_dict('records'))
        except ValueError:
            return []
    
    def search_by_text(self, query: str, limit: int = 50) -> List[Dict]:
        """Busca veículos por texto livre"""
        if self.df is None:
            return []
        
        query = query.upper().strip()
        if not query:
            return []
        
        # Buscar em múltiplas colunas
        mask = (
            self.df['BrandName'].str.upper().str.contains(query, na=False) |
            self.df['VehicleName'].str.upper().str.contains(query, na=False) |
            self.df['Abreviação de descrição'].str.upper().str.contains(query, na=False)
        )
        
        results = self.df[mask].head(limit)
        return self._enrich_results(results.to_dict('records'))
    
    def search_by_brand_model(self, brand: str = None, model: str = None, 
                             year: int = None, limit: int = 50) -> List[Dict]:
        """Busca por marca, modelo e/ou ano"""
        if self.df is None:
            return []
        
        mask = pd.Series([True] * len(self.df))
        
        if brand:
            mask &= self.df['BrandName'].str.upper().str.contains(brand.upper(), na=False)
        
        if model:
            mask &= self.df['VehicleName'].str.upper().str.contains(model.upper(), na=False)
        
        if year:
            mask &= self.df['VehicleModelYear'] == year
        
        results = self.df[mask].head(limit)
        return self._enrich_results(results.to_dict('records'))
    
    def _enrich_results(self, results: List[Dict]) -> List[Dict]:
        """Enriquece resultados com informações de calibração Bosch"""
        enriched_results = []
        
        for result in results:
            # Adicionar informações de ADAS
            result['adas_info'] = self._get_adas_info(result)
            
            # Adicionar informações de calibração Bosch
            brand = result.get('BrandName', '')
            result['calibration_info'] = self._get_calibration_info(brand)
            
            enriched_results.append(result)
        
        return enriched_results
    
    def _get_adas_info(self, vehicle_data: Dict) -> Dict:
        """Extrai informações de ADAS do veículo"""
        return {
            'has_adas': vehicle_data.get('ADAS', '').upper() == 'SIM',
            'adas_windshield': vehicle_data.get('ADAS no Parabrisa', '').upper() == 'SIM',
            'adas_bumper': vehicle_data.get('Adas no Parachoque', '').upper() == 'SIM',
            'camera_mirror': vehicle_data.get('Camera no Retrovisor', '').upper() == 'SIM',
            'matrix_lights': vehicle_data.get('Faróis Matrix', '').upper() == 'SIM',
            'regulation_type': vehicle_data.get('Tipo de Regulagem', '')
        }
    
    def _get_calibration_info(self, brand: str) -> Dict:
        """Obtém informações de calibração da Bosch para a marca"""
        if not self.bosch_mapping:
            return {'available': False, 'message': 'Mapeamento Bosch não disponível'}
        
        brand_mapping = self.bosch_mapping.get('brand_mapping', {})
        bosch_brand = brand_mapping.get(brand.upper())
        
        if not bosch_brand:
            return {
                'available': False,
                'brand': brand,
                'bosch_brand': None,
                'message': f'Informações de calibração não disponíveis para {brand}',
                'calibration_types': []
            }
        
        calibration_details = self.bosch_mapping.get('calibration_details', {})
        calibration_types = calibration_details.get(bosch_brand, [])
        
        return {
            'available': True,
            'brand': brand,
            'bosch_brand': bosch_brand,
            'message': f'Informações de calibração disponíveis para {bosch_brand}',
            'calibration_types': calibration_types,
            'documentation_url': self.bosch_mapping.get('base_url', '')
        }
    
    def get_brands(self) -> List[str]:
        """Retorna lista de marcas disponíveis"""
        if self.df is None:
            return []
        return sorted(self.df['BrandName'].unique().tolist())
    
    def get_models_by_brand(self, brand: str) -> List[str]:
        """Retorna modelos de uma marca"""
        if self.df is None:
            return []
        
        brand_data = self.df[self.df['BrandName'].str.upper() == brand.upper()]
        return sorted(brand_data['VehicleName'].unique().tolist())
    
    def get_years_by_brand_model(self, brand: str, model: str) -> List[int]:
        """Retorna anos disponíveis para marca/modelo"""
        if self.df is None:
            return []
        
        mask = (
            self.df['BrandName'].str.upper() == brand.upper()
        ) & (
            self.df['VehicleName'].str.upper().str.contains(model.upper(), na=False)
        )
        
        years = self.df[mask]['VehicleModelYear'].unique()
        return sorted([int(year) for year in years if pd.notna(year)])
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas dos dados"""
        if self.df is None:
            return {}
        
        total_vehicles = len(self.df)
        vehicles_with_adas = len(self.df[self.df['ADAS'].str.upper() == 'SIM'])
        unique_brands = self.df['BrandName'].nunique()
        unique_models = self.df['VehicleName'].nunique()
        
        return {
            'total_vehicles': total_vehicles,
            'vehicles_with_adas': vehicles_with_adas,
            'adas_percentage': round((vehicles_with_adas / total_vehicles) * 100, 2),
            'unique_brands': unique_brands,
            'unique_models': unique_models,
            'year_range': {
                'min': int(self.df['VehicleModelYear'].min()),
                'max': int(self.df['VehicleModelYear'].max())
            }
        }

if __name__ == "__main__":
    # Teste do motor de busca
    engine = SearchEngine(
        '/home/ubuntu/adas_calibration_system/data/processed_data.csv',
        '/home/ubuntu/adas_calibration_system/data/bosch_mapping.json'
    )
    
    # Teste de busca por FIPE
    results = engine.search_by_fipe('5092272')
    print(f"Busca por FIPE: {len(results)} resultados")
    if results:
        print("Primeiro resultado:", results[0]['VehicleName'])
        print("Tem ADAS:", results[0]['adas_info']['has_adas'])
        print("Calibração disponível:", results[0]['calibration_info']['available'])
    
    # Teste de busca por texto
    results = engine.search_by_text('POLO TSI')
    print(f"Busca por 'POLO TSI': {len(results)} resultados")
    
    # Estatísticas
    stats = engine.get_statistics()
    print(f"Estatísticas: {stats['vehicles_with_adas']} de {stats['total_vehicles']} veículos têm ADAS ({stats['adas_percentage']}%)")

