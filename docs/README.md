# SantaGitNews - Gerador de Newsletter para Repositórios GitHub

## Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Fluxo de Trabalho](#fluxo-de-trabalho)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Configuração do Modelo LLM](#configuração-do-modelo-llm)
- [Desenvolvimento](#desenvolvimento)
- [Contribuição](#contribuição)
- [Licença](#licença)

## Visão Geral

O SantaGitNews é uma aplicação Python desenvolvida para gerar newsletters automatizadas a partir de repositórios GitHub. Utilizando a arquitetura LangGraph para orquestrar um fluxo de trabalho entre diferentes agentes especializados, o sistema extrai informações relevantes de repositórios, analisa seu conteúdo e produz newsletters informativas e bem estruturadas.

A aplicação foi projetada para ajudar equipes de desenvolvimento e profissionais de tecnologia a manterem-se atualizados sobre projetos importantes, facilitando a criação de resumos informativos sobre repositórios relevantes.

## Funcionalidades

- **Extração de Dados do GitHub**: Coleta informações detalhadas sobre repositórios, incluindo descrição, estatísticas, README e metadados.
- **Geração de Conteúdo Inteligente**: Utiliza modelos de linguagem para analisar e gerar conteúdo contextualizado.
- **Estruturação Automática**: Organiza o conteúdo em um formato de newsletter profissional.
- **Processamento Modular**: Arquitetura baseada em agentes especializados para diferentes etapas do processo.
- **Geração de Arquivos**: Produz arquivos formatados com o conteúdo da newsletter.

## Arquitetura

O SantaGitNews implementa uma arquitetura baseada em agentes orquestrados por um grafo de fluxo de trabalho, utilizando o framework LangGraph. Esta abordagem permite:

- **Processamento Sequencial**: Cada etapa é executada na ordem correta com base no estado atual.
- **Flexibilidade**: Facilidade para adicionar ou modificar agentes sem alterar a lógica central.
- **Manutenção Simplificada**: Cada agente é responsável por uma tarefa específica, facilitando a manutenção.
- **Fluxo Condicional**: Decisões dinâmicas sobre qual agente acionar com base no estado atual do processo.

A arquitetura de agentes permite que o sistema seja facilmente extensível, tornando simples a adição de novas funcionalidades ou a melhoria das existentes. Cada agente é especializado em uma tarefa específica e contribui para o estado compartilhado que flui pelo grafo.

## Tecnologias

- **Python 3.8+**: Linguagem de programação principal.
- **LangGraph 0.0.15**: Framework para orquestração de agentes.
- **OpenRouter**: Gateway para acesso a modelos de linguagem.
- **GitHub API**: Interface para extração de dados de repositórios.
- **python-dotenv**: Gerenciamento de variáveis de ambiente.
- **requests**: Biblioteca para requisições HTTP.

## Estrutura do Projeto

```
SantaGitNews/
├── agents/                  # Agentes especializados
│   ├── github_agent.py         # Integração com GitHub
│   ├── estruturador_newsletter.py  # Estruturação básica
│   ├── gerador_newsletter.py   # Geração de conteúdo
│   └── redator_newsletter.py   # Formatação final
├── config/                  # Configurações
│   └── settings.py             # Configurações e variáveis de ambiente
├── docs/                    # Documentação
│   └── README.md               # Este arquivo
├── logs/                    # Logs de execução
├── models/                  # Modelos de dados
│   └── state.py                # Estrutura de estado
├── output/                  # Saídas geradas
├── utils/                   # Utilitários
│   ├── logger.py               # Configuração de logging
│   ├── monitor.py              # Monitoramento de execução
│   └── file_manager.py         # Gerenciador de arquivos
├── workflow/                # Fluxo de trabalho
│   ├── executor.py             # Executor do fluxo
│   └── graph.py                # Definição do grafo
├── .env                     # Variáveis de ambiente
├── main.py                  # Ponto de entrada da aplicação
└── requirements.txt         # Dependências
```

## Fluxo de Trabalho

O fluxo de trabalho do sistema segue estas etapas principais:

1. **Coleta de Dados (GitHub Agent)**:
   - Extrai informações do repositório GitHub
   - Obtém README, estatísticas e metadados

2. **Estruturação Básica (Estruturador Newsletter)**:
   - Cria um template inicial com dados básicos
   - Estrutura as seções principais da newsletter

3. **Geração de Conteúdo (Gerador Newsletter)**:
   - Utiliza LLM para analisar o repositório
   - Gera análises detalhadas, casos de uso e pontos fortes

4. **Formatação Final (Redator Newsletter)**:
   - Integra conteúdo estruturado com análises geradas
   - Formata o documento final
   - Salva a newsletter no formato apropriado

Cada etapa modifica o estado compartilhado (`NewsletterState`), que flui através do grafo, permitindo que cada agente contribua com sua especialidade.

## Requisitos

- Python 3.8 ou superior
- Dependências listadas em `requirements.txt`:
  - python-dotenv (>=0.19.0)
  - requests (>=2.26.0) 
  - langgraph (==0.0.15)
  - typing-extensions (>=4.5.0)
  - pyyaml (>=6.0)
  - colorama (>=0.4.4)
  - tqdm (>=4.65.0)
  - pytest (>=7.3.1)
  - black (>=23.3.0)

## Instalação

1. Clone o repositório:
   ```powershell
   git clone https://github.com/seu-usuario/SantaGitNews.git
   cd SantaGitNews
   ```

2. Instale as dependências:
   ```powershell
   pip install -r requirements.txt
   ```

## Configuração

1. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
   ```
   # Token de acesso à API do GitHub
   GITHUB_TOKEN=seu_token_github
   
   # Chave API para o OpenRouter (acesso ao LLM)
   OPENROUTER_API_KEY=sua_chave_api_openrouter
   
   # Diretório de saída (opcional)
   OUTPUT_DIR=caminho/para/diretorio/saida
   ```

2. Obtenha um token do GitHub:
   - Acesse [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
   - Gere um novo token com permissões de leitura para repositórios

3. Obtenha uma chave API do OpenRouter:
   - Registre-se em [OpenRouter](https://openrouter.ai/)
   - Crie uma chave API na seção de configurações

## Uso

Execute o script principal:

```powershell
python main.py
```

O programa solicitará a URL de um repositório GitHub e gerará uma newsletter com base nas informações obtidas. O arquivo de saída será salvo na pasta `output/` (ou no diretório personalizado configurado em `.env`).

### Exemplo de uso passo a passo:

1. Execute o programa:
   ```powershell
   python main.py
   ```

2. Quando solicitado, insira a URL do repositório:
   ```
   Digite a URL do repositório GitHub: https://github.com/username/repository
   ```

3. Aguarde o processamento. O programa irá:
   - Extrair informações do repositório
   - Analisar o conteúdo
   - Gerar e estruturar a newsletter
   - Salvar o arquivo de saída

4. Ao finalizar, será exibido o caminho para o arquivo gerado:
   ```
   Newsletter gerada com sucesso! Arquivo: output/repository_newsletter.md
   ```

## Configuração do Modelo LLM

O projeto utiliza o OpenRouter para acessar modelos de linguagem. As configurações são gerenciadas através do arquivo `config/settings.py`.

### Parâmetros Configuráveis

- **OPENROUTER_MODEL**: Define o modelo a ser utilizado (padrão: "deepseek/deepseek-chat-v3:free")
- **OPENROUTER_TEMPERATURE**: Controla a criatividade/aleatoriedade (0.0-2.0)
  - Valores mais baixos (0.0-0.3): Respostas mais determinísticas
  - Valores médios (0.4-0.7): Equilíbrio entre criatividade e consistência
  - Valores altos (0.8-2.0): Respostas mais criativas
- **OPENROUTER_MAX_TOKENS**: Limita o tamanho da resposta (padrão: 1500)
- **OPENROUTER_TOP_P**: Controla a diversidade (0.0-1.0, padrão: 0.9)
- **OPENROUTER_FREQUENCY_PENALTY**: Penaliza palavras frequentes (-2.0 a 2.0)
- **OPENROUTER_PRESENCE_PENALTY**: Penaliza repetições (-2.0 a 2.0)

Estas configurações podem ser ajustadas no arquivo `.env`.

## Desenvolvimento

### Estrutura de Estado

O sistema utiliza a classe `NewsletterState` para manter o estado entre os diferentes agentes:

```python
class NewsletterState(TypedDict):
    repo_url: str                 # URL do repositório GitHub
    repo_data: Optional[Dict]     # Dados extraídos do repositório
    content: Optional[str]        # Conteúdo básico estruturado
    enhanced_content: Optional[str]  # Conteúdo aprimorado com análise do LLM
    formatted_content: Optional[str] # Conteúdo final formatado
    output_file: Optional[str]    # Caminho do arquivo de saída
    error: Optional[str]          # Mensagem de erro, se houver
```

### Adicionando Novos Agentes

Para adicionar um novo agente ao sistema:

1. Crie um novo arquivo Python na pasta `agents/`
2. Implemente a função principal do agente que recebe e retorna um `NewsletterState`
3. Atualize o arquivo `workflow/graph.py` para incluir o novo agente no fluxo de trabalho

### Personalização

O sistema foi projetado para ser facilmente extensível:

- **Novos Formatos**: Modifique o `redator_newsletter.py` para gerar diferentes formatos de saída
- **Fontes Adicionais**: Estenda o `github_agent.py` para coletar mais dados ou de diferentes fontes
- **Análises Personalizadas**: Ajuste os prompts no `gerador_newsletter.py` para focar em aspectos específicos

### Depuração e Logs

O sistema utiliza um sistema de logs configurado pelo módulo `utils/logger.py` para facilitar a depuração. Os logs são armazenados no diretório `logs/` e contêm informações detalhadas sobre a execução do fluxo.

Para visualizar os logs de execução:
```powershell
Get-Content -Tail 20 logs/santagitnews.log
```

## Contribuição

Contribuições são bem-vindas! Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Diretrizes para contribuição:
- Mantenha o estilo de código consistente
- Adicione testes para novas funcionalidades
- Atualize a documentação conforme necessário
- Siga as práticas de desenvolvimento limpo

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE). 