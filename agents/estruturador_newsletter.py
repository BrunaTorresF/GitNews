import logging
from datetime import datetime
from typing import Dict, Any, Optional

from models.state import NewsletterState

# Configuração do logger específico para o estruturador
logger = logging.getLogger("newsletter_generator.estruturador")

#=============================================================================
# FUNÇÕES AUXILIARES
#=============================================================================

def formatar_data_iso(data_iso: str) -> str:
    """
    Converte uma data em formato ISO para o formato brasileiro (dd/mm/aaaa).
    
    Args:
        data_iso: String contendo a data em formato ISO 8601
        
    Returns:
        String formatada no padrão brasileiro
    """
    # Substitui 'Z' por '+00:00' para compatibilidade com fromisoformat
    return datetime.fromisoformat(data_iso.replace('Z', '+00:00')).strftime('%d/%m/%Y')

#=============================================================================
# FUNÇÃO PRINCIPAL DE ESTRUTURAÇÃO DA NEWSLETTER
#=============================================================================

def estruturar_newsletter(state: NewsletterState) -> NewsletterState:
    """
    Gera a estrutura básica da newsletter com os dados do repositório.
    
    Args:
        state: Dicionário contendo o estado atual da geração da newsletter,
               deve incluir 'repo_data' com os dados do repositório e 'repo_url'
               
    Returns:
        Dicionário atualizado com o conteúdo da newsletter no campo 'content'
        ou mensagem de erro no campo 'error'
        
    Raises:
        Exception: Qualquer erro durante o processamento é capturado e registrado
    """
    try:
        #=============================================================================
        # VALIDAÇÃO DE DADOS DE ENTRADA
        #=============================================================================
        
        # Verifica se os dados do repositório estão presentes no estado
        if not state.get('repo_data'):
            error_msg = "Dados do repositório não encontrados"
            logger.error(error_msg)
            # Retorna o estado original com a adição do campo de erro
            return {
                **state,  # Preserva todos os campos do estado original
                'error': error_msg
            }
            
        #=============================================================================
        # PROCESSAMENTO DOS DADOS
        #=============================================================================
        
        # Extrai os dados do repositório do estado para facilitar o acesso
        repo_data = state['repo_data']
        logger.info(f"Estruturando newsletter para o repositório {repo_data['name']}")
        
        #=============================================================================
        # GERAÇÃO DO CONTEÚDO BÁSICO
        #=============================================================================
        
        # Criar estrutura básica da newsletter usando template Markdown
        # O template é dividido em seções: título, visão geral, estatísticas e acesso rápido
        content = f"""# {repo_data['name']} - Análise e Guia Prático

## Visão Geral
- **Criado por:** {repo_data['owner']['login']}
- **Descrição:** {repo_data.get('description', 'Sem descrição')}
- **Linguagem Principal:** {repo_data.get('language', 'Não especificada')}
- **Última atualização:** {formatar_data_iso(repo_data['updated_at'])}

## Estatísticas e Popularidade
- ⭐ Stars: {repo_data['stargazers_count']}
- 🍴 Forks: {repo_data['forks_count']}
- 🔍 Issues Abertas: {repo_data['open_issues_count']}
- 📅 Criado em: {formatar_data_iso(repo_data['created_at'])}

## Acesso Rápido
📂 Repositório: {state['repo_url']}
{f"📄 Website: {repo_data.get('homepage')}" if repo_data.get('homepage') else ""}

---
Newsletter gerada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        
        #=============================================================================
        # FINALIZAÇÃO E RETORNO
        #=============================================================================
        
        # Registra o tamanho do conteúdo gerado para fins de monitoramento
        logger.info(f"Estrutura básica gerada com {len(content)} caracteres")
        # Retorna o estado atualizado com o conteúdo da newsletter
        return {
            **state,  # Preserva todos os campos do estado original
            'content': content  # Adiciona o conteúdo gerado
        }
        
    except Exception as e:
        # Captura qualquer exceção não tratada para evitar falhas na pipeline
        error_msg = f"Erro ao gerar estrutura básica: {str(e)}"
        logger.error(error_msg)
        # Retorna o estado original com a adição do campo de erro
        return {
            **state,
            'error': error_msg
        } 