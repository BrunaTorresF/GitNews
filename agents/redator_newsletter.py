from datetime import datetime
from pathlib import Path
import json
from models.state import NewsletterState
from utils.file_manager import save_newsletter
from config.settings import OPENROUTER_CONFIG
import logging

# Configuração do logger específico para o redator de newsletter
logger = logging.getLogger("newsletter_generator.redator")

#=============================================================================
# CONSTANTES E CONFIGURAÇÕES E PROMPTS
#=============================================================================

# Constantes para prompts de seções
SECTION_PROMPTS = {
    "newsletter_title": """## SantaNews 📰""",

    "destaques": """Crie uma seção de destaques para a newsletter, apresentando os pontos mais importantes do repositório.
Siga EXATAMENTE esta estrutura para cada destaque:

### 1. **Problema real resolvido**  
📊 [Uma frase ESPECÍFICA descrevendo o problema que o projeto resolve, mencionando tecnologias ou conceitos REAIS do repositório]  
💡 **Por que isso importa?** [Uma frase explicando a importância com exemplos CONCRETOS]  

---

### 2. **Relevância tecnológica**  
🔗 [Uma frase sobre a relevância tecnológica, mencionando ESPECIFICAMENTE as tecnologias usadas no repositório]  
📈 **Por que isso é relevante?** [Uma frase explicando a relevância com DADOS CONCRETOS]  

---

### 3. **Aspecto técnico ou usabilidade**  
🧩 [Uma frase sobre um aspecto técnico ou de usabilidade, citando COMPONENTES REAIS do projeto]  
🛠️ **Por que isso é importante?** [Uma frase explicando a importância com EXEMPLOS ESPECÍFICOS (se der informações com números ou fatosprecisa dar a fonte)]  

---

### 🎯 **Conclusão: [Título da conclusão]**  
[Um parágrafo curto resumindo os destaques, mencionando o nome do repositório e suas características reais] 🚀✨

IMPORTANTE:
1. NÃO use descrições genéricas que poderiam se aplicar a qualquer projeto similar.
2. CITE NOMES ESPECÍFICOS de tecnologias, arquivos, funções ou componentes que existem no repositório.
3. Se não tiver informações suficientes, ADMITA EXPLICITAMENTE a limitação em vez de inventar.
4. NÃO mencione funcionalidades ou integrações a menos que tenha evidências concretas de que existem.
5. NÃO altere esta estrutura. NÃO adicione mais destaques. NÃO repita informações básicas que já estão na seção de visão geral.""",
    
    "casos_uso": """Crie uma seção de casos de uso práticos para o repositório.
Siga EXATAMENTE esta estrutura:

## Casos de Uso Práticos: Onde o **[Nome do Repositório]** brilha ✨

O projeto **[Nome do Repositório]** não é apenas um exemplo técnico, mas uma solução prática para diversos desafios reais. Abaixo, exploramos três cenários onde ele pode fazer a diferença:

---

### 1. **[Título do caso de uso: setor ou contexto]**  
**Problema:** [Descrição do problema em 2 frases]  
**Solução:** [Como o projeto resolve o problema em 2-3 frases]  
**Benefícios:**  
- [Benefício 1]  
- [Benefício 2]  
- [Benefício 3]  
**Perfis que se beneficiam:** [Lista de perfis ou funções]  

---

### 2. **[Título do caso de uso: setor ou contexto]**  
**Problema:** [Descrição do problema em 2 frases]  
**Solução:** [Como o projeto resolve o problema em 2-3 frases]  
**Benefícios:**  
- [Benefício 1]  
- [Benefício 2]  
- [Benefício 3]  
**Perfis que se beneficiam:** [Lista de perfis ou funções]  

---

### 3. **[Título do caso de uso: setor ou contexto]**  
**Problema:** [Descrição do problema em 2 frases]  
**Solução:** [Como o projeto resolve o problema em 2-3 frases]  
**Benefícios:**  
- [Benefício 1]  
- [Benefício 2]  
- [Benefício 3]  
**Perfis que se beneficiam:** [Lista de perfis ou funções]  

---

### Por que isso importa? 🌍  
[Um parágrafo curto explicando a importância geral] 🚀  

Pronto para implementar? Acesse o repositório e descubra como ele pode transformar o seu fluxo de trabalho! 🔗

NÃO altere esta estrutura. NÃO adicione mais casos de uso. NÃO repita informações básicas que já estão na seção de visão geral.""",
    
    "glossario": """Crie uma seção de glossário acessível para a newsletter.
Siga EXATAMENTE esta estrutura:

[Incluir emojis para cada Termo que combinar com o significado]

**[Termo 1]** 
[Definição breve e simples sobre o que é em 1-2 frases]  

**[Termo 2]**   
[Definição breve e simples sobre o que é em 1-2 frases]  

**[Termo 3]**   
[Definição breve e simples sobre o que é em 1-2 frases]  

**[Termo 4]**  
[Definição breve e simples sobre o que é em 1-2 frases]  

**[Termo 5]**   
[Definição breve e simples sobre o que é em 1-2 frases]  

Agora você está pronto para entender tudo sobre o projeto! 🚀

NÃO altere esta estrutura. NÃO adicione mais termos. Escolha apenas os 5 termos técnicos mais relevantes para o projeto.""",
}

# Prompt do sistema para o redator - define o comportamento e restrições da LLM
SYSTEM_PROMPT_REDATOR = """Você é um redator especializado em comunicação técnica inclusiva.
Sua função é transformar conteúdo técnico em material acessível, prático e relevante para diversos públicos.
Você deve seguir EXATAMENTE as estruturas fornecidas nos prompts para cada seção, sem alterações.
Não adicione seções extras, não modifique a formatação solicitada e não crie conteúdo fora do escopo definido.

IMPORTANTE: 
1. Siga rigorosamente a estrutura fornecida para cada seção.
2. Não repita informações básicas que já estão na seção de visão geral da newsletter.
3. Use linguagem clara e acessível, evitando jargões técnicos desnecessários.
4. Mantenha-se fiel aos dados fornecidos sobre o repositório, sem inventar funcionalidades ou características.
5. Use os emojis e formatação exatamente como indicado nos templates."""

#=============================================================================
# FUNÇÕES DE GERAÇÃO DE CONTEÚDO
#=============================================================================

def gerar_secao_llm(prompt: str, enhanced_content: str, basic_content: str) -> str:
    """
    Gera uma seção específica usando a LLM.
    
    Args:
        prompt: Prompt específico para a seção a ser gerada
        enhanced_content: Conteúdo aprimorado para referência
        basic_content: Conteúdo básico já presente na newsletter
        
    Returns:
        Texto da seção gerada pela LLM ou string vazia em caso de erro
    """

    try:
        logger.info("Iniciando geração de seção com LLM")
        
        # Construir o prompt do usuário combinando instruções específicas com conteúdos de referência
        user_prompt = f"""Com base no conteúdo fornecido, crie uma seção específica para a newsletter.

{prompt}

Conteúdo básico já presente na newsletter (NÃO REPITA ESTAS INFORMAÇÕES):
{basic_content[:1000]}  # Limita o conteúdo básico para evitar prompts muito longos

Conteúdo base para referência e análise:
{enhanced_content[:3000]}"""  # Limita o conteúdo de referência para evitar prompts muito longos
        
        # Preparar mensagens para o chat no formato esperado pela API
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_REDATOR},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.debug(f"Enviando requisição para API com prompt de {len(user_prompt)} caracteres")
        # Fazer requisição para a API
        success, result = OPENROUTER_CONFIG.make_request(messages)
        
        # Verificar se a requisição foi bem-sucedida
        if not success:
            logger.error(f"Erro ao gerar seção: {result}")
            return ""  # Retorna string vazia em caso de erro
        
        logger.info("Seção gerada com sucesso")
        logger.debug(f"Resposta recebida com {len(result['choices'][0]['message']['content'])} caracteres")
        
        # Extrai e retorna o conteúdo gerado pela LLM
        return result['choices'][0]['message']['content']
        
    except Exception as e:
        # Captura qualquer exceção não tratada para evitar falhas na pipeline
        logger.error(f"Erro ao gerar seção com LLM: {str(e)}", exc_info=True)
        return ""

#=============================================================================
# FUNÇÕES DE VALIDAÇÃO DE CONTEÚDO
#=============================================================================

def validar_secao(secao_nome: str, conteudo: str, repo_data: dict = None) -> bool:
    """
    Valida se o conteúdo da seção segue o formato esperado e tem qualidade adequada.
    
    Args:
        secao_nome: Nome da seção a ser validada
        conteudo: Conteúdo gerado pela LLM
        repo_data: Dados do repositório para validação de conteúdo
        
    Returns:
        bool: True se o conteúdo for válido, False caso contrário
    """
    logger.info(f"Validando seção: {secao_nome}")
    
    # Validação básica de tamanho mínimo para qualquer seção
    if not conteudo or len(conteudo) < 50:
        logger.warning(f"Conteúdo da seção '{secao_nome}' muito curto ou vazio")
        return False
    
    # Validações específicas para cada tipo de seção
    if secao_nome == "destaques":
        # Verificar se contém os 3 destaques e a conclusão
        if not "### 1. **" in conteudo or not "### 2. **" in conteudo or not "### 3. **" in conteudo:
            logger.warning(f"Seção '{secao_nome}' não contém os 3 destaques esperados")
            return False
        if not "### 🎯 **Conclusão:" in conteudo:
            logger.warning(f"Seção '{secao_nome}' não contém a conclusão esperada")
            return False
            
        # Verificar se o conteúdo é específico o suficiente usando dados do repositório
        if repo_data:
            # Lista de termos genéricos que indicam conteúdo vago ou genérico demais
            termos_genericos = [
                "o projeto resolve", "o sistema permite", "a aplicação oferece",
                "essa abordagem", "essa organização", "essa estrutura",
                "desenvolvedores que buscam", "empresas que precisam"
            ]
            
            # Contar ocorrências de termos genéricos para avaliar especificidade
            contagem_genericos = sum(1 for termo in termos_genericos if termo.lower() in conteudo.lower())
            
            # Se tiver muitos termos genéricos, considera o conteúdo vago demais
            if contagem_genericos > 3:
                logger.warning(f"Seção '{secao_nome}' contém muitos termos genéricos ({contagem_genericos})")
                return False
                
            # Verificar se menciona o nome do repositório - critério de relevância
            if repo_data.get('name') and repo_data['name'].lower() not in conteudo.lower():
                logger.warning(f"Seção '{secao_nome}' não menciona o nome do repositório")
                return False
                
            # Verificar se menciona tecnologias específicas - critério de especificidade
            if repo_data.get('language') and repo_data['language'].lower() not in conteudo.lower():
                logger.warning(f"Seção '{secao_nome}' não menciona a linguagem principal do repositório")
                return False
            
    elif secao_nome == "casos_uso":
        # Verificar se contém os 3 casos de uso conforme estrutura definida
        if not "### 1. **" in conteudo or not "### 2. **" in conteudo or not "### 3. **" in conteudo:
            logger.warning(f"Seção '{secao_nome}' não contém os 3 casos de uso esperados")
            return False
        # Verificar se cada caso de uso tem os elementos obrigatórios
        if not "**Problema:**" in conteudo or not "**Solução:**" in conteudo or not "**Benefícios:**" in conteudo:
            logger.warning(f"Seção '{secao_nome}' não segue a estrutura esperada para casos de uso")
            return False
            
    elif secao_nome == "glossario":
        # Verificar se contém pelo menos 5 termos no glossário
        termo_count = conteudo.count("**[") + conteudo.count("**") // 2
        if termo_count < 5:
            logger.warning(f"Seção '{secao_nome}' contém apenas {termo_count} termos, esperados 5")
            return False
    
    # Se passou por todas as validações, considera o conteúdo válido
    logger.info(f"Seção '{secao_nome}' validada com sucesso")
    return True

#=============================================================================
# MECANISMO DE GERAÇÃO COM CONTROLE DE QUALIDADE E RETENTATIVAS
# USA FUNÇÃO DE GERAÇÃO COM LLM(gerar_secao_llm) E FUNÇÃO DE VALIDAÇÃO DE CONTEÚDO(validar_secao) 
#=============================================================================

def gerar_secao_com_validacao(secao_nome: str, prompt: str, enhanced_content: str, basic_content: str, repo_data: dict = None, max_tentativas: int = 3) -> str:
    """
    Gera uma seção e valida se ela segue o formato esperado.
    Tenta novamente até max_tentativas vezes se a validação falhar.
    
    Args:
        secao_nome: Nome da seção a ser gerada
        prompt: Prompt para a LLM
        enhanced_content: Conteúdo aprimorado para referência
        basic_content: Conteúdo básico já presente na newsletter
        repo_data: Dados do repositório para validação de conteúdo
        max_tentativas: Número máximo de tentativas
        
    Returns:
        str: Conteúdo da seção gerada
    """
    # Loop de tentativas para gerar conteúdo válido
    for tentativa in range(1, max_tentativas + 1):
        logger.info(f"Gerando seção '{secao_nome}' - Tentativa {tentativa}/{max_tentativas}")
        
        # Gerar seção usando a LLM
        conteudo = gerar_secao_llm(prompt, enhanced_content, basic_content)
        
        # Validar o conteúdo gerado usando critérios específicos
        if validar_secao(secao_nome, conteudo, repo_data):
            logger.info(f"Seção '{secao_nome}' gerada e validada com sucesso na tentativa {tentativa}")
            return conteudo
        
        logger.warning(f"Seção '{secao_nome}' não passou na validação. Tentativa {tentativa}/{max_tentativas}")
        
        # Se for a última tentativa, retorna o melhor resultado disponível mesmo que não seja ideal
        if tentativa == max_tentativas:
            logger.warning(f"Número máximo de tentativas atingido para seção '{secao_nome}'. Retornando último resultado disponível.")
            return conteudo
    
    # Cláusula de segurança - não deveria chegar aqui devido ao retorno dentro do loop
    return ""

#=============================================================================
# FUNÇÃO PRINCIPAL DE REDAÇÃO DA NEWSLETTER
#=============================================================================

def redigir_newsletter(state: NewsletterState) -> NewsletterState:
    """
    Redige a newsletter final combinando o conteúdo básico com a análise gerada pelo LLM,
    adiciona seções específicas e salva o resultado em um arquivo.
    
    Args:
        state: Estado atual contendo o conteúdo básico, análise aprimorada e dados do repositório
        
    Returns:
        Estado atualizado com o conteúdo formatado da newsletter, caminho do arquivo de saída
        e métricas de geração, ou mensagem de erro em caso de falha
    """
    try:
        logger.info("Iniciando processo de redação da newsletter")
        
        #=============================================================================
        # VALIDAÇÃO DE DADOS DE ENTRADA
        #=============================================================================
        
        # Verifica se o conteúdo básico está presente no estado
        if not state.get('content'):
            error_msg = "Conteúdo básico não encontrado no estado"
            logger.error(error_msg)
            return {
                **state,
                'error': error_msg
            }
            
        # Verifica se a análise aprimorada está presente no estado
        if not state.get('enhanced_content'):
            error_msg = "Análise de conteúdo não encontrada no estado"
            logger.error(error_msg)
            return {
                **state,
                'error': error_msg
            }
        
        # Extrai os dados do repositório para uso nas funções de geração
        repo_data = state['repo_data']
        logger.info(f"Redigindo newsletter final para {repo_data['name']}")
        
        # Combinar o conteúdo básico com as seções geradas
        basic_content = state['content']
        
        #=============================================================================
        # GERAÇÃO DAS SEÇÕES ESPECÍFICAS
        #=============================================================================
        
        logger.info("Gerando seções específicas da newsletter")
        # Dicionário para armazenar as seções geradas
        secoes = {}
        
        # Gera cada seção definida nos prompts
        for nome, prompt in SECTION_PROMPTS.items():
            logger.info(f"Gerando seção: {nome}")
            # Gera e valida o conteúdo da seção
            secao_conteudo = gerar_secao_com_validacao(nome, prompt, state['enhanced_content'], basic_content, repo_data)
            
            # Tratamento para caso de falha na geração
            if not secao_conteudo:
                logger.warning(f"Conteúdo vazio gerado para a seção '{nome}'. Usando placeholder.")
                secao_conteudo = f"[Não foi possível gerar a seção {nome}]"
                
            # Armazena a seção gerada no dicionário
            secoes[nome] = secao_conteudo
            logger.info(f"Seção '{nome}' gerada com {len(secao_conteudo)} caracteres")
        
        #=============================================================================
        # MONTAGEM DO CONTEÚDO FINAL
        #=============================================================================
        
        # Divide o conteúdo básico para inserir as seções antes da linha de separação final
        logger.debug("Dividindo conteúdo básico para inserção das seções")
        parts = basic_content.split('---')
        
        # Tratamento para formato inesperado do conteúdo básico
        if len(parts) < 2:
            logger.warning("Formato do conteúdo básico não é o esperado. Ajustando estrutura.")
            parts = [basic_content, ""]  # Cria uma estrutura padrão
        
        # Construir o conteúdo formatado - agora sem repetir informações
        logger.info("Montando conteúdo final da newsletter com todas as seções")
        formatted_content = f"""{parts[0]}

## 🔍 Destaques
{secoes['destaques']}

## 💡 Casos de Uso Práticos
{secoes['casos_uso']}

## 📘 Glossário
{secoes['glossario']}

---
Newsletter gerada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"""
        
        #=============================================================================
        # SALVAMENTO E FINALIZAÇÃO
        #=============================================================================
        
        # Salva o conteúdo usando o gerenciador de arquivos
        logger.info(f"Salvando newsletter para o repositório {repo_data['name']}")
        try:
            # Utiliza função externa para salvar o arquivo
            output_file = save_newsletter(formatted_content, repo_data['name'])
            logger.info(f"Newsletter salva com sucesso em {output_file}")
        except Exception as e:
            # Tratamento de erro específico para falha no salvamento
            error_msg = f"Erro ao salvar newsletter: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                **state,
                'error': error_msg,
                'formatted_content': formatted_content  # Inclui o conteúdo gerado mesmo com erro
            }
        
        #=============================================================================
        # CÁLCULO DE MÉTRICAS
        #=============================================================================
        
        # Calcula métricas sobre o conteúdo gerado para monitoramento no log
        total_caracteres = len(formatted_content)
        total_palavras = len(formatted_content.split())
        tamanho_secoes = {
            "destaques": len(secoes['destaques']),
            "casos_uso": len(secoes['casos_uso']),
            "glossario": len(secoes['glossario'])
        }
        
        # Registra métricas no log
        logger.info(f"Newsletter gerada com {total_caracteres} caracteres e aproximadamente {total_palavras} palavras")
        logger.info(f"Tamanho das seções: Destaques ({tamanho_secoes['destaques']} caracteres), " +
                   f"Casos de Uso ({tamanho_secoes['casos_uso']} caracteres), " +
                   f"Glossário ({tamanho_secoes['glossario']} caracteres)")
        logger.info(f"Processo de redação da newsletter concluído com sucesso para {repo_data['name']}")
        
        # Retorna o estado atualizado com o conteúdo formatado, caminho do arquivo e métricas
        return {
            **state,
            'formatted_content': formatted_content,
            'output_file': output_file,
            'metrics': {
                'total_caracteres': total_caracteres,
                'total_palavras': total_palavras,
                'tamanho_secoes': tamanho_secoes
            }
        }
        
    except Exception as e:
        # Captura qualquer exceção não tratada para evitar falhas na pipeline
        error_msg = f"Erro ao redigir newsletter: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            **state,
            'error': error_msg
        } 