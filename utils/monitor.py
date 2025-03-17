import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configuração do logger específico para o monitor de execução
logger = logging.getLogger("newsletter_generator.monitor")

#=============================================================================
# CLASSE PARA MONITORAMENTO DE EXECUÇÃO
#=============================================================================

class ExecutionMonitor:
    """
    Monitor para acompanhar a execução do grafo em tempo real.
    
    Registra informações sobre cada etapa da execução, exibe logs no console
    e salva um relatório detalhado ao final do processamento.
    """
    
    def __init__(self):
        """
        Inicializa o monitor de execução.
        
        Configura diretórios para logs e inicializa variáveis de controle.
        """
        #=============================================================================
        # INICIALIZAÇÃO DE VARIÁVEIS
        #=============================================================================
        
        # Lista para armazenar informações sobre cada passo da execução
        self.steps: List[Dict[str, Any]] = []
        
        # Marcadores de tempo para medir a duração total da execução
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        #=============================================================================
        # CONFIGURAÇÃO DE DIRETÓRIOS
        #=============================================================================
        
        # Caminho da pasta raiz do projeto
        project_root = Path(__file__).parent.parent
        
        # Diretório de logs dentro do projeto
        self.output_dir = project_root / "logs"
        self.output_dir.mkdir(exist_ok=True)
        
        logger.debug("Monitor de execução inicializado")
    
    #=============================================================================
    # MÉTODOS DE CONTROLE DE EXECUÇÃO
    #=============================================================================
    
    def start_execution(self) -> None:
        """
        Inicia o monitoramento da execução.
        
        Registra o tempo de início e prepara a estrutura para coleta de dados.
        """
        self.start_time = time.time()
        self.steps = []
        logger.info("Iniciando execução do fluxo de trabalho")
        print("\n[MONITOR] Iniciando execução do grafo...")
    
    def end_execution(self) -> None:
        """
        Finaliza o monitoramento da execução.
        
        Registra o tempo de término e calcula a duração total.
        """
        self.end_time = time.time()
        duration = self.end_time - self.start_time if self.start_time else 0
        
        logger.info(f"Execução finalizada em {duration:.2f} segundos")
        print(f"\n[MONITOR] Execução finalizada em {duration:.2f} segundos")
        
        if self.steps:
            execution_path = ' -> '.join([step['node'] for step in self.steps])
            logger.info(f"Caminho de execução: {execution_path}")
            print(f"[MONITOR] Caminho de execução: {execution_path}")
    
    #=============================================================================
    # MÉTODOS DE REGISTRO DE PASSOS
    #=============================================================================
    
    def record_step(self, node_name: str, state: Dict[str, Any]) -> None:
        """
        Registra um passo na execução (método legado para compatibilidade).
        
        Args:
            node_name: Nome do nó (agente) em execução
            state: Estado atual do pipeline
        """
        # Filtrar estado para não incluir dados grandes
        filtered_state = {k: v for k, v in state.items() if k != 'repo_data'}
        if 'repo_data' in state and state['repo_data']:
            filtered_state['repo_name'] = state['repo_data'].get('name', 'N/A')
        
        # Criar informações do passo
        step_info = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "node": node_name,
            "state": filtered_state
        }
        self.steps.append(step_info)
        
        # Exibir informação sobre o passo
        print(f"[MONITOR] {step_info['timestamp']} - Executando nó: {node_name}")
        
        # Mostrar informações relevantes do estado
        self._log_relevant_state_info(node_name, state)
    
    def record_step_start(self, node_name: str) -> None:
        """
        Registra o início da execução de um nó.
        
        Args:
            node_name: Nome do nó (agente) que está iniciando a execução
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        logger.info(f"Iniciando nó: {node_name}")
        print(f"[MONITOR] {timestamp} - Iniciando nó: {node_name}")
    
    def record_step_end(self, node_name: str, state: Dict[str, Any]) -> None:
        """
        Registra o fim da execução de um nó e salva o estado.
        
        Args:
            node_name: Nome do nó (agente) que concluiu a execução
            state: Estado atual após execução do nó
        """
        # Filtrar estado para não incluir dados grandes
        filtered_state = {k: v for k, v in state.items() if k != 'repo_data'}
        if 'repo_data' in state and state['repo_data']:
            filtered_state['repo_name'] = state['repo_data'].get('name', 'N/A')
        
        # Criar informações do passo
        step_info = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "node": node_name,
            "state": filtered_state
        }
        self.steps.append(step_info)
        
        # Exibir informação sobre o passo
        logger.info(f"Concluído nó: {node_name}")
        print(f"[MONITOR] {step_info['timestamp']} - Concluído nó: {node_name}")
        
        # Mostrar informações relevantes do estado
        self._log_relevant_state_info(node_name, state)
    
    def record_step_error(self, node_name: str, error_message: str) -> None:
        """
        Registra um erro na execução de um nó.
        
        Args:
            node_name: Nome do nó (agente) onde ocorreu o erro
            error_message: Mensagem detalhada do erro
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        logger.error(f"Erro no nó {node_name}: {error_message}")
        print(f"[MONITOR] {timestamp} - Erro no nó {node_name}: {error_message}")
        
        # Adicionar ao histórico de passos
        step_info = {
            "timestamp": timestamp,
            "node": node_name,
            "error": error_message
        }
        self.steps.append(step_info)
    
    #=============================================================================
    # MÉTODOS AUXILIARES
    #=============================================================================
    
    def _log_relevant_state_info(self, node_name: str, state: Dict[str, Any]) -> None:
        """
        Exibe informações relevantes do estado específicas para cada nó.
        
        Args:
            node_name: Nome do nó (agente) que gerou o estado
            state: Estado atual do pipeline
        """
        # Mostrar erro se existir
        if 'error' in state and state['error']:
            logger.error(f"Erro no nó {node_name}: {state['error']}")
            print(f"  [ERRO] {state['error']}")
            
        # Informações específicas para cada tipo de nó
        if node_name == 'github_agent' and 'repo_data' in state and state['repo_data']:
            repo_name = state['repo_data'].get('name', 'N/A')
            logger.info(f"Dados obtidos para repositório: {repo_name}")
            print(f"  [INFO] Dados obtidos para repositório: {repo_name}")
            
        if node_name == 'estruturador_newsletter' and 'content' in state and state['content']:
            content_len = len(state['content'])
            logger.info(f"Estrutura básica gerada: {content_len} caracteres")
            print(f"  [INFO] Estrutura básica gerada: {content_len} caracteres")
            
        if node_name == 'content_generator' and 'enhanced_content' in state and state['enhanced_content']:
            content_len = len(state['enhanced_content'])
            logger.info(f"Conteúdo melhorado com LLM: {content_len} caracteres")
            print(f"  [INFO] Conteúdo melhorado com LLM: {content_len} caracteres")
            
        if node_name == 'redator_newsletter' and 'formatted_content' in state and state['formatted_content']:
            content_len = len(state['formatted_content'])
            logger.info(f"Newsletter formatada com {content_len} caracteres")
            print(f"  [INFO] Newsletter formatada com {content_len} caracteres")
    
    #=============================================================================
    # MÉTODOS DE PERSISTÊNCIA
    #=============================================================================
    
    def save_execution_log(self) -> str:
        """
        Salva o log de execução em um arquivo JSON.
        
        Gera um relatório detalhado com todos os passos da execução,
        tempos de início e término, duração total e estados parciais.
        
        Returns:
            Caminho do arquivo de log salvo
        """
        # Verificar se a execução foi iniciada e finalizada
        if not self.start_time or not self.end_time:
            logger.warning("Tentativa de salvar log sem iniciar ou finalizar execução")
            return ""
            
        # Preparar dados do log
        log_data = {
            "execution_path": [step['node'] for step in self.steps],
            "start_time": datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": datetime.fromtimestamp(self.end_time).strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round(self.end_time - self.start_time, 2),
            "steps": self.steps
        }
        
        # Gerar nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.output_dir / f"execution_log_{timestamp}.json"
        
        # Salvar dados no arquivo
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Log de execução salvo em {filename}")
            print(f"[MONITOR] Log de execução salvo em {filename}")
            return str(filename)
            
        except Exception as e:
            error_msg = f"Erro ao salvar log de execução: {str(e)}"
            logger.error(error_msg)
            print(f"[ERRO] {error_msg}")
            return ""