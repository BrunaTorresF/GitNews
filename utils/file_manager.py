import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configuração do logger específico para o gerenciador de arquivos
logger = logging.getLogger("newsletter_generator.file_manager")

#=============================================================================
# FUNÇÕES DE GERENCIAMENTO DE DIRETÓRIOS
#=============================================================================

def get_output_directory() -> Path:
    """
    Retorna o diretório de saída para os arquivos gerados.
    
    Prioriza a variável de ambiente OUTPUT_DIR se estiver definida,
    caso contrário usa o diretório 'output' no raiz do projeto.
    
    Returns:
        Path: Caminho do diretório de saída
    """
    # Verificar se existe uma variável de ambiente definindo o diretório de saída
    env_output_dir = os.getenv('OUTPUT_DIR')
    
    if env_output_dir:
        # Usar o diretório definido na variável de ambiente
        output_dir = Path(env_output_dir)
        logger.debug(f"Usando diretório de saída definido na variável de ambiente: {output_dir}")
    else:
        # Usar o diretório padrão dentro do projeto
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "output"
        logger.debug(f"Usando diretório de saída padrão: {output_dir}")
    
    # Garantir que o diretório existe
    output_dir.mkdir(exist_ok=True)
    
    return output_dir

#=============================================================================
# FUNÇÕES DE SALVAMENTO DE ARQUIVOS
#=============================================================================

def save_newsletter(content: str, repo_name: str) -> str:
    """
    Salva o conteúdo da newsletter em um arquivo markdown.
    
    Args:
        content: Conteúdo da newsletter
        repo_name: Nome do repositório
        
    Returns:
        Caminho do arquivo salvo
        
    Raises:
        Exception: Se ocorrer algum erro durante o salvamento
    """
    try:
        #=============================================================================
        # OBTENÇÃO DO DIRETÓRIO DE SAÍDA
        #=============================================================================
        
        # Obter diretório de saída
        output_dir = get_output_directory()
        
        #=============================================================================
        # GERAÇÃO DO NOME DO ARQUIVO
        #=============================================================================
        
        # Converter o nome do repositório para um formato seguro para nome de arquivo
        # Substitui caracteres não alfanuméricos por underscore
        safe_repo_name = ''.join(c if c.isalnum() else '_' for c in repo_name)
        
        # Gerar nome único com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        relative_filename = f"newsletter_{safe_repo_name}_{timestamp}.md"
        filename = output_dir / relative_filename
        
        #=============================================================================
        # SALVAMENTO DO CONTEÚDO
        #=============================================================================
        
        # Salvar conteúdo no arquivo
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Newsletter salva com sucesso em {filename}")
        return str(filename)
        
    except Exception as e:
        # Captura qualquer erro durante o processo de salvamento
        error_msg = f"Erro ao salvar arquivo: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) 