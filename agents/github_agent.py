import requests
import os
from models.state import NewsletterState
from config.settings import GITHUB_TOKEN
import logging

# Configuração do logger específico para o agente GitHub
logger = logging.getLogger("github_agent")

#=============================================================================
# FUNÇÃO PRINCIPAL DO AGENTE GITHUB
#=============================================================================

def github_agent(state: NewsletterState) -> NewsletterState:
    """
    Busca dados detalhados de um repositório GitHub.
    
    Args:
        state: Estado atual contendo a URL do repositório no formato 'repo_url'
        
    Returns:
        Estado atualizado com os dados do repositório em 'repo_data' ou
        mensagem de erro em 'error' caso ocorra algum problema
        
    Dados coletados:
        - Informações básicas do repositório
        - Conteúdo do README
        - Estrutura de arquivos
        - Linguagens utilizadas
        - Commits recentes
    """
    try:
        #=============================================================================
        # EXTRAÇÃO DE INFORMAÇÕES DA URL
        #=============================================================================
        
        # Extrair owner/repo da URL (formato esperado: https://github.com/owner/repo)
        # Primeiro remove barras finais e depois divide por '/'
        parts = state['repo_url'].strip('/').split('/')
        # Os dois últimos elementos são sempre owner e repo, independente do formato da URL
        owner, repo = parts[-2], parts[-1]
        
        logger.info(f"Buscando dados para repositório {owner}/{repo}")
        
        #=============================================================================
        # VERIFICAÇÃO DO TOKEN DE AUTENTICAÇÃO
        #=============================================================================
        
        # Verificar se o token está disponível na configuração
        github_token = GITHUB_TOKEN
        if not github_token:
            # Estratégia de fallback: tentar obter o token diretamente das variáveis de ambiente
            # Isso é útil quando a configuração não foi carregada corretamente
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                error_msg = "Token do GitHub não encontrado"
                logger.error(error_msg)
                return {
                    **state,  # Preserva o estado original
                    'error': error_msg
                }
        
        #=============================================================================
        # CONFIGURAÇÃO E REQUISIÇÃO PRINCIPAL
        #=============================================================================
        
        # Configuração dos headers para autenticação na API do GitHub
        # O token é necessário para aumentar o rate limit e acessar repositórios privados
        # O User-Agent é obrigatório para requisições à API do GitHub
        headers = {
            "Authorization": f"token {github_token}",
            "User-Agent": "GitGRAPH-Newsletter-Generator"
        }
        
        # URL da API
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        logger.info(f"Fazendo requisição para: {api_url}")
        
        # Requisição HTTP para obter dados básicos do repositório
        response = requests.get(api_url, headers=headers)
        
        # Adicionar log para depuração
        logger.info(f"Status code da resposta: {response.status_code}")
        if response.status_code != 200:
            # Tenta extrair detalhes do erro da resposta JSON
            try:
                error_details = response.json()
                logger.error(f"Detalhes do erro: {error_details}")
            except:
                logger.error("Não foi possível obter detalhes do erro")
        
        # Verificação de sucesso da requisição
        if response.status_code != 200:
            error_msg = f"Erro ao acessar API do GitHub: {response.status_code}"
            logger.error(error_msg)
            return {
                **state,
                'error': error_msg
            }
        
        # Adicionar mais dados do repositório para o LLM
        repo_json = response.json()
        
        #=============================================================================
        # OBTENÇÃO DO README
        #=============================================================================
        
        # Requisição para obter metadados do README (não o conteúdo em si)
        # A API do GitHub retorna informações sobre o arquivo, incluindo a URL para download
        readme_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/readme",
            headers=headers
        )
        
        if readme_response.status_code == 200:
            readme_data = readme_response.json()
            # Segunda requisição para obter o conteúdo raw do README
            # Não precisamos do token para acessar o conteúdo raw, apenas o User-Agent
            content_response = requests.get(
                readme_data['download_url'],
                headers={"User-Agent": "GitGRAPH-Newsletter-Generator"}
            )
            if content_response.status_code == 200:
                # Adiciona o conteúdo do README aos dados do repositório
                repo_json['readme_content'] = content_response.text
                logger.info(f"README obtido com {len(repo_json['readme_content'])} caracteres")
        else:
            # O repositório pode não ter um README ou pode estar em um formato não padrão
            logger.warning(f"README não encontrado: {readme_response.status_code}")
            
        #=============================================================================
        # OBTENÇÃO DA ESTRUTURA DE ARQUIVOS
        #=============================================================================
        
        # Tenta obter a estrutura completa de arquivos do repositório
        try:
            logger.info(f"Obtendo estrutura de arquivos para {owner}/{repo}")
            # Primeiro tenta na branch 'main' (padrão mais recente do GitHub)
            tree_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1",
                headers=headers
            )
            
            # Estratégia de fallback: se não encontrar na branch 'main', tenta na 'master'
            # Isso é necessário porque repositórios mais antigos usam 'master' como padrão
            if tree_response.status_code != 200:
                logger.info("Branch 'main' não encontrada, tentando 'master'")
                tree_response = requests.get(
                    f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1",
                    headers=headers
                )
                
            if tree_response.status_code == 200:
                tree_data = tree_response.json()
                # Filtrar apenas os caminhos dos arquivos para simplificar
                repo_json['tree'] = [item['path'] for item in tree_data.get('tree', []) if item['type'] == 'blob']
                logger.info(f"Estrutura de arquivos obtida com {len(repo_json['tree'])} arquivos")
            else:
                # Pode falhar se o repositório estiver vazio ou se as branches forem diferentes
                logger.warning(f"Estrutura de arquivos não encontrada: {tree_response.status_code}")
        except Exception as e:
            # Captura erros específicos da obtenção da estrutura, mas continua o processamento
            # Isso permite que outras informações ainda sejam coletadas mesmo com falha parcial
            logger.warning(f"Erro ao obter estrutura de arquivos: {str(e)}")
            
        #=============================================================================
        # OBTENÇÃO DAS LINGUAGENS UTILIZADAS
        #=============================================================================
        
        # Obtenção das linguagens de programação usadas no repositório
        try:
            logger.info(f"Obtendo linguagens para {owner}/{repo}")
            languages_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/languages",
                headers=headers
            )
            
            if languages_response.status_code == 200:
                # A API retorna um dicionário com linguagens e bytes de código
                repo_json['languages'] = languages_response.json()
                logger.info(f"Linguagens obtidas: {', '.join(repo_json['languages'].keys())}")
            else:
                logger.warning(f"Linguagens não encontradas: {languages_response.status_code}")
        except Exception as e:
            # Captura erros específicos da obtenção de linguagens, mas continua o processamento
            logger.warning(f"Erro ao obter linguagens: {str(e)}")
            
        #=============================================================================
        # OBTENÇÃO DOS COMMITS RECENTES
        #=============================================================================
        
        # Obtenção dos 10 commits mais recentes do repositório
        try:
            logger.info(f"Obtendo commits recentes para {owner}/{repo}")
            commits_response = requests.get(
                # Limita a 10 commits para evitar excesso de dados e respeitar rate limits
                f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=10",
                headers=headers
            )
            
            if commits_response.status_code == 200:
                commits_data = commits_response.json()
                # Simplifica os dados dos commits, extraindo apenas as informações relevantes
                # A resposta original da API contém muitos dados que não são necessários
                repo_json['recent_commits'] = [
                    {
                        'message': commit['commit']['message'],  # Mensagem do commit
                        'author': commit['commit']['author']['name'],  # Nome do autor
                        'date': commit['commit']['author']['date']  # Data do commit
                    }
                    for commit in commits_data
                ]
                logger.info(f"Commits recentes obtidos: {len(repo_json['recent_commits'])}")
            else:
                logger.warning(f"Commits recentes não encontrados: {commits_response.status_code}")
        except Exception as e:
            # Captura erros específicos da obtenção de commits, mas continua o processamento
            logger.warning(f"Erro ao obter commits recentes: {str(e)}")
        
        #=============================================================================
        # FINALIZAÇÃO E RETORNO
        #=============================================================================
        
        logger.info(f"Dados do repositório obtidos com sucesso")
        # Retorna o estado atualizado com os dados do repositório
        return {
            **state,
            'repo_data': repo_json
        }
        
    except Exception as e:
        # Captura qualquer exceção não tratada para evitar falhas na pipeline
        error_msg = f"Erro ao buscar dados do repositório: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            'error': error_msg
        }