import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from config.settings import OPENROUTER_CONFIG
from models.state import NewsletterState

# Configuração do logger específico para o gerador de conteúdo
logger = logging.getLogger("newsletter_generator.content_generator")

#=============================================================================
# CONSTANTES E CONFIGURAÇÕES
#=============================================================================

# Constantes para prompts
SYSTEM_PROMPT = """Você é um especialista em comunicação técnica com foco em tecnologia e desenvolvimento de software.
Sua tarefa é realizar uma análise FACTUAL do repositório GitHub, baseando-se APENAS nos dados fornecidos.
NÃO invente funcionalidades, características ou estatísticas que não estejam explicitamente mencionadas nos dados fornecidos.
Se os dados fornecidos forem limitados, reconheça essa limitação em vez de criar informações fictícias.

Forneça insights sobre a arquitetura e implementação, mas também explique a relevância prática e o valor do projeto.
Use um tom profissional, porém acessível e didático, evitando jargões desnecessários.
Limite-se a 4-5 parágrafos, priorizando clareza e aplicabilidade.

IMPORTANTE: 
1. Foque em informações que complementem os dados básicos do repositório (nome, descrição, linguagem, stars, forks, etc.).
2. Sua análise deve trazer insights mais profundos sobre o projeto, como arquitetura, casos de uso, relevância no mercado.
3. CITE NOMES ESPECÍFICOS de arquivos, funções, classes ou componentes que existem no repositório.
4. Mencione TECNOLOGIAS ESPECÍFICAS usadas no projeto, não apenas a linguagem principal.
5. Se não tiver informações suficientes, ADMITA EXPLICITAMENTE a limitação em vez de inventar."""

USER_PROMPT_TEMPLATE = """Realize uma análise FACTUAL do seguinte repositório GitHub, considerando tanto aspectos técnicos quanto práticos.
Baseie-se APENAS nos dados fornecidos. NÃO invente funcionalidades ou características.

Aborde os seguintes pontos (apenas se houver informações suficientes nos dados fornecidos):
- Propósito e problema que o projeto resolve (contexto prático)
- Arquitetura e estrutura do projeto (explicada de forma acessível)
- Principais funcionalidades e como elas beneficiam os usuários
- Casos de uso reais e exemplos práticos de aplicação
- Facilidade de uso e curva de aprendizado
- Relevância no cenário tecnológico atual

Adapte sua linguagem para ser compreensível por pessoas com diferentes níveis de conhecimento técnico.
Equilibre informações técnicas com explicações sobre o valor prático do projeto.

IMPORTANTE: 
1. Não repita as informações básicas que já estão disponíveis nos dados do repositório (nome, descrição, linguagem, stars, forks, etc.).
2. Foque em fornecer insights mais profundos e análises que complementem essas informações básicas.
3. Se os dados fornecidos forem limitados, reconheça essa limitação em vez de criar informações fictícias.
4. Seja FACTUAL e baseie-se APENAS nos dados fornecidos.
5. CITE NOMES ESPECÍFICOS de arquivos, funções, classes ou componentes que existem no repositório.
6. Mencione TECNOLOGIAS ESPECÍFICAS usadas no projeto, não apenas a linguagem principal.
7. Use frases como "Com base nos dados disponíveis..." ou "O README do projeto indica que..." para mostrar a fonte das informações.
8. Se não tiver certeza sobre alguma informação, use linguagem que indique incerteza: "Parece que...", "Os dados sugerem que..."

Dados do repositório:
{repo_data}"""

# Constantes para limites de tamanho
README_MAX_LENGTH = 2000
COMMITS_MAX_COUNT = 5

#=============================================================================
# FUNÇÕES AUXILIARES
#=============================================================================

def limitar_texto(texto: str, limite: int = README_MAX_LENGTH) -> str:
    """
    Limita o tamanho de um texto, adicionando '...' se exceder o limite.
    
    Args:
        texto: Texto a ser limitado
        limite: Número máximo de caracteres permitidos
        
    Returns:
        Texto limitado ao tamanho especificado
    """
    if len(texto) > limite:
        return texto[:limite] + "..."
    return texto

def limitar_lista(lista: List[Any], limite: int = COMMITS_MAX_COUNT) -> List[Any]:
    """
    Limita o tamanho de uma lista ao número especificado de itens.
    
    Args:
        lista: Lista a ser limitada
        limite: Número máximo de itens permitidos
        
    Returns:
        Lista limitada ao tamanho especificado
    """
    if len(lista) > limite:
        return lista[:limite]
    return lista

#=============================================================================
# FUNÇÃO PRINCIPAL DE GERAÇÃO DE CONTEÚDO
#=============================================================================

def content_generator(state: NewsletterState) -> NewsletterState:
    """
    Gera análise técnica aprofundada do repositório usando LLM via Open Router.
    
    Args:
        state: Estado atual contendo dados do repositório ('repo_data') e 
               conteúdo básico ('content')
               
    Returns:
        Estado atualizado com o conteúdo aprimorado no campo 'enhanced_content'
        ou mensagem de erro no campo 'error'
        
    Raises:
        KeyError: Se campos obrigatórios estiverem ausentes
        ValueError: Se os dados do repositório forem inválidos
        Exception: Para outros erros durante o processamento
    """
    try:
        #=============================================================================
        # VALIDAÇÃO DE DADOS DE ENTRADA
        #=============================================================================
        
        # Verificar se os dados necessários estão presentes no estado
        if not state.get('content'):
            error_msg = "Conteúdo básico não encontrado no estado"
            logger.error(error_msg)
            return {
                **state,  # Preserva o estado original
                'error': error_msg
            }
            
        if not state.get('repo_data'):
            error_msg = "Dados do repositório não encontrados no estado"
            logger.error(error_msg)
            return {
                **state,  
                'error': error_msg
            }
        
        # Extrair dados do repositório para processamento
        repo_data = state['repo_data']
        
        # Verificar campos obrigatórios nos dados do repositório
        campos_obrigatorios = ['name', 'stargazers_count', 'forks_count', 'open_issues_count', 'created_at', 'updated_at']
        for campo in campos_obrigatorios:
            if campo not in repo_data:
                error_msg = f"Campo obrigatório '{campo}' não encontrado nos dados do repositório"
                logger.error(error_msg)
                return {
                    **state,  
                    'error': error_msg
                }
        
        logger.info(f"Gerando análise técnica para {repo_data['name']}")
        
        #=============================================================================
        # PREPARAÇÃO DOS DADOS DO REPOSITÓRIO
        #=============================================================================
        
        # Criar um resumo dos dados para o LLM com os campos básicos
        repo_summary = {
            "name": repo_data['name'],
            "description": repo_data.get('description', 'Sem descrição'),
            "language": repo_data.get('language', 'Não especificada'),
            "stars": repo_data['stargazers_count'],
            "forks": repo_data['forks_count'],
            "open_issues": repo_data['open_issues_count'],
            "created_at": repo_data['created_at'],
            "updated_at": repo_data['updated_at']
        }
        
        # Adicionar dados de README se disponíveis, limitando o tamanho
        if 'readme_content' in repo_data:
            repo_summary["readme_preview"] = limitar_texto(repo_data['readme_content'])
            logger.debug(f"README adicionado ao resumo ({len(repo_summary['readme_preview'])} caracteres)")
        
        # Adicionar informações sobre a estrutura do repositório se disponíveis
        if 'tree' in repo_data:
            repo_summary["file_structure"] = repo_data['tree']
            logger.debug(f"Estrutura de arquivos adicionada ao resumo ({len(repo_summary['file_structure'])} arquivos)")
        
        # Adicionar informações sobre as linguagens usadas se disponíveis
        if 'languages' in repo_data:
            repo_summary["languages"] = repo_data['languages']
            logger.debug(f"Linguagens adicionadas ao resumo ({len(repo_summary['languages'])} linguagens)")
        
        # Adicionar informações sobre os commits recentes se disponíveis, limitando a quantidade
        if 'recent_commits' in repo_data:
            repo_summary["recent_commits"] = limitar_lista(repo_data['recent_commits'])
            logger.debug(f"Commits recentes adicionados ao resumo ({len(repo_summary['recent_commits'])} commits)")
        
        #=============================================================================
        # CONSTRUÇÃO DO PROMPT E CHAMADA À API
        #=============================================================================
        
        # Formatar os dados do repositório para incluir no prompt
        try:
            formatted_repo_data = json.dumps(repo_summary, indent=2, ensure_ascii=False)
        except TypeError as e:
            error_msg = f"Erro ao serializar dados do repositório: {str(e)}"
            logger.error(error_msg)
            return {
                **state,  
                'error': error_msg
            }
        
        # Construir o prompt do usuário usando o template
        user_prompt = USER_PROMPT_TEMPLATE.format(repo_data=formatted_repo_data)
        
        # Preparar mensagens para o chat
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info("Enviando requisição para Open Router")
        
        # Fazer requisição para a API usando a configuração centralizada
        # OPENROUTER_CONFIG contém as configurações para acesso à API do LLM, 
        # incluindo chaves de API, endpoints, e configurações de timeout
        try:
            success, result = OPENROUTER_CONFIG.make_request(messages)
        except Exception as e:
            error_msg = f"Erro na comunicação com a API: {str(e)}"
            logger.error(error_msg)
            return {
                **state,  
                'error': error_msg
            }
        
        # Verificar se a requisição foi bem-sucedida
        if not success:
            error_msg = f"Erro na resposta da API: {result}"
            logger.error(error_msg)
            return {
                **state,  
                'error': error_msg
            }
        
        #=============================================================================
        # PROCESSAMENTO DA RESPOSTA
        #=============================================================================
        
        # Extrair o texto da análise da resposta da API
        try:
            analysis_text = result['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            error_msg = f"Erro ao extrair conteúdo da resposta da API: {str(e)}"
            logger.error(error_msg)
            return {
                **state,  
                'error': error_msg
            }
            
        logger.info(f"Resposta recebida do LLM ({len(analysis_text)} caracteres)")
        
        #=============================================================================
        # FINALIZAÇÃO E RETORNO
        #=============================================================================
        
        # Retornar o estado atualizado com o conteúdo aprimorado
        return {
            **state,  
            'enhanced_content': analysis_text  # Adiciona o conteúdo gerado
        }
        
    except KeyError as e:
        # Erro específico para chaves ausentes
        error_msg = f"Erro de acesso a dados: chave '{str(e)}' não encontrada"
        logger.error(error_msg)
        return {
            **state,  
            'error': error_msg
        }
    except ValueError as e:
        # Erro específico para valores inválidos
        error_msg = f"Erro de validação de dados: {str(e)}"
        logger.error(error_msg)
        return {
            **state,  
            'error': error_msg
        }
    except Exception as e:
        # Captura qualquer outra exceção não tratada
        error_msg = f"Erro ao gerar análise técnica: {str(e)}"
        logger.error(error_msg)
        return {
            **state,  
            'error': error_msg
        }