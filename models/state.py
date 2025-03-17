import logging
from typing import Dict, List, Optional
from typing_extensions import TypedDict

# Configuração do logger específico para o módulo de estado
logger = logging.getLogger("newsletter_generator.state")

#=============================================================================
# DEFINIÇÃO DO TIPO DE ESTADO DA NEWSLETTER
#=============================================================================

class NewsletterState(TypedDict):
    """
    Define a estrutura de estado para processamento da newsletter.
    
    Campos:
        repo_url: URL do repositório GitHub
        repo_data: Dados extraídos do repositório
        content: Conteúdo básico estruturado da newsletter
        enhanced_content: Conteúdo aprimorado com análise do LLM
        formatted_content: Conteúdo final formatado da newsletter
        output_file: Caminho do arquivo de saída
        error: Mensagem de erro, se houver
    """
    repo_url: str
    repo_data: Optional[Dict]
    content: Optional[str]
    enhanced_content: Optional[str]
    formatted_content: Optional[str]
    output_file: Optional[str]
    error: Optional[str]