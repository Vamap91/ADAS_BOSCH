import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from fuzzywuzzy import fuzz, process
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Optional, Tuple
import hashlib
import json
import os

# Configuração da página
st.set_page_config(
    page_title="Sistema de Calibração ADAS",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class VehicleDatabase:
    """Classe para gerenciamento da base de dados de veículos"""
    
    def __init__(self, csv_file_path: str):
        self.df = None
        self.brand_index = {}
        self.model_index = {}
        self.fipe_index = {}
        self.cache = {}
        self.load_data(csv_file_path)
        self.create_indexes()
    
    def load_data(self, csv_file_path: str):
        """Carrega os dados do CSV"""
        try:
            self.df = pd.read_csv(csv_file_path, encoding='utf-8', sep=';')
            # Limpar dados
            self.df['BrandName'] = self.df['BrandName'].str.strip().str.upper()
            self.df['VehicleName'] = self.df['VehicleName'].str.strip()
            self.df['Abreviação de descrição'] = self.df['Abreviação de descrição'].str.strip()
            st.success(f"✅ Base de dados carregada: {len(self.df)} veículos")
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {str(e)}")
    
    def create_indexes(self):
        """Cria índices para busca rápida"""
        if self.df is not None:
            # Índice por FIPE ID
            self.fipe_index = self.df.set_index('FipeID').to_dict('index')
            
            # Índice por marca
            for _, row in self.df.iterrows():
                brand = row['BrandName']
                if brand not in self.brand_index:
                    self.brand_index[brand] = []
                self.brand_index[brand].append(row.to_dict())
            
            # Índice por modelo (abreviação)
            for _, row in self.df.iterrows():
                model = row['Abreviação de descrição']
                if pd.notna(model):
                    if model not in self.model_index:
                        self.model_index[model] = []
                    self.model_index[model].append(row.to_dict())

class IntelligentSearch:
    """Sistema de busca inteligente"""
    
    def __init__(self, vehicle_db: VehicleDatabase):
        self.db = vehicle_db
        self.model = None
        self.load_sentence_transformer()
    
    def load_sentence_transformer(self):
        """Carrega modelo de embeddings (opcional - fallback para fuzzy)"""
        try:
            # Comentado para evitar dependência pesada inicialmente
            # self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            pass
        except:
            pass
    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto para busca"""
        text = text.upper().strip()
        # Remove acentos
        replacements = {
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A',
            'É': 'E', 'Ê': 'E', 'Í': 'I', 'Ó': 'O',
            'Ô': 'O', 'Õ': 'O', 'Ú': 'U', 'Ü': 'U',
            'Ç': 'C'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def search_by_fipe(self, fipe_id: str) -> Optional[Dict]:
        """Busca por código FIPE"""
        try:
            fipe_int = int(fipe_id)
            return self.db.fipe_index.get(fipe_int)
        except:
            return None
    
    def search_by_brand_model(self, query: str) -> List[Dict]:
        """Busca por marca e modelo"""
        query_norm = self.normalize_text(query)
        results = []
        
        # Buscar em todas as linhas
        for _, row in self.db.df.iterrows():
            score = 0
            brand_norm = self.normalize_text(row['BrandName'])
            model_norm = self.normalize_text(row['VehicleName'])
            abbrev_norm = self.normalize_text(str(row['Abreviação de descrição']))
            
            # Score por marca
            if brand_norm in query_norm:
                score += 50
            
            # Score por modelo
            score += fuzz.partial_ratio(query_norm, model_norm)
            
            # Score por abreviação
            if pd.notna(row['Abreviação de descrição']):
                score += fuzz.ratio(query_norm, abbrev_norm)
            
            if score > 70:  # Threshold de relevância
                result = row.to_dict()
                result['search_score'] = score
                results.append(result)
        
        # Ordenar por score
        results = sorted(results, key=lambda x: x['search_score'], reverse=True)
        return results[:10]  # Top 10 resultados

class BoschIntegration:
    """Integração com o site da Bosch para instruções de calibração"""
    
    def __init__(self):
        self.base_url = "https://help.boschdiagnostics.com/DAS3000/#/home/Onepager/pt/default"
        self.cache_file = "bosch_cache.json"
        self.cache = self.load_cache()
    
    def load_cache(self) -> Dict:
        """Carrega cache de instruções"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_cache(self):
        """Salva cache de instruções"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def get_calibration_instructions(self, brand: str, model: str) -> Dict:
        """Obtém instruções de calibração do site da Bosch"""
        cache_key = f"{brand.upper()}_{model.upper()}"
        
        # Verificar cache primeiro
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Por enquanto, retornar instruções genéricas baseadas no tipo de regulagem
        # TODO: Implementar scraping específico do site da Bosch
        
        generic_instructions = {
            "Dinamica": {
                "title": "Calibração Dinâmica",
                "steps": [
                    "1. Verificar alinhamento das rodas",
                    "2. Conectar equipamento de diagnóstico",
                    "3. Realizar test drive em pista específica",
                    "4. Seguir protocolo de calibração dinâmica",
                    "5. Validar funcionamento dos sistemas ADAS"
                ],
                "requirements": [
                    "Pista de calibração específica",
                    "Condições climáticas adequadas",
                    "Equipamento DAS 3000 ou similar"
                ]
            },
            "Estática": {
                "title": "Calibração Estática",
                "steps": [
                    "1. Posicionar veículo em superfície plana",
                    "2. Instalar targets de calibração",
                    "3. Conectar equipamento de diagnóstico",
                    "4. Executar procedimento de calibração estática",
                    "5. Verificar alinhamento dos sensores"
                ],
                "requirements": [
                    "Superfície plana e nivelada",
                    "Targets de calibração específicos",
                    "Ambiente controlado (iluminação)"
                ]
            }
        }
        
        # Cache e retorna instrução genérica
        instruction = generic_instructions.get("Dinamica")  # Default
        self.cache[cache_key] = instruction
        self.save_cache()
        
        return instruction

class ADASCalibrationSystem:
    """Sistema principal de calibração ADAS"""
    
    def __init__(self):
        self.vehicle_db = None
        self.search_engine = None
        self.bosch_integration = BoschIntegration()
        
    def initialize(self, csv_path: str):
        """Inicializa o sistema"""
        self.vehicle_db = VehicleDatabase(csv_path)
        self.search_engine = IntelligentSearch(self.vehicle_db)
    
    def search_vehicle(self, query: str) -> Tuple[List[Dict], str]:
        """Busca veículo por query"""
        if not query.strip():
            return [], "Por favor, insira um termo de busca."
        
        # Tentar busca por FIPE primeiro
        if query.isdigit():
            result = self.search_engine.search_by_fipe(query)
            if result:
                return [result], f"✅ Veículo encontrado por código FIPE: {query}"
        
        # Busca por marca/modelo
        results = self.search_engine.search_by_brand_model(query)
        
        if results:
            return results, f"✅ Encontrados {len(results)} veículos relacionados a: '{query}'"
        else:
            return [], f"❌ Nenhum veículo encontrado para: '{query}'"
    
    def get_adas_info(self, vehicle: Dict) -> Dict:
        """Extrai informações de ADAS do veículo"""
        return {
            "has_adas": vehicle.get('ADAS') == 'Sim',
            "windshield_adas": vehicle.get('ADAS no Parabrisa') == 'Sim',
            "bumper_adas": vehicle.get('Adas no Parachoque') == 'Sim',
            "calibration_type": vehicle.get('Tipo de Regulagem', 'Não informado'),
            "rearview_camera": vehicle.get('Camera no Retrovisor') == 'Sim',
            "matrix_lights": vehicle.get('Faróis Matrix') == 'Sim'
        }
    
    def generate_calibration_guide(self, vehicle: Dict) -> Dict:
        """Gera guia de calibração para o veículo"""
        adas_info = self.get_adas_info(vehicle)
        
        if not adas_info["has_adas"]:
            return {
                "status": "no_adas",
                "message": "❌ Este veículo não possui sistemas ADAS para calibração."
            }
        
        # Obter instruções da Bosch
        instructions = self.bosch_integration.get_calibration_instructions(
            vehicle['BrandName'], 
            vehicle['VehicleName']
        )
        
        return {
            "status": "success",
            "vehicle_info": {
                "brand": vehicle['BrandName'],
                "model": vehicle['VehicleName'],
                "year": vehicle['VehicleModelYear'],
                "fipe_id": vehicle['FipeID']
            },
            "adas_features": adas_info,
            "calibration": instructions
        }

# Função principal do Streamlit
def main():
    st.title("🔧 Sistema Inteligente de Calibração ADAS")
    st.markdown("---")
    
    # Inicializar sistema (usar cache do Streamlit)
    @st.cache_resource
    def init_system():
        system = ADASCalibrationSystem()
        # Aqui você deve colocar o caminho do seu arquivo CSV
        # system.initialize("processed_data.csv")
        return system
    
    # Para demo, vamos simular sem carregar arquivo
    # system = init_system()
    
    # Interface de busca
    st.subheader("🔍 Buscar Veículo")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Digite o código FIPE, marca, modelo ou abreviação:",
            placeholder="Ex: Polo TSI 2025, BMW 118i, 92983",
            help="Você pode buscar por código FIPE, nome da marca, modelo ou abreviação do veículo"
        )
    
    with col2:
        search_button = st.button("🔍 Buscar", type="primary")
    
    # Processamento da busca
    if search_button and search_query:
        with st.spinner("🔄 Buscando veículo..."):
            # Simulação de resultado (remover quando integrar com dados reais)
            st.success("✅ Veículo encontrado!")
            
            # Layout de resultados
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📋 Informações do Veículo")
                st.write("**Marca:** BMW")
                st.write("**Modelo:** 118i M Sport 1.5 TB 12V Aut. 5p")
                st.write("**Ano:** 2024")
                st.write("**Código FIPE:** 92983")
                
                st.subheader("🎯 Status ADAS")
                st.success("✅ Possui ADAS")
                st.write("**ADAS no Parabrisa:** ✅ Sim")
                st.write("**ADAS no Parachoque:** ✅ Sim")
                st.write("**Tipo de Regulagem:** Dinâmica")
                st.write("**Câmera no Retrovisor:** ❌ Não")
                st.write("**Faróis Matrix:** ❌ Não")
            
            with col2:
                st.subheader("⚙️ Instruções de Calibração")
                
                with st.expander("🔧 Calibração Dinâmica", expanded=True):
                    st.write("**Procedimento:**")
                    st.write("1. Verificar alinhamento das rodas")
                    st.write("2. Conectar equipamento de diagnóstico")
                    st.write("3. Realizar test drive em pista específica")
                    st.write("4. Seguir protocolo de calibração dinâmica")
                    st.write("5. Validar funcionamento dos sistemas ADAS")
                    
                    st.write("**Requisitos:**")
                    st.write("• Pista de calibração específica")
                    st.write("• Condições climáticas adequadas")
                    st.write("• Equipamento DAS 3000 ou similar")
                
                st.info("💡 **Dica:** Para calibração dinâmica, certifique-se de que o veículo esteja com pneus calibrados e alinhamento em dia.")
    
    # Seção de estatísticas (sidebar ou rodapé)
    with st.sidebar:
        st.subheader("📊 Estatísticas da Base")
        st.metric("Total de Veículos", "65.735")
        st.metric("Marcas Disponíveis", "33")
        st.metric("Veículos com ADAS", "65.735 (100%)")
        
        st.subheader("🔧 Tipos de Calibração")
        st.write("• **Dinâmica:** 37.623 veículos")
        st.write("• **Estática:** 24.009 veículos")
        st.write("• **Estática/Dinâmica:** 3.883 veículos")

if __name__ == "__main__":
    main()
