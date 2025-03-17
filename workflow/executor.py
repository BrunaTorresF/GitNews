import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from langgraph.graph import Graph, END, START

from models.state import NewsletterState
from utils.monitor import ExecutionMonitor
from workflow.graph import create_workflow
from agents.github_agent import github_agent
from agents.estruturador_newsletter import estruturar_newsletter
from agents.gerador_newsletter import content_generator
from agents.redator_newsletter import redigir_newsletter
from workflow.graph import determine_next

#=============================================================================
# CONFIGURAÇÃO DO LOGGER
#=============================================================================

logger = logging.getLogger("newsletter_generator.executor")

#=============================================================================
# CLASSE EXECUTORA DO WORKFLOW
#=============================================================================

class WorkflowExecutor:
    """
    Executa o workflow com monitoramento integrado.
    
    Responsável por criar, configurar e executar o grafo de workflow,
    integrando o monitoramento de execução para acompanhamento e
    diagnóstico de cada etapa.
    """
    
    def __init__(self):
        """
        Inicializa o executor de workflow.
        
        Cria o monitor de execução e configura o grafo de workflow
        com cada passo monitorado.
        """
        # Inicializar monitor de execução para acompanhamento
        self.monitor = ExecutionMonitor()
        
        # Criar grafo de workflow com monitoramento integrado
        self.app = self._create_monitored_workflow()
    
    def _create_monitored_workflow(self) -> Any:
        """
        Cria workflow com monitoramento integrado.
        
        Adiciona wrappers para monitoramento em cada nó do grafo,
        registrando início, fim e possíveis erros em cada etapa.
        
        Returns:
            Grafo de workflow compilado e pronto para execução
        """
        #=============================================================================
        # CRIAÇÃO E CONFIGURAÇÃO DO GRAFO
        #=============================================================================
        
        # Criar instância do grafo
        workflow = Graph()
        
        #=============================================================================
        # DEFINIÇÃO DE WRAPPERS DE MONITORAMENTO
        #=============================================================================
        
        def monitored_github_agent(state: Dict[str, Any]) -> Dict[str, Any]:
            """Wrapper para monitorar a execução do agente GitHub."""
            self.monitor.record_step_start("github_agent")
            try:
                result = github_agent(state)
                self.monitor.record_step_end("github_agent", result)
                return result
            except Exception as e:
                self.monitor.record_step_error("github_agent", str(e))
                raise
            
        def monitored_estruturador_newsletter(state: Dict[str, Any]) -> Dict[str, Any]:
            """Wrapper para monitorar a execução do estruturador da newsletter."""
            self.monitor.record_step_start("estruturador_newsletter")
            try:
                result = estruturar_newsletter(state)
                self.monitor.record_step_end("estruturador_newsletter", result)
                return result
            except Exception as e:
                self.monitor.record_step_error("estruturador_newsletter", str(e))
                raise
            
        def monitored_content_generator(state: Dict[str, Any]) -> Dict[str, Any]:
            """Wrapper para monitorar a execução do gerador de conteúdo."""
            self.monitor.record_step_start("content_generator")
            try:
                result = content_generator(state)
                self.monitor.record_step_end("content_generator", result)
                return result
            except Exception as e:
                self.monitor.record_step_error("content_generator", str(e))
                raise
            
        def monitored_redator_newsletter(state: Dict[str, Any]) -> Dict[str, Any]:
            """Wrapper para monitorar a execução do redator da newsletter."""
            self.monitor.record_step_start("redator_newsletter")
            try:
                result = redigir_newsletter(state)
                self.monitor.record_step_end("redator_newsletter", result)
                return result
            except Exception as e:
                self.monitor.record_step_error("redator_newsletter", str(e))
                raise
        
        #=============================================================================
        # CONFIGURAÇÃO DO GRAFO DE WORKFLOW
        #=============================================================================
        
        # Adicionar nós com monitoramento
        workflow.add_node("github_agent", monitored_github_agent)
        workflow.add_node("estruturador_newsletter", monitored_estruturador_newsletter)
        workflow.add_node("content_generator", monitored_content_generator)
        workflow.add_node("redator_newsletter", monitored_redator_newsletter)
    
        # Configurar fluxo
        workflow.add_edge(START, "github_agent")
        workflow.add_conditional_edges(
            "github_agent",
            determine_next,
            {
                "estruturador_newsletter": "estruturador_newsletter",
                END: END
            }
        )
        workflow.add_conditional_edges(
            "estruturador_newsletter",
            determine_next,
            {
                "content_generator": "content_generator",
                END: END
            }
        )
        workflow.add_conditional_edges(
            "content_generator",
            determine_next,
            {
                "redator_newsletter": "redator_newsletter",
                END: END
            }
        )
        workflow.add_edge("redator_newsletter", END)
    
        # Compilar e retornar o workflow
        return workflow.compile()
    
    def execute(self, repo_url: str) -> str:
        """
        Executa o workflow para um repositório.
        
        Inicializa o estado da newsletter com a URL do repositório,
        executa o grafo completo de processamento e retorna o
        caminho do arquivo de saída gerado.
        
        Args:
            repo_url: URL do repositório GitHub para análise
        
        Returns:
            str: Caminho do arquivo de newsletter gerado
            
        Raises:
            Exception: Se ocorrer algum erro durante a execução
        """
        logger.info(f"Iniciando execução para repositório: {repo_url}")
        
        #=============================================================================
        # INICIALIZAÇÃO DO ESTADO
        #=============================================================================
        
        # Criar estado inicial com a URL do repositório
        initial_state = NewsletterState(
            repo_url=repo_url,
            repo_data=None,
            content=None,
            enhanced_content=None,
            formatted_content=None,
            output_file=None,
            error=None
        )
        
        #=============================================================================
        # EXECUÇÃO DO GRAFO E MONITORAMENTO
        #=============================================================================
        
        try:
            # Iniciar monitoramento da execução
            self.monitor.start_execution()
            
            # Executar o grafo completo com o estado inicial
            final_state = self.app.invoke(initial_state)
            
            # Finalizar monitoramento e salvar log
            self.monitor.end_execution()
            log_file = self.monitor.save_execution_log()
            logger.info(f"Log de execução salvo em: {log_file}")
            
            #=============================================================================
            # VERIFICAÇÃO DE ERROS E RETORNO
            #=============================================================================
            
            # Verificar se houve erro durante a execução
            if final_state.get('error'):
                error_msg = final_state['error']
                logger.error(f"Erro encontrado: {error_msg}")
                raise Exception(error_msg)
            
            # Verificar se foi gerado o arquivo de saída
            output_file = final_state.get('output_file', '')
            if not output_file:
                logger.warning("Nenhum arquivo de saída foi gerado")
                
            logger.info(f"Newsletter gerada com sucesso: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Erro durante execução: {str(e)}")
            # Propagar o erro para o chamador
            raise