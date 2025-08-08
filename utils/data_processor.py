import pandas as pd
import json
import re
from typing import Dict, List, Optional

class DataProcessor:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        
    def load_data(self) -> pd.DataFrame:
        """Carrega dados do Excel"""
        try:
            self.df = pd.read_excel(self.excel_path, sheet_name='NOVO SISTEMA TMD')
            print(f"Dados carregados: {len(self.df)} registros")
            return self.df
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return None
    
    def clean_data(self) -> pd.DataFrame:
        """Limpa e normaliza os dados"""
        if self.df is None:
            return None
            
        # Normalizar valores de ADAS
        self.df['ADAS'] = self.df['ADAS'].str.upper().replace({'NÃO': 'NÃO', 'SIM': 'SIM'})
        self.df['ADAS no Parabrisa'] = self.df['ADAS no Parabrisa'].str.upper().replace({'NÃO': 'NÃO', 'SIM': 'SIM'})
        self.df['Adas no Parachoque'] = self.df['Adas no Parachoque'].str.upper().replace({'NÃO': 'NÃO', 'sim': 'SIM'})
        
        # Limpar espaços em branco
        string_columns = ['BrandName', 'VehicleName', 'Abreviação de descrição']
        for col in string_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
        
        # Remover registros com FIPE ID inválido
        self.df = self.df[self.df['FipeID'].notna()]
        
        print(f"Dados limpos: {len(self.df)} registros")
        return self.df
    
    def create_search_index(self) -> Dict:
        """Cria índices para busca rápida"""
        if self.df is None:
            return {}
            
        # Índice por FIPE ID
        fipe_index = {}
        for _, row in self.df.iterrows():
            fipe_id = str(int(row['FipeID']))
            if fipe_id not in fipe_index:
                fipe_index[fipe_id] = []
            fipe_index[fipe_id].append(row.to_dict())
        
        # Índice por marca
        brand_index = {}
        for _, row in self.df.iterrows():
            brand = row['BrandName'].upper()
            if brand not in brand_index:
                brand_index[brand] = []
            brand_index[brand].append(row.to_dict())
        
        return {
            'fipe': fipe_index,
            'brand': brand_index
        }
    
    def get_vehicle_info(self, fipe_id: str) -> List[Dict]:
        """Busca informações de um veículo por FIPE ID"""
        if self.df is None:
            return []
            
        results = self.df[self.df['FipeID'] == int(fipe_id)]
        return results.to_dict('records')
    
    def search_vehicles(self, query: str, limit: int = 50) -> List[Dict]:
        """Busca veículos por texto"""
        if self.df is None:
            return []
            
        query = query.upper()
        
        # Buscar por marca, modelo ou descrição
        mask = (
            self.df['BrandName'].str.upper().str.contains(query, na=False) |
            self.df['VehicleName'].str.upper().str.contains(query, na=False) |
            self.df['Abreviação de descrição'].str.upper().str.contains(query, na=False)
        )
        
        results = self.df[mask].head(limit)
        return results.to_dict('records')
    
    def get_brands(self) -> List[str]:
        """Retorna lista de marcas únicas"""
        if self.df is None:
            return []
        return sorted(self.df['BrandName'].unique().tolist())
    
    def get_models_by_brand(self, brand: str) -> List[str]:
        """Retorna modelos de uma marca específica"""
        if self.df is None:
            return []
        brand_data = self.df[self.df['BrandName'].str.upper() == brand.upper()]
        return sorted(brand_data['VehicleName'].unique().tolist())
    
    def has_adas(self, vehicle_data: Dict) -> Dict[str, bool]:
        """Verifica quais tipos de ADAS o veículo possui"""
        return {
            'adas_geral': vehicle_data.get('ADAS', '').upper() == 'SIM',
            'adas_parabrisa': vehicle_data.get('ADAS no Parabrisa', '').upper() == 'SIM',
            'adas_parachoque': vehicle_data.get('Adas no Parachoque', '').upper() == 'SIM',
            'camera_retrovisor': vehicle_data.get('Camera no Retrovisor', '').upper() == 'SIM',
            'farois_matrix': vehicle_data.get('Faróis Matrix', '').upper() == 'SIM'
        }
    
    def save_processed_data(self, output_path: str):
        """Salva dados processados em CSV"""
        if self.df is None:
            return False
            
        try:
            # Selecionar colunas principais
            columns_to_save = [
                'FipeID', 'VehicleModelYear', 'BrandName', 'VehicleName',
                'Abreviação de descrição', 'ADAS', 'ADAS no Parabrisa',
                'Adas no Parachoque', 'Tipo de Regulagem', 'Camera no Retrovisor',
                'Faróis Matrix'
            ]
            
            df_to_save = self.df[columns_to_save].copy()
            df_to_save.to_csv(output_path, index=False, encoding='utf-8')
            print(f"Dados salvos em: {output_path}")
            return True
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
            return False

if __name__ == "__main__":
    # Teste do processador
    processor = DataProcessor('/home/ubuntu/upload/TMD_v3.xlsx')
    processor.load_data()
    processor.clean_data()
    processor.save_processed_data('/home/ubuntu/adas_calibration_system/data/processed_data.csv')
    
    # Teste de busca
    results = processor.search_vehicles('POLO')
    print(f"Encontrados {len(results)} resultados para 'POLO'")
    if results:
        print("Primeiro resultado:", results[0]['VehicleName'])

