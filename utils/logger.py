import logging
import os
from pathlib import Path
from typing import Optional

#=============================================================================
# CONFIGURAÇÃO DO LOGGER
#=============================================================================

def setup_logger(name: str = "SantaGitNews") -> logging.Logger:
    """
    Configura e retorna um logger para a aplicação.
    
    Cria handlers para saída em arquivo e console com 
    formato padronizado de logs.
    
    Args:
        name: Nome do logger, usado também como prefixo para o arquivo de log
        
    Returns:
        Logger configurado para uso na aplicação
    """
    #=============================================================================
    # DEFINIÇÃO DE FORMATO E DIRETÓRIO
    #=============================================================================
    
    # Formato padrão para todas as mensagens de log
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    
    # Caminho da pasta raiz do projeto
    project_root = Path(__file__).parent.parent
    
    # Garantir que temos um diretório de logs dentro do projeto
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{name}.log"
    
    #=============================================================================
    # CONFIGURAÇÃO DO LOGGER E HANDLERS
    #=============================================================================
    
    # Obter ou criar logger com o nome especificado
    logger = logging.getLogger(name)
    
    # Evitar handlers duplicados se o logger já foi configurado
    if not logger.handlers:
        # Definir nível de log
        logger.setLevel(logging.INFO)
        
        # Handler de arquivo - salva logs em arquivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
        
        # Handler de console - exibe logs no console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(console_handler)
        
        logger.info(f"Logger '{name}' configurado com sucesso. Logs salvos em: {log_file}")
    
    return logger