import streamlit as st
import pandas as pd
import os
from typing import Dict, List

# Configuração da página
st.set_page_config(
    page_title="Sistema ADAS Pro",
    page_icon="🔧",
    layout="wide"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .vehicle-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin: 1rem 0;
    }
    
    .adas-status-positive {
        background: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_vehicle_data(uploaded_file=None):
    """Carrega dados de veículos"""
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
            return df
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {e}")
    
    # Verificar se existe arquivo local
    if os.path.exists('data/processed_data.csv'):
        try:
            df = pd.read_csv('data/processed_data.csv', sep=';', encoding='utf-8')
            return df
        except Exception as e:
            st.warning(f"Erro ao carregar arquivo local: {e}")
    
    # Dados de demonstração
    return pd.DataFrame({
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
        'ADAS': ['Sim'] * 10,
        'ADAS no Parabrisa': ['Sim', 'Sim', 'Sim', 'Sim', 'Não', 'Sim', 'Sim', 'Sim', 'Sim', 'Sim'],
        'Adas no Parachoque': ['Sim'] * 10,
        'Tipo de Regulagem': [
            'Dinamica', 'Estatica', 'Dinamica', 'Estatica/Dinamica', 'Dinamica',
            'Dinamica', 'Estatica', 'Dinamica', 'Estatica', 'Dinamica'
        ],
        'Camera no Retrovisor': ['Não', 'Sim', 'Sim', 'Não', 'Sim', 'Sim', 'Não', 'Sim', 'Sim', 'Sim'],
        'Faróis Matrix': ['Não', 'Não', 'Sim', 'Sim', 'Não', 'Sim', 'Não', 'Não', 'Sim', 'Sim']
    })

def intelligent_search(query: str, df: pd.DataFrame) -> List[Dict]:
    """Sistema de busca inteligente"""
    if not query.strip():
        return []
    
    query_clean = query.strip().upper()
    results = []
    
    # Busca por FIPE ID
    if query_clean.isdigit():
        fipe_matches = df[df['FipeID'].astype(str) == query_clean]
        if not fipe_matches.empty:
            return fipe_matches.to_dict('records')
    
    # Busca textual
    for idx, row in df.iterrows():
        score = 0
        
        # Score por marca
        if query_clean in str(row['BrandName']).upper():
            score += 50
        
        # Score por modelo
        if query_clean in str(row['VehicleName']).upper():
            score += 40
        
        # Score por abreviação
        if query_clean in str(row['Abreviação de descrição']).upper():
            score += 30
        
        if score > 0:
            result = row.to_dict()
            result['search_score'] = score
            results.append(result)
    
    return sorted(results, key=lambda x: x.get('search_score', 0), reverse=True)[:10]

def get_calibration_instructions(brand: str, calibration_type: str) -> Dict:
    """Retorna instruções de calibração"""
    instructions_db = {
        'BMW': {
            'title': '🔧 Calibração BMW ADAS',
            'duration': '60-90 minutos',
            'steps': [
                'Conectar DAS 3000 ou equipamento compatível BMW',
                'Verificar códigos de defeito e limpar se necessário',
                'Verificar pressão dos pneus conforme especificação BMW',
                'Selecionar "BMW" → "Sistemas ADAS" no equipamento',
                'Escolher tipo de calibração (Estática/Dinâmica)',
                'Seguir procedimento guiado no equipamento',
                'Realizar test drive para validação (se dinâmica)',
                'Verificar funcionamento de todos os sistemas ADAS'
            ],
            'requirements': [
                'Equipamento DAS 3000 ou compatível BMW',
                'Superfície plana e nivelada para calibração estática',
                'Pista de teste adequada para calibração dinâmica',
                'Condições climáticas favoráveis (sem chuva intensa)',
                'Pneus calibrados conforme especificação',
                'Alinhamento e geometria da direção em dia'
            ],
            'warnings': [
                '⚠️ Verificar recalls de software antes da calibração',
                '⚠️ Não realizar calibração com códigos de defeito ativos',
                '⚠️ Temperatura ambiente deve estar entre 5°C e 35°C'
            ]
        },
        'VOLKSWAGEN': {
            'title': '🔧 Calibração Volkswagen ADAS',
            'duration': '30-60 minutos',
            'steps': [
                'Conectar VCDS, ODIS ou equipamento compatível',
                'Verificar e limpar códigos de defeito',
                'Posicionar veículo conforme especificações VW',
                'Instalar targets de calibração específicos VW/Audi',
                'Acessar Central de Conforto → Sistemas ADAS',
                'Executar "Calibração da Câmera Frontal"',
                'Aguardar conclusão sem mover o veículo',
                'Verificar funcionamento dos sistemas'
            ],
            'requirements': [
                'VCDS, ODIS ou equipamento compatível',
                'Targets específicos do grupo VW/Audi',
                'Ambiente com iluminação controlada',
                'Bateria com carga mínima de 12,5V',
                'Sistema de direção centralizado'
            ],
            'warnings': [
                '⚠️ Respeitar distâncias exatas para targets',
                '⚠️ Não mover o veículo durante calibração estática',
                '⚠️ Verificar se para-brisa não possui trincas'
            ]
        }
    }
    
    return instructions_db.get(brand, {
        'title': f'🔧 Calibração {brand} ADAS',
        'duration': '45-75 minutos',
        'steps': [
            'Conectar equipamento de diagnóstico adequado',
            'Verificar pré-requisitos do sistema',
            'Seguir procedimento específico do fabricante',
            'Realizar validação conforme manual técnico'
        ],
        'requirements': [
            'Equipamento compatível com a marca',
            'Manual técnico atualizado',
            'Ambiente adequado para calibração'
        ],
        'warnings': [
            '⚠️ Consultar documentação específica',
            '⚠️ Verificar atualizações disponíveis'
        ]
    })

def main():
    """Função principal"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🔧 Sistema Inteligente de Calibração ADAS</h1>
        <p>Plataforma profissional para calibração de sistemas avançados de assistência ao condutor</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "📁 Carregar Base de Dados",
            type=['csv'],
            help="Envie seu arquivo CSV com dados dos veículos"
        )
        
        st.markdown("---")
        st.subheader("📊 Estatísticas")
    
    # Carregar dados
    df = load_vehicle_data(uploaded_file)
    
    # Mostrar estatísticas na sidebar
    with st.sidebar:
        total_vehicles = len(df)
        vehicles_with_adas = len(df[df['ADAS'] == 'Sim'])
        unique_brands = df['BrandName'].nunique()
        
        st.metric("Total de Veículos", f"{total_vehicles:,}")
        st.metric("Veículos com ADAS", f"{vehicles_with_adas:,}")
        st.metric("Marcas Únicas", unique_brands)
        
        if not uploaded_file:
            st.info("ℹ️ Usando dados de demonstração")
    
    # Interface de busca principal
    st.subheader("🔍 Buscar Veículo")
    
    search_col, button_col = st.columns([4, 1])
    
    with search_col:
        search_query = st.text_input(
            "",
            placeholder="Digite código FIPE, marca, modelo ou abreviação (ex: BMW 118i, 92983, Polo TSI)",
            help="Busca inteligente: aceita código FIPE, nome da marca, modelo ou abreviação do veículo"
        )
    
    with button_col:
        search_button = st.button("🔍 Buscar", type="primary", use_container_width=True)
    
    # Processamento da busca
    if search_button and search_query:
        with st.spinner("🔄 Buscando veículo na base de dados..."):
            results = intelligent_search(search_query, df)
        
        if results:
            st.success(f"✅ Encontrados {len(results)} veículo(s) para: '{search_query}'")
            
            for i, vehicle in enumerate(results):
                # Card do veículo
                st.markdown(f"""
                <div class="vehicle-card">
                    <h3>🚗 {vehicle['BrandName']} {vehicle['VehicleName']}</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0;">
                        <div><strong>Ano:</strong> {vehicle['VehicleModelYear']}</div>
                        <div><strong>FIPE ID:</strong> {vehicle['FipeID']}</div>
                        <div><strong>Abreviação:</strong> {vehicle['Abreviação de descrição']}</div>
                        <div><strong>Calibração:</strong> {vehicle['Tipo de Regulagem']}</div>
                    </div>
                    
                    <div class="adas-status-positive">
                        <h4>✅ Status ADAS</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                            <div>• ADAS no Parabrisa: {'✅' if vehicle['ADAS no Parabrisa'] == 'Sim' else '❌'}</div>
                            <div>• ADAS no Parachoque: {'✅' if vehicle['Adas no Parachoque'] == 'Sim' else '❌'}</div>
                            <div>• Câmera Retrovisor: {'✅' if vehicle['Camera no Retrovisor'] == 'Sim' else '❌'}</div>
                            <div>• Faróis Matrix: {'✅' if vehicle['Faróis Matrix'] == 'Sim' else '❌'}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Instruções de calibração
                if vehicle['ADAS'] == 'Sim':
                    instructions = get_calibration_instructions(
                        vehicle['BrandName'], 
                        vehicle['Tipo de Regulagem']
                    )
                    
                    with st.expander(f"⚙️ Instruções de Calibração - {vehicle['BrandName']}", expanded=True):
                        st.markdown(f"### {instructions['title']}")
                        st.write(f"**⏱️ Duração Estimada:** {instructions['duration']}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📝 Procedimento Passo a Passo")
                            for j, step in enumerate(instructions['steps'], 1):
                                st.write(f"{j}. {step}")
                        
                        with col2:
                            st.subheader("📋 Requisitos")
                            for req in instructions['requirements']:
                                st.write(f"• {req}")
                            
                            if 'warnings' in instructions:
                                st.subheader("⚠️ Avisos Importantes")
                                for warning in instructions['warnings']:
                                    st.warning(warning)
                
                st.markdown("---")
        
        else:
            st.error(f"❌ Nenhum veículo encontrado para: '{search_query}'")
            st.info("💡 **Dicas de busca:**")
            st.write("• Use o código FIPE para busca exata")
            st.write("• Digite apenas a marca para ver todos os modelos")
            st.write("• Use abreviações como 'Polo TSI', '118i'")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🔧 <strong>Sistema ADAS Pro</strong> | Desenvolvido para profissionais da área automotiva</p>
        <p>💡 Sugestões? Entre em contato: desenvolvimento@adas.com</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
