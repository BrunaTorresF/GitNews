import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from config.settings import load_env, GITHUB_TOKEN, OPENROUTER_API_KEY
from utils.logger import setup_logger
from workflow.executor import WorkflowExecutor

#=============================================================================
# FUNÇÕES DE CONFIGURAÇÃO E INICIALIZAÇÃO
#=============================================================================

def estrutura_projeto() -> bool:
    """
    Garante que a estrutura de diretórios do projeto existe.
    
    Cria diretórios necessários para o funcionamento da aplicação,
    como a pasta de logs.
    
    Returns:
        True se a estrutura foi verificada/criada com sucesso
    """
    #=============================================================================
    # CRIAÇÃO DE DIRETÓRIOS
    #=============================================================================
    
    # Caminho da pasta raiz do projeto
    project_root = Path(__file__).parent
    
    # Cria o diretório de logs
    dir_name = "logs"
    dir_path = project_root / dir_name
    dir_path.mkdir(exist_ok=True)
    
    # Cria o diretório de saída
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    
    return True

#=============================================================================
# FUNÇÃO PRINCIPAL
#=============================================================================

def main() -> None:
    """
    Função principal da aplicação.
    
    Configura o ambiente, verifica as dependências e executa
    o fluxo de geração da newsletter.
    """
    #=============================================================================
    # CONFIGURAÇÃO INICIAL
    #=============================================================================
    
    # Garantir que a estrutura de diretórios existe
    estrutura_projeto()
    
    # Configurar logger
    logger = setup_logger()
    logger.info("Iniciando gerador de newsletter")
    
    #=============================================================================
    # VERIFICAÇÃO DE CONFIGURAÇÃO
    #=============================================================================
    
    # Verificar configuração de ambiente
    if not load_env():
        logger.error("Configuração não encontrada. Verifique o arquivo .env")
        print("Erro: Configuração não encontrada. Configure o arquivo .env com GITHUB_TOKEN e OPENROUTER_API_KEY")
        sys.exit(1)
    
    # Verificar se o token do GitHub foi carregado corretamente
    if not GITHUB_TOKEN:
        logger.error("Token do GitHub não foi carregado corretamente")
        print("Erro: Token do GitHub não foi carregado. Verifique o arquivo .env")
        sys.exit(1)

    # Verificar se o token da OpenRouter foi carregado corretamente
    if not OPENROUTER_API_KEY:
        logger.error("Token da OpenRouter não foi carregado corretamente")
        print("Erro: Token da OpenRouter não foi carregado. Verifique o arquivo .env")
        sys.exit(1)    
    
    #=============================================================================
    # EXECUÇÃO DO FLUXO PRINCIPAL
    #=============================================================================
    
    try:
        # Exibir cabeçalho no console
        print("SantaGitNews - Gerador de Newsletter para Repositórios GitHub")
        print("----------------------------------------------------------")
        
        # Obter URL do repositório do usuário
        repo_url = input("Digite a URL do repositório GitHub: ").strip()
        print("\nProcessando... Isso pode levar alguns segundos.")
        
        # Criar e executar workflow
        executor = WorkflowExecutor()
        output_file = executor.execute(repo_url)
        
        # Exibir mensagem de sucesso
        print(f"\nNewsletter gerada com sucesso! Arquivo: {output_file}")
        logger.info(f"Newsletter gerada com sucesso para {repo_url}. Arquivo: {output_file}")
        
    except Exception as e:
        # Capturar e registrar qualquer erro durante a execução
        logger.error(f"Erro na execução: {str(e)}")
        print(f"\nErro: {str(e)}")
        sys.exit(1)

#=============================================================================
# PONTO DE ENTRADA
#=============================================================================

if __name__ == "__main__":
    main()