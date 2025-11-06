# Agent Core Starter

Um kit inicial abrangente para construir e implantar agentes de IA usando o Amazon Bedrock AgentCore. Este projeto fornece agentes de exemplo, automação de implantação e infraestrutura de apoio para desenvolvimento rápido de agentes.

## 🚀 Funcionalidades

- **Múltiplos Frameworks de Agentes**: Exemplos usando Strands e LangGraph
- **Implantação Automatizada**: Implantação com um clique na AWS com configuração adequada de IAM e autenticação
- **Integração de Busca Vetorial**: Armazenamento vetorial S3 integrado para recuperação de conhecimento
- **Autenticação**: Integração opcional com Cognito para acesso seguro ao agente
- **Observabilidade**: Capacidades integradas de logging e monitoramento
- **Servidor MCP**: Implementação do servidor Model Context Protocol

## 📁 Estrutura do Projeto

```
CRAWLER/
├── agents/                    # Implementações de agentes de exemplo
│   ├── strands/              # Agente do framework Strands
│   │   └── agent.py
│   └── langgraph/            # Agente do framework LangGraph
│       └── agent.py
├── aws/                      # Utilitários de infraestrutura AWS
├── crawler/                  # Crawler de repositórios GitHub
├── models/                   # Definições de modelos e utilitários
├── processors/               # Pipelines de processamento de documentos
├── stores/                   # Implementações de armazenamento vetorial
├── utils/                    # Utilitários compartilhados e logging
├── deploy.py                 # Script principal de implantação
├── mcp_server.py            # Implementação do servidor MCP
├── requirements.txt         # Dependências Python
└── .bedrock_agentcore.yaml  # Configuração do AgentCore
```

## 🛠️ Pré-requisitos

- Python 3.8+
- AWS CLI configurado com permissões apropriadas
- Docker (para implantações containerizadas)
- Acesso ao AWS Bedrock em sua região

## ⚙️ Configuração

Antes da implantação, configure as seguintes variáveis em `deploy.py`:

```python
AGENT_NAME = "nome-do-seu-agente"           # Identificador único para seu agente
REQUIRED_FILES = ["agents/strands/agent.py", "requirements.txt"]  # Arquivos obrigatórios
ENTRYPOINT = "agents/strands/agent.py"      # Ponto de entrada principal do agente
AUTH = False                                # Habilitar/desabilitar autenticação
```

### Permissões IAM

Atualize a lista `IAM_STMTS` em `deploy.py` para corresponder aos requisitos do seu agente:

```python
IAM_STMTS = [
    Stmt.query_s3_vectors("seu-bucket", "seu-index"),
    # Adicione permissões adicionais conforme necessário
]
```

## 🚀 Início Rápido

1. **Clonar e Configurar**
   ```bash
   git clone <url-do-repositório>
   cd CRAWLER
   pip install -r requirements.txt
   ```

2. **Configurar Credenciais AWS**
   ```bash
   aws configure
   # ou definir variáveis de ambiente:
   # export AWS_ACCESS_KEY_ID=sua-chave
   # export AWS_SECRET_ACCESS_KEY=seu-secret
   # export AWS_DEFAULT_REGION=us-west-2
   ```

3. **Implantar Seu Agente**
   ```bash
   python deploy.py
   ```

O script de implantação irá:
- Criar roles e políticas IAM necessárias
- Configurar autenticação Cognito (se habilitada)
- Construir e implantar seu agente no AgentCore
- Armazenar configuração no AWS Parameter Store

## 🤖 Agentes de Exemplo

### Agente Strands

Localizado em `agents/strands/agent.py`, este exemplo demonstra:
- Integração com busca A3 Data Wiki
- Consulta em armazenamento vetorial
- Arquitetura baseada em ferramentas
- Integração com modelo Bedrock

**Principais Funcionalidades:**
- Ferramenta `search_a3_wiki()` para recuperação de conhecimento
- Integração com armazenamento vetorial S3
- Logging estruturado

### Agente LangGraph

Localizado em `agents/langgraph/agent.py`, este exemplo mostra:
- Capacidades de cálculo matemático
- Implementação de grafo de estado
- Padrões de composição de ferramentas
- Manipulação de mensagens

**Principais Funcionalidades:**
- Avaliação de expressões matemáticas
- Execução segura de funções
- Fluxo de conversação baseado em grafo

## 📊 Integração de Armazenamento Vetorial

O projeto inclui integração com S3Vector Store para recuperação de conhecimento:

```python
from stores.s3_vector import S3VectorStore

store = S3VectorStore(bucket_name="seu-bucket", index_name="seu-index")
results = store.search(query, limit=5)
```

## 🔐 Autenticação

Habilite a autenticação definindo `AUTH = True` em `deploy.py`. Isso irá:
- Criar um Cognito User Pool
- Configurar autorização JWT
- Configurar acesso seguro do cliente

## 📝 Logging

O projeto inclui logging estruturado via `utils/logger.py`:

```python
from utils.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Sua mensagem aqui")
```

## 🔧 Desenvolvimento

### Adicionando Novos Agentes

1. Crie um novo diretório em `agents/`
2. Implemente seu agente em `agent.py`
3. Atualize `ENTRYPOINT` em `deploy.py`
4. Adicione dependências necessárias ao `requirements.txt`

### Ferramentas Personalizadas

Estenda as capacidades do agente adicionando ferramentas:

```python
from strands import tool

@tool()
def sua_ferramenta_personalizada(param: str) -> str:
    """Descrição da sua ferramenta"""
    # Implementação aqui
    return result
```

### Variáveis de Ambiente

Variáveis de ambiente comuns:
- `AWS_REGION`: Região AWS para implantação
- `LOG_LEVEL`: Nível de logging (DEBUG, INFO, WARNING, ERROR)

## 🚀 Opções de Implantação

### Implantação Padrão
```bash
python deploy.py
```

### Com Autenticação
Defina `AUTH = True` em `deploy.py` antes da implantação.

### Configuração Personalizada
Modifique a configuração em `deploy.py`:
- Nome do agente e ponto de entrada
- Arquivos obrigatórios
- Permissões IAM
- Configurações de autenticação

## 📚 Recursos Adicionais

- [Documentação do Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/)
- [Framework Strands](https://github.com/strands-ai)
- [Documentação do LangGraph](https://langchain-ai.github.io/langgraph/)
- [Especificação do Protocolo MCP](https://modelcontextprotocol.io/)

## 🤝 Contribuindo

1. Faça um fork do repositório
2. Crie uma branch de feature
3. Faça suas alterações
4. Adicione testes se aplicável
5. Submeta um pull request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - consulte o arquivo LICENSE para detalhes.

## 🆘 Solução de Problemas

### Problemas Comuns

**Implantação Falha com Erros IAM**
- Certifique-se de que suas credenciais AWS têm permissões suficientes
- Verifique se as políticas IAM necessárias estão anexadas ao seu usuário/role

**Agente Não Responde**
- Verifique se o arquivo de ponto de entrada existe e está correto
- Consulte os logs do CloudWatch para detalhes de erro
- Certifique-se de que todas as dependências necessárias estão em `requirements.txt`

**Problemas de Conexão com Armazenamento Vetorial**
- Verifique se o bucket S3 existe e está acessível
- Verifique as permissões IAM para acesso S3
- Certifique-se de que o nome do índice está correto

### Obtendo Ajuda

- Consulte os logs do AWS CloudWatch para seu agente
- Revise a configuração do AgentCore em `.bedrock_agentcore.yaml`
- Verifique as entradas do Parameter Store para configurações armazenadas

---

Construído com ❤️ usando Amazon Bedrock AgentCore