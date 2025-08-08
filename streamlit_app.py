import streamlit as st
import pandas as pd
import json
from typing import Dict, List
import os

# Configuração da página
st.set_page_config(
    page_title="Sistema de Calibração ADAS",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Classe SearchEngine simplificada
class SearchEngine:
    def __init__(self, csv_path: str, json_path: str):
        self.csv_path = csv_path
        self.json_path = json_path
        self.df = None
        self.bosch_mapping = None
        self.load_data()
    
    def load_data(self):
        try:
            self.df = pd.read_csv(self.csv_path)
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.bosch_mapping = json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
    
    def search_by_fipe(self, fipe_id: str) -> List[Dict]:
        if self.df is None:
            return []
        try:
            fipe_int = int(fipe_id)
            results = self.df[self.df['FipeID'] == fipe_int]
            return self._enrich_results(results.to_dict('records'))
        except ValueError:
            return []
    
    def search_by_text(self, query: str, limit: int = 50) -> List[Dict]:
        if self.df is None:
            return []
        
        query = query.upper().strip()
        if not query:
            return []
        
        mask = (
            self.df['BrandName'].str.upper().str.contains(query, na=False) |
            self.df['VehicleName'].str.upper().str.contains(query, na=False) |
            self.df['Abreviação de descrição'].str.upper().str.contains(query, na=False)
        )
        
        results = self.df[mask].head(limit)
        return self._enrich_results(results.to_dict('records'))
    
    def search_by_brand_model(self, brand: str = None, model: str = None, 
                             year: int = None, limit: int = 50) -> List[Dict]:
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
            'adas_bumper': vehicle_data.get('Adas no Parachoque', '').upper() == 'SIM',
            'camera_mirror': vehicle_data.get('Camera no Retrovisor', '').upper() == 'SIM',
            'matrix_lights': vehicle_data.get('Faróis Matrix', '').upper() == 'SIM',
            'regulation_type': vehicle_data.get('Tipo de Regulagem', '')
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
        if self.df is None:
            return []
        return sorted(self.df['BrandName'].unique().tolist())
    
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

# Inicializar motor de busca
@st.cache_resource
def get_search_engine():
    return SearchEngine('data/processed_data.csv', 'data/bosch_mapping.json')

def main():
    st.title("🚗 Sistema de Calibração ADAS")
    st.markdown("**Sistema inteligente para consulta de informações sobre calibração de sistemas ADAS**")
    
    # Carregar motor de busca
    search_engine = get_search_engine()
    
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
    
    # Abas principais
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            brands = search_engine.get_brands()
            selected_brand = st.selectbox("Marca:", [""] + brands)
        
        with col2:
            search_text = st.text_input("Modelo/Texto:", placeholder="Ex: POLO TSI")
        
        with col3:
            year = st.number_input("Ano:", min_value=1990, max_value=2030, value=None, step=1)
        
        search_vehicle = st.button("🔍 Buscar Veículo", key="search_vehicle")
        
        if search_vehicle:
            with st.spinner("Buscando veículos..."):
                if search_text:
                    results = search_engine.search_by_text(search_text)
                elif selected_brand:
                    results = search_engine.search_by_brand_model(brand=selected_brand, year=year)
                else:
                    st.warning("Por favor, selecione uma marca ou digite um texto para busca.")
                    results = []
                
                if results:
                    # Filtrar por marca se selecionada
                    if selected_brand:
                        results = [r for r in results if r['BrandName'].upper() == selected_brand.upper()]
                    
                    # Filtrar por ano se especificado
                    if year:
                        results = [r for r in results if r['VehicleModelYear'] == year]
                
                display_results(results, f"Busca: {search_text or selected_brand}")
    
    with tab3:
        st.header("Sobre o Sistema")
        stats = search_engine.get_statistics()
        st.markdown(f"""
        ### 🎯 Objetivo
        Este sistema permite consultar informações sobre calibração de sistemas ADAS (Advanced Driver Assistance Systems) 
        em veículos, integrando dados da tabela FIPE com a documentação técnica da Bosch.
        
        ### 🔧 Funcionalidades
        - **Busca por código FIPE**: Consulta direta usando o código FIPE do veículo
        - **Busca por marca/modelo**: Busca flexível por marca, modelo ou texto livre
        - **Informações ADAS**: Verifica se o veículo possui sistemas ADAS
        - **Instruções de calibração**: Fornece procedimentos específicos por marca
        - **Links para documentação**: Acesso direto à documentação técnica da Bosch
        
        ### 📊 Base de Dados
        - **{stats.get('total_vehicles', 0):,} veículos** cadastrados
        - **{stats.get('vehicles_with_adas', 0):,} veículos com ADAS** ({stats.get('adas_percentage', 0):.1f}%)
        - **{stats.get('unique_brands', 0)} marcas** diferentes
        - Integração com documentação Bosch DAS 3000
        
        ### 🔗 Links Úteis
        - [Documentação Bosch ADAS](https://help.boschdiagnostics.com/DAS3000/#/home/Onepager/pt/default)
        - [Tabela FIPE](https://veiculos.fipe.org.br/)
        """)

def display_results(results: List[Dict], search_term: str):
    """Exibe resultados da busca"""
    if not results:
        st.warning(f"Nenhum resultado encontrado para: {search_term}")
        return
    
    st.success(f"Encontrados **{len(results)}** resultados para: {search_term}")
    
    # Filtros adicionais
    col1, col2 = st.columns(2)
    with col1:
        only_adas = st.checkbox("Apenas veículos com ADAS")
    with col2:
        only_calibration = st.checkbox("Apenas com informações de calibração")
    
    # Aplicar filtros
    filtered_results = results
    if only_adas:
        filtered_results = [r for r in filtered_results if r['adas_info']['has_adas']]
    if only_calibration:
        filtered_results = [r for r in filtered_results if r['calibration_info']['available']]
    
    if not filtered_results:
        st.warning("Nenhum resultado após aplicar os filtros.")
        return
    
    st.info(f"Exibindo **{len(filtered_results)}** resultados após filtros")
    
    # Exibir resultados
    for i, result in enumerate(filtered_results[:20]):  # Limitar a 20 resultados
        with st.expander(f"🚗 {result['BrandName']} {result['VehicleName']} ({result['VehicleModelYear']})"):
            display_vehicle_details(result)

def display_vehicle_details(vehicle: Dict):
    """Exibe detalhes de um veículo"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Informações do Veículo")
        st.write(f"**Código FIPE:** {vehicle['FipeID']}")
        st.write(f"**Marca:** {vehicle['BrandName']}")
        st.write(f"**Modelo:** {vehicle['VehicleName']}")
        st.write(f"**Ano:** {vehicle['VehicleModelYear']}")
        st.write(f"**Descrição:** {vehicle.get('Abreviação de descrição', 'N/A')}")
        
        # Status ADAS
        st.subheader("🛡️ Status ADAS")
        adas_info = vehicle['adas_info']
        
        if adas_info['has_adas']:
            st.success("✅ Veículo possui ADAS")
        else:
            st.error("❌ Veículo não possui ADAS")
        
        # Detalhes ADAS
        adas_details = []
        if adas_info['adas_windshield']:
            adas_details.append("🪟 ADAS no Parabrisa")
        if adas_info['adas_bumper']:
            adas_details.append("🚗 ADAS no Parachoque")
        if adas_info['camera_mirror']:
            adas_details.append("📹 Câmera no Retrovisor")
        if adas_info['matrix_lights']:
            adas_details.append("💡 Faróis Matrix")
        
        if adas_details:
            st.write("**Componentes ADAS:**")
            for detail in adas_details:
                st.write(f"- {detail}")
        
        if adas_info['regulation_type']:
            st.write(f"**Tipo de Regulagem:** {adas_info['regulation_type']}")
    
    with col2:
        st.subheader("🔧 Informações de Calibração")
        calibration_info = vehicle['calibration_info']
        
        if calibration_info['available']:
            st.success(f"✅ {calibration_info['message']}")
            
            if calibration_info['calibration_types']:
                st.write("**Tipos de Calibração Disponíveis:**")
                
                for cal_type in calibration_info['calibration_types']:
                    with st.container():
                        st.write(f"**{cal_type['type']}**")
                        st.write(f"- {cal_type['description']}")
                        st.write(f"- **Equipamentos:** {', '.join(cal_type['equipment'])}")
                        st.write(f"- **Categoria:** {cal_type['category']}")
                        st.write("---")
            
            # Link para documentação
            if calibration_info.get('documentation_url'):
                st.markdown(f"[📖 Acessar Documentação Bosch]({calibration_info['documentation_url']})")
        else:
            st.warning(f"⚠️ {calibration_info['message']}")
            st.info("💡 Verifique se há atualizações na documentação Bosch ou consulte o fabricante.")

if __name__ == "__main__":
    main()
