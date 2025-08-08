# Sistema de Calibração ADAS

Sistema inteligente para consulta de informações sobre calibração de sistemas ADAS (Advanced Driver Assistance Systems) em veículos, integrando dados da tabela FIPE com a documentação técnica da Bosch.

## 🎯 Funcionalidades

### ✅ Implementadas
- **Busca por código FIPE**: Consulta direta usando o código FIPE do veículo
- **Busca por marca/modelo**: Busca flexível por marca, modelo ou texto livre
- **Informações ADAS**: Verifica se o veículo possui sistemas ADAS
- **Instruções de calibração**: Fornece procedimentos específicos por marca
- **Filtros avançados**: Apenas veículos com ADAS ou com informações de calibração
- **Interface responsiva**: Design otimizado para desktop e mobile
- **Estatísticas em tempo real**: Dashboard com métricas da base de dados

### 🔧 Exemplo de Uso
1. **Busca por FIPE**: Digite "5092272" → Encontra Mercedes-Benz Caminhões 1318
2. **Busca por modelo**: Digite "POLO" → Encontra 50 resultados de Volkswagen Polo
3. **Informações detalhadas**: Para cada veículo, mostra:
   - Status ADAS (Sim/Não)
   - Componentes ADAS (parabrisa, parachoque, câmera, faróis matrix)
   - Equipamentos de calibração necessários
   - Links para documentação Bosch

## 📊 Base de Dados

- **274.263 veículos** cadastrados
- **65.735 veículos com ADAS** (23.97%)
- **48 marcas** diferentes
- **5.771 modelos** únicos
- **Anos**: 2000 - 2026
- Integração com documentação Bosch DAS 3000

## 🏗️ Arquitetura

```
adas_calibration_system/
├── app_fixed.py           # Aplicação principal Streamlit
├── data/
│   ├── processed_data.csv # Dados processados do Excel (274k registros)
│   └── bosch_mapping.json # Mapeamento das informações Bosch
├── utils/
│   ├── data_processor.py  # Processamento dos dados Excel
│   ├── bosch_scraper.py   # Extração de dados da Bosch
│   └── search_engine.py   # Motor de busca integrado
├── requirements.txt       # Dependências Python
└── README.md             # Esta documentação
```

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11+
- Streamlit
- Pandas
- OpenPyXL

### Instalação
```bash
# Clonar o repositório
git clone <repository-url>
cd adas_calibration_system

# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run app_fixed.py
```

### Acesso
- **Local**: http://localhost:8501
- **Público**: https://8502-ij50w6ekk0ygo7eqpkkez-04341da7.manusvm.computer

## 🔍 Funcionalidades Detalhadas

### Busca por FIPE
- Campo de entrada para código FIPE
- Validação automática do código
- Resultados instantâneos com informações completas

### Busca por Veículo
- **Marca**: Seleção dropdown com todas as marcas disponíveis
- **Modelo/Texto**: Busca textual inteligente
- **Ano**: Filtro por ano específico
- **Combinações**: Permite combinar múltiplos filtros

### Informações do Veículo
- **Dados básicos**: FIPE, marca, modelo, ano, descrição
- **Status ADAS**: Indicação visual clara (✅/❌)
- **Componentes**: Lista detalhada dos sistemas ADAS
- **Tipo de regulagem**: Informações técnicas específicas

### Informações de Calibração
- **Disponibilidade**: Verifica se há informações na documentação Bosch
- **Tipos de calibração**: Lista completa por categoria
  - Câmera frontal, traseira, 360°
  - Radar frontal, traseiro
  - Sistema Lidar
- **Equipamentos**: Lista de equipamentos necessários (DAS 3000, CTA, etc.)
- **Links diretos**: Acesso à documentação oficial Bosch

## 🎨 Interface

### Sidebar - Estatísticas
- Total de veículos na base
- Quantidade com ADAS
- Percentual de cobertura ADAS
- Número de marcas e modelos
- Faixa de anos disponíveis

### Abas Principais
1. **🔍 Busca por FIPE**: Interface simplificada para busca direta
2. **🚙 Busca por Veículo**: Interface avançada com múltiplos filtros
3. **ℹ️ Sobre**: Informações do sistema e links úteis

### Filtros Dinâmicos
- **Apenas veículos com ADAS**: Filtra apenas veículos que possuem sistemas ADAS
- **Apenas com informações de calibração**: Filtra apenas veículos com procedimentos Bosch

## 🔗 Integração Bosch

### Marcas Suportadas
- **Com documentação completa**: AUDI, BMW/MINI, MERCEDES, FORD, HONDA, etc.
- **Mapeamento automático**: Sistema identifica a marca e busca procedimentos
- **Fallback inteligente**: Para marcas não mapeadas, sugere consulta ao fabricante

### Tipos de Calibração (Exemplo AUDI)
1. **Câmera 360 graus** → Equipamento: CTA 500-1
2. **Câmera frontal** → Equipamentos: DAS 3000, SCT 41x/141x
3. **Câmera traseira** → Equipamento: CTA 501-1
4. **Radar frontal** → Equipamento: DAS 3000
5. **Radar traseiro** → Equipamento: CTA 110-1
6. **Sistema Lidar** → Equipamento: CTA 150-1

## 📈 Performance

- **Tempo de carregamento**: < 3 segundos
- **Busca instantânea**: Resultados em < 1 segundo
- **Cache inteligente**: Dados carregados uma vez por sessão
- **Limite de resultados**: 50 por busca (otimização de performance)
- **Responsividade**: Interface adaptável a diferentes tamanhos de tela

## 🔧 Tecnologias Utilizadas

- **Frontend**: Streamlit (Python)
- **Processamento**: Pandas para manipulação de dados
- **Armazenamento**: CSV (dados) + JSON (mapeamentos)
- **Integração**: Web scraping da documentação Bosch
- **Deploy**: Streamlit Cloud (GitHub integration)

## 📋 Próximos Passos

### Para Deploy em Produção
1. **GitHub Repository**: Criar repositório público
2. **Streamlit Cloud**: Conectar com GitHub para deploy automático
3. **Domínio personalizado**: Configurar URL amigável
4. **Monitoramento**: Implementar analytics de uso

### Melhorias Futuras
- **Cache persistente**: Redis ou similar para performance
- **API REST**: Endpoints para integração com outros sistemas
- **Histórico de buscas**: Salvar consultas frequentes
- **Exportação**: PDF/Excel com informações de calibração
- **Notificações**: Alertas sobre atualizações na documentação Bosch

## 🔗 Links Úteis

- **Documentação Bosch ADAS**: https://help.boschdiagnostics.com/DAS3000/#/home/Onepager/pt/default
- **Tabela FIPE**: https://veiculos.fipe.org.br/
- **Streamlit Docs**: https://docs.streamlit.io/

## 📞 Suporte

Para dúvidas ou sugestões sobre o sistema, consulte a documentação ou entre em contato com a equipe de desenvolvimento.

---

**Sistema desenvolvido para otimizar o processo de calibração ADAS, integrando informações técnicas da Bosch com dados da tabela FIPE brasileira.**

