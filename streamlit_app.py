import streamlit as st
import pandas as pd
import json
import gzip
from typing import Dict, List
import os

# Configuração da página
st.set_page_config(
    page_title="Sistema de Calibração ADAS - Versão Leve",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Classe SearchEngine otimizada
class SearchEngineLight:
    def __init__(self, csv_path: str, json_path: str):
        self.csv_path = csv_path
        self.json_path = json_path
        self.df = None
        self.bosch_mapping = None
        self.load_data()
    
    def load_data(self):
        try:
            # Carregar dados CSV (suporta gzip)
            if self.csv_path.endswith('.gz'):
                self.df = pd.read_csv(self.csv_path, compression='gzip')
            else:
                self.df = pd.read_csv(self.csv_path)
            
            # Carregar mapeamento Bosch
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.bosch_mapping = json.load(f)
                
            st.success(f"✅ Dados carregados: {len(self.df):,} registros")
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {e}")
    
    def search_by_fipe(self, fipe_id: str) -> List[Dict]:
        if self.df is None:
            return []
        try:
            fipe_int = int(fipe_id)
            results = self.df[self.df['FipeID'] == fipe_int]
            return self._enrich_results(results.to_dict('records'))
        except ValueError:
            return []
    
    def search_by_text(self, query: str, limit: int = 20) -> List[Dict]:
        if self.df is None:
            return []
        
        query = query.upper().strip()
        if not query:
            return []
        
        # Buscar apenas nas colunas essenciais para performance
        mask = (
            self.df['BrandName'].str.upper().str.contains(query, na=False) |
            self.df['VehicleName'].str.upper().str.contains(query, na=False)
        )
        
        results = self.df[mask].head(limit)
        return self._enrich_results(results.to_dict('records'))
    
    def _enrich_results(self, results: List[Dict]) -> List[Dict]:
        enriched_results = []
        
        for result in results:
            result['adas_info'] = self._get_adas_info(result)
            brand = result.get('BrandName', '')
            result['calibration_info'] = self._get_calibration_info(brand)
            enriched_results.append(result)
        
        return enriched_results
    
    def _get_adas_info(self, vehicle_data: Dict) -> Dict:
        return {
            'has_adas': vehicle_data.get('ADAS', '').upper() == 'SIM',
            'adas_windshield': vehicle_data.get('ADAS no Parabrisa', '').upper() == 'SIM',
            'adas_bumper': vehicle_data.get('Adas no Parachoque', '').upper() == 'SIM'
        }
    
    def _get_calibration_info(self, brand: str) -> Dict:
        if not self.bosch_mapping:
            return {'available': False, 'message': 'Mapeamento Bosch não disponível'}
        
        brand_mapping = self.bosch_mapping.get('brand_mapping', {})
        bosch_brand = brand_mapping.get(brand.upper())
        
        if not bosch_brand:
            return {
                'available': False,
                'brand': brand,
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
    
    def get_statistics(self) -> Dict:
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

# Função para detectar qual arquivo usar
def get_data_file():
    """Detecta qual arquivo de dados usar baseado na disponibilidade"""
    data_options = [
        ('processed_data_compressed.csv.gz', 'Dados Completos Comprimidos (0.3MB)'),
        ('processed_data_adas_only.csv', 'Apenas Veículos com ADAS (6.4MB)'),
        ('processed_data_sample.csv', 'Amostra de 10k Veículos (0.9MB)'),
        ('processed_data_optimized.csv', 'Dados Otimizados (18.5MB)')
    ]
    
    for filename, description in data_options:
        if os.path.exists(filename):
            return filename, description
    
    return None, None

# Inicializar aplicação
@st.cache_resource
def get_search_engine():
    data_file, description = get_data_file()
    if data_file:
        st.info(f"📊 Usando: {description}")
        return SearchEngineLight(data_file, '/home/ubuntu/adas_calibration_system/data/bosch_mapping.json')
    else:
        st.error("❌ Nenhum arquivo de dados encontrado!")
        return None

def main():
    st.title("🚗 Sistema de Calibração ADAS - Versão Leve")
    st.markdown("**Versão otimizada para melhor performance**")
    
    # Carregar motor de busca
    search_engine = get_search_engine()
    if not search_engine:
        st.stop()
    
    # Sidebar com estatísticas
    with st.sidebar:
        st.header("📊 Estatísticas")
        stats = search_engine.get_statistics()
        if stats:
            st.metric("Total de Veículos", f"{stats['total_vehicles']:,}")
            st.metric("Veículos com ADAS", f"{stats['vehicles_with_adas']:,}")
            st.metric("Percentual ADAS", f"{stats['adas_percentage']}%")
            st.metric("Marcas Únicas", stats['unique_brands'])
            st.metric("Modelos Únicos", stats['unique_models'])
            st.write(f"**Anos:** {stats['year_range']['min']} - {stats['year_range']['max']}")
    
    # Interface principal
    tab1, tab2, tab3 = st.tabs(["🔍 Busca por FIPE", "🚙 Busca por Veículo", "ℹ️ Sobre"])
    
    with tab1:
        st.header("Busca por Código FIPE")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            fipe_id = st.text_input("Digite o código FIPE:", placeholder="Ex: 5092272")
        with col2:
            search_fipe = st.button("🔍 Buscar", key="search_fipe")
        
        if search_fipe and fipe_id:
            with st.spinner("Buscando informações..."):
                results = search_engine.search_by_fipe(fipe_id)
                display_results(results, f"Código FIPE: {fipe_id}")
    
    with tab2:
        st.header("Busca por Marca/Modelo")
        
        search_text = st.text_input("Digite marca ou modelo:", placeholder="Ex: POLO, MERCEDES, AUDI")
        search_vehicle = st.button("🔍 Buscar Veículo", key="search_vehicle")
        
        if search_vehicle and search_text:
            with st.spinner("Buscando veículos..."):
                results = search_engine.search_by_text(search_text, limit=20)
                display_results(results, f"Busca: {search_text}")
    
    with tab3:
        st.header("Sobre o Sistema - Versão Leve")
        stats = search_engine.get_statistics()
        st.markdown(f"""
        ### 🎯 Versão Otimizada
        Esta é uma versão leve do sistema, otimizada para melhor performance e menor uso de recursos.
        
        ### 📊 Base de Dados Atual
        - **{stats.get('total_vehicles', 0):,} veículos** cadastrados
        - **{stats.get('vehicles_with_adas', 0):,} veículos com ADAS** ({stats.get('adas_percentage', 0):.1f}%)
        - **{stats.get('unique_brands', 0)} marcas** diferentes
        - Integração com documentação Bosch DAS 3000
        
        ### 🚀 Melhorias desta Versão
        - **Arquivo comprimido**: Redução de 26MB para 0.3MB
        - **Carregamento rápido**: Sem travamentos
        - **Busca otimizada**: Resultados limitados para melhor performance
        - **Interface responsiva**: Funciona em qualquer dispositivo
        
        ### 🔗 Links Úteis
        - [Documentação Bosch ADAS](https://help.boschdiagnostics.com/DAS3000/#/home/Onepager/pt/default)
        - [Tabela FIPE](https://veiculos.fipe.org.br/)
        """)

def display_results(results: List[Dict], search_term: str):
    """Exibe resultados da busca de forma otimizada"""
    if not results:
        st.warning(f"Nenhum resultado encontrado para: {search_term}")
        return
    
    st.success(f"Encontrados **{len(results)}** resultados para: {search_term}")
    
    # Filtro apenas ADAS
    only_adas = st.checkbox("Apenas veículos com ADAS")
    
    # Aplicar filtro
    filtered_results = results
    if only_adas:
        filtered_results = [r for r in filtered_results if r['adas_info']['has_adas']]
    
    if not filtered_results:
        st.warning("Nenhum resultado após aplicar os filtros.")
        return
    
    st.info(f"Exibindo **{len(filtered_results)}** resultados")
    
    # Exibir resultados de forma compacta
    for i, result in enumerate(filtered_results):
        with st.expander(f"🚗 {result['BrandName']} {result['VehicleName']} ({result['VehicleModelYear']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**FIPE:** {result['FipeID']}")
                st.write(f"**Marca:** {result['BrandName']}")
                st.write(f"**Modelo:** {result['VehicleName']}")
                st.write(f"**Ano:** {result['VehicleModelYear']}")
                
                # Status ADAS simplificado
                if result['adas_info']['has_adas']:
                    st.success("✅ Possui ADAS")
                else:
                    st.error("❌ Não possui ADAS")
            
            with col2:
                calibration_info = result['calibration_info']
                if calibration_info['available']:
                    st.success(f"✅ Calibração: {calibration_info['bosch_brand']}")
                    if calibration_info.get('documentation_url'):
                        st.markdown(f"[📖 Ver Documentação]({calibration_info['documentation_url']})")
                else:
                    st.warning("⚠️ Sem informações de calibração")

if __name__ == "__main__":
    main()
