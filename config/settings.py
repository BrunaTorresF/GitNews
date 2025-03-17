import os
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Tuple, Optional

from dotenv import load_dotenv

#=============================================================================
# CONFIGURAÇÃO DO LOGGER
#=============================================================================

logger = logging.getLogger("settings")

#=============================================================================
# FUNÇÕES DE CONFIGURAÇÃO DE AMBIENTE
#=============================================================================

def load_env() -> bool:
    """
    Carrega variáveis de ambiente do arquivo .env.
    
    Verifica a existência do arquivo .env na raiz do projeto e carrega
    as variáveis de ambiente necessárias para a aplicação.
    
    Returns:
        bool: True se todas as variáveis foram carregadas com sucesso, False caso contrário
    """
    # Verificar se o arquivo .env existe
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    
    if not env_path.exists():
        logger.error(f"Arquivo .env não encontrado em: {env_path}")
        return False
    
    # Carregar variáveis de ambiente
    logger.info(f"Carregando variáveis de ambiente de: {env_path}")
    load_dotenv(dotenv_path=env_path)
    
    required_vars = ['GITHUB_TOKEN', 'OPENROUTER_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Variáveis de ambiente necessárias não encontradas: {', '.join(missing_vars)}")
        return False
    
    # Verificar se o token do GitHub está sendo carregado corretamente
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        # Mostrar apenas os primeiros e últimos caracteres para segurança
        masked_token = f"{github_token[:4]}...{github_token[-4:]}"
        logger.info(f"Token do GitHub carregado: {masked_token}")
    else:
        logger.error("Token do GitHub não encontrado no arquivo .env")
        return False
    
    return True

#=============================================================================
# CARREGAMENTO INICIAL DE VARIÁVEIS DE AMBIENTE
#=============================================================================

# Carregar variáveis de ambiente ao importar o módulo
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

#=============================================================================
# CONSTANTES DE CONFIGURAÇÃO
#=============================================================================

# Configurações do GitHub
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Configurações do OpenRouter
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Configurações de diretórios
OUTPUT_DIR = os.getenv('OUTPUT_DIR')

# Informações da aplicação
APP_NAME = os.getenv('APP_NAME', 'SantaGitNews')
APP_VERSION = os.getenv('APP_VERSION', '1.0')
APP_REFERRER = os.getenv('APP_REFERRER', "https://github.com/seu-usuario/SantaGitNews")

# Constantes padrão para o ModelConfig
DEFAULT_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 60
DEFAULT_MODEL = "deepseek/deepseek-chat-v3:free"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 2500
DEFAULT_TOP_P = 0.9
DEFAULT_STREAM = False

#=============================================================================
# CLASSES DE CONFIGURAÇÃO
#=============================================================================

@dataclass
class ModelConfig:
    """
    Configuração para modelos de LLM via OpenRouter.
    
    Armazena as configurações necessárias para realizar chamadas à API
    da OpenRouter, incluindo chaves de autenticação, parâmetros do modelo
    e informações da aplicação.
    
    Args:
        api_key: Chave de API para autenticação na OpenRouter
        api_url: URL base da API da OpenRouter
        timeout: Tempo limite em segundos para as requisições
        app_name: Nome da aplicação para identificação na API
        app_version: Versão da aplicação
        app_referrer: URL de referência da aplicação
        model: ID do modelo de LLM a ser utilizado
        temperature: Temperatura de geração (0-1)
        max_tokens: Número máximo de tokens na resposta
        top_p: Parâmetro top_p para amostragem de tokens (0-1)
        stream: Se deve usar o modo de streaming de resposta
    """
    # Configuração da API - este é o único parâmetro obrigatório
    api_key: str
    
    # Outros parâmetros com valores padrão definidos pelas constantes
    api_url: str = DEFAULT_API_URL
    timeout: int = DEFAULT_TIMEOUT
    
    # Informações do App
    app_name: str = APP_NAME
    app_version: str = APP_VERSION
    app_referrer: str = APP_REFERRER
    
    # Configuração do modelo
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    top_p: float = DEFAULT_TOP_P
    stream: bool = DEFAULT_STREAM
    
    def get_headers(self) -> Dict[str, str]:
        """
        Retorna os headers para a API do OpenRouter.
        
        Prepara os cabeçalhos HTTP necessários para autenticação 
        e identificação da aplicação na API.
        
        Returns:
            Dict[str, str]: Dicionário com os cabeçalhos HTTP
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.app_referrer,
            "X-Title": self.app_name,
            "User-Agent": f"{self.app_name}/{self.app_version}"
        }
    
    def create_payload(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Cria um payload para a API da OpenRouter.
        
        Args:
            messages: Lista de mensagens no formato
                     [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        
        Returns:
            Dict[str, Any]: Dicionário com o payload completo
        """
        # Cria o payload base a partir dos atributos da classe
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }
        
        # Adiciona stream apenas se for True
        if self.stream:
            payload["stream"] = True
            
        return payload
    
    def make_request(self, messages: List[Dict[str, str]]) -> Tuple[bool, Any]:
        """
        Faz uma requisição para a API da OpenRouter.
        
        Envia uma solicitação HTTP para a API com as mensagens fornecidas
        e processa a resposta.
        
        Args:
            messages: Lista de mensagens no formato OpenAI
        
        Returns:
            Tuple[bool, Any]: Tupla com status de sucesso e resultado ou mensagem de erro
        """
        try:
            import requests
            
            # Preparar payload e headers
            payload = self.create_payload(messages)
            headers = self.get_headers()
            
            # Fazer requisição
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Verificar status code
            if response.status_code != 200:
                return False, f"Erro na API: {response.status_code} - {response.text}"
            
            # Processar resposta
            result = response.json()
            
            # Verificar estrutura da resposta
            if 'choices' not in result or not result['choices'] or 'message' not in result['choices'][0]:
                return False, f"Resposta da API em formato inesperado: {result}"
                
            return True, result
            
        except Exception as e:
            return False, f"Erro ao fazer requisição: {str(e)}"
    
    @classmethod
    def from_env(cls) -> 'ModelConfig':
        """
        Cria uma instância da configuração a partir das variáveis de ambiente.
        
        Lê as variáveis de ambiente relacionadas à configuração do modelo
        e cria uma instância com esses valores.
        
        Returns:
            ModelConfig: Instância configurada com os valores das variáveis de ambiente
        """
        return cls(
            api_key=os.getenv('OPENROUTER_API_KEY', ''),
            api_url=os.getenv('OPENROUTER_API_URL', DEFAULT_API_URL),
            timeout=int(os.getenv('OPENROUTER_TIMEOUT', str(DEFAULT_TIMEOUT))),
            app_name=os.getenv('APP_NAME', APP_NAME),
            app_version=os.getenv('APP_VERSION', APP_VERSION),
            app_referrer=os.getenv('APP_REFERRER', APP_REFERRER),
            model=os.getenv('OPENROUTER_MODEL', DEFAULT_MODEL),
            temperature=float(os.getenv('OPENROUTER_TEMPERATURE', str(DEFAULT_TEMPERATURE))),
            max_tokens=int(os.getenv('OPENROUTER_MAX_TOKENS', str(DEFAULT_MAX_TOKENS))),
            top_p=float(os.getenv('OPENROUTER_TOP_P', str(DEFAULT_TOP_P))),
            stream=os.getenv('OPENROUTER_STREAM', str(DEFAULT_STREAM).lower()) == 'true'
        )

#=============================================================================
# INSTÂNCIAS GLOBAIS
#=============================================================================

# Criar instância padrão da configuração do modelo
OPENROUTER_CONFIG = ModelConfig.from_env()

#=============================================================================
# FUNÇÕES DE COMPATIBILIDADE
#=============================================================================

def make_openrouter_request(messages: List[Dict[str, str]]) -> Tuple[bool, Any]:
    """
    Wrapper para a função de requisição da classe ModelConfig.
    
    Mantido para compatibilidade com código existente que pode
    usar esta função diretamente.
    
    Args:
        messages: Lista de mensagens no formato OpenAI
    
    Returns:
        Tuple[bool, Any]: Tupla com status de sucesso e resultado ou mensagem de erro
    """
    return OPENROUTER_CONFIG.make_request(messages)