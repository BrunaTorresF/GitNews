import logging
from typing import Literal, Dict, Any, Optional

from langgraph.graph import Graph, END, START

from models.state import NewsletterState
from agents.github_agent import github_agent
from agents.estruturador_newsletter import estruturar_newsletter
from agents.gerador_newsletter import content_generator
from agents.redator_newsletter import redigir_newsletter

#=============================================================================
# CONFIGURAÇÃO DO LOGGER
#=============================================================================

logger = logging.getLogger("newsletter_generator.workflow")

#=============================================================================
# FUNÇÕES DE CONTROLE DE FLUXO
#=============================================================================

def determine_next(state: NewsletterState) -> Literal["estruturador_newsletter", "content_generator", "redator_newsletter", "__end__"]:
    """
    Determina o próximo passo do workflow baseado no estado atual.
    
    Função de roteamento que avalia o estado atual da newsletter
    e decide qual deve ser o próximo agente a ser executado na
    sequência de processamento ou se o processamento deve ser
    finalizado.
    
    Args:
        state: Estado atual da newsletter contendo todos os dados
              processados até o momento
    
    Returns:
        Literal: Nome do próximo nó a ser executado ou END para finalizar
    """
    # Verificar se ocorreu algum erro em etapas anteriores
    if state.get('error'):
        logger.warning(f"Erro detectado, encerrando workflow: {state.get('error')}")
        return END
    
    # Roteamento com base no estado atual dos dados
    if state.get('repo_data') and not state.get('content'):
        # Dados do repositório obtidos, prosseguir para estruturação
        logger.info("Avançando para estruturação da newsletter")
        return "estruturador_newsletter"
        
    if state.get('content') and not state.get('enhanced_content'):
        # Estrutura básica obtida, prosseguir para geração de conteúdo
        logger.info("Avançando para geração de conteúdo avançado")
        return "content_generator"
        
    if state.get('enhanced_content') and not state.get('formatted_content'):
        # Conteúdo aprimorado obtido, prosseguir para formatação final
        logger.info("Avançando para redação da newsletter")
        return "redator_newsletter"
    
    # Se todas as etapas foram concluídas, finalizar
    logger.info("Workflow concluído")
    return END

#=============================================================================
# FUNÇÕES DE CRIAÇÃO DE WORKFLOW
#=============================================================================

def create_workflow() -> Any:
    """
    Cria o grafo de workflow do LangGraph.
    
    Configura todos os nós e arestas que definem o fluxo de processamento
    da newsletter, incluindo os pontos de decisão para roteamento
    condicional entre os agentes.
    
    Returns:
        Grafo compilado pronto para execução
    """
    logger.info("Criando grafo de workflow")
    
    #=============================================================================
    # CRIAÇÃO E CONFIGURAÇÃO DO GRAFO
    #=============================================================================
    
    # Criar instância do grafo
    workflow = Graph()

    #=============================================================================
    # ADIÇÃO DE NÓS AO GRAFO
    #=============================================================================
    
    # Adicionar nós representando cada agente do sistema
    workflow.add_node("github_agent", github_agent)
    workflow.add_node("estruturador_newsletter", estruturar_newsletter)
    workflow.add_node("content_generator", content_generator)
    workflow.add_node("redator_newsletter", redigir_newsletter)

    #=============================================================================
    # CONFIGURAÇÃO DO FLUXO DE EXECUÇÃO
    #=============================================================================
    
    # Definir o ponto de entrada no grafo
    workflow.add_edge(START, "github_agent")
    
    # Definir transições condicionais após obtenção dos dados do GitHub
    workflow.add_conditional_edges(
        "github_agent",
        determine_next,
        {
            "estruturador_newsletter": "estruturador_newsletter",
            END: END
        }
    )
    
    # Definir transições condicionais após estruturação da newsletter
    workflow.add_conditional_edges(
        "estruturador_newsletter",
        determine_next,
        {
            "content_generator": "content_generator",
            END: END
        }
    )
    
    # Definir transições condicionais após geração de conteúdo
    workflow.add_conditional_edges(
        "content_generator",
        determine_next,
        {
            "redator_newsletter": "redator_newsletter",
            END: END
        }
    )
    
    # Definir transição final após redação da newsletter
    workflow.add_edge("redator_newsletter", END)

    #=============================================================================
    # COMPILAÇÃO DO GRAFO
    #=============================================================================
    
    # Compilar e retornar o grafo pronto para execução
    return workflow.compile()