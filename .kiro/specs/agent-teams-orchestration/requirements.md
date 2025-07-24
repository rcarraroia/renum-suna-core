# Especificação: Sistema de Equipes de Agentes - Módulo de Orquestração

## Visão Geral

Implementar um sistema completo de "Equipes de Agentes" na Plataforma Renum Suna, permitindo que usuários criem, configurem e executem equipes coordenadas de agentes de IA para resolver tarefas complexas que requerem múltiplas especialidades.

## Objetivos

### Objetivo Principal
Criar um sistema robusto de orquestração que permita a coordenação inteligente de múltiplos agentes, com comunicação inter-agentes, contexto compartilhado e diferentes estratégias de execução.

### Objetivos Específicos
1. **Orquestração Flexível**: Suportar diferentes padrões de execução (sequencial, paralelo, pipeline, condicional)
2. **Comunicação Inter-agentes**: Sistema de mensagens e contexto compartilhado
3. **Interface Intuitiva**: Builder visual para criação e configuração de equipes
4. **Monitoramento Avançado**: Dashboards e métricas de performance das equipes
5. **Integração Orgânica**: Aproveitar máximo da infraestrutura existente

## Requisitos Funcionais

### RF007 - Interface Builder para Equipes (UI/UX)
- **Como** usuário da plataforma
- **Eu quero** uma interface visual intuitiva para criar e gerenciar equipes
- **Para que** eu possa facilmente configurar fluxos complexos sem conhecimento técnico

**Critérios de Aceitação:**
- [ ] Página /teams/new para criação de equipes
- [ ] Página /teams/[id] para detalhes e gerenciamento
- [ ] Seleção visual de agentes existentes para compor equipe
- [ ] Definição visual do fluxo de trabalho (arrastar e soltar)
- [ ] Conectar agentes visualmente para definir sequência
- [ ] Configuração de condições para transição entre agentes
- [ ] Preview do workflow antes da execução
- [ ] Templates pré-configurados para casos comuns

## Requisitos Funcionais

### RF001 - Criação de Equipes no Backend Renum
- **Como** usuário da plataforma
- **Eu quero** criar equipes de agentes selecionando agentes existentes
- **Para que** eu possa coordenar múltiplos agentes em uma tarefa complexa

**Critérios de Aceitação:**
- [ ] Usuário pode criar nova equipe com nome e descrição
- [ ] Usuário pode adicionar/remover agentes da equipe (lista de agent_ids)
- [ ] Usuário pode definir workflow_definition (JSON/DSL) para orquestração
- [ ] Sistema valida que todos os agentes pertencem ao mesmo account_id
- [ ] Backend Renum atua como "cérebro" da equipe, delegando ao Suna Core
- [ ] Suna Core permanece inalterado em sua funcionalidade principal

### RF002 - Configuração de Estratégias de Execução
- **Como** usuário da plataforma
- **Eu quero** escolher como os agentes da equipe irão executar
- **Para que** eu possa otimizar a execução conforme o tipo de tarefa

**Critérios de Aceitação:**
- [ ] Suporte a execução sequencial (um por vez)
- [ ] Suporte a execução paralela (todos simultaneamente)
- [ ] Suporte a execução em pipeline (saída de um é entrada do próximo)
- [ ] Suporte a execução condicional (baseada em resultados)
- [ ] Interface visual para configurar estratégia

### RF003 - Contexto Compartilhado Aprimorado
- **Como** agente em uma equipe
- **Eu quero** acessar informações compartilhadas pela equipe
- **Para que** eu possa tomar decisões baseadas no trabalho de outros agentes

**Critérios de Aceitação:**
- [ ] Context object atualizado por cada agente e passado para o próximo
- [ ] Memory compartilhado gerenciado via Redis para comunicação rápida
- [ ] Contexto é persistido durante toda a execução da equipe
- [ ] Contexto é isolado por execução de equipe
- [ ] Sistema de versionamento para mudanças no contexto
- [ ] Suporte a API keys personalizadas por usuário/equipe

### RF004 - Comunicação Inter-agentes
- **Como** agente em uma equipe
- **Eu quero** enviar mensagens para outros agentes
- **Para que** eu possa coordenar ações e compartilhar resultados

**Critérios de Aceitação:**
- [ ] Agente pode enviar mensagem para agente específico
- [ ] Agente pode fazer broadcast para toda a equipe
- [ ] Agente pode solicitar resposta de outro agente
- [ ] Sistema de timeout para mensagens não respondidas
- [ ] Log de todas as mensagens trocadas

### RF005 - Execução de Equipes
- **Como** usuário da plataforma
- **Eu quero** executar uma equipe de agentes
- **Para que** eu possa resolver tarefas complexas automaticamente

**Critérios de Aceitação:**
- [ ] Usuário pode iniciar execução de equipe com prompt inicial
- [ ] Sistema cria plano de execução baseado na configuração
- [ ] Sistema coordena execução conforme estratégia definida
- [ ] Sistema gerencia dependências entre agentes
- [ ] Sistema permite parar execução em andamento

### RF006 - Monitoramento e Atribuição de Custos
- **Como** usuário da plataforma
- **Eu quero** acompanhar o progresso da execução da equipe e custos associados
- **Para que** eu possa entender o que está acontecendo, intervir se necessário e controlar gastos

**Critérios de Aceitação:**
- [ ] Dashboard em tempo real do status de cada agente
- [ ] Visualização do fluxo de execução
- [ ] Log detalhado de todas as ações
- [ ] Métricas de performance (tempo, tokens, custos) por agente individual
- [ ] Sistema de logging que captura consumo de modelos IA por agente
- [ ] Atribuição correta de custos ao user_id da equipe
- [ ] Suporte a API keys personalizadas do usuário
- [ ] Preparação para futuro modelo de billing nativo
- [ ] Alertas para falhas ou problemas

## Requisitos Não Funcionais

### RNF001 - Performance
- Sistema deve suportar até 10 agentes por equipe simultaneamente
- Latência máxima de 2 segundos para coordenação entre agentes
- Throughput mínimo de 100 execuções de equipe por hora

### RNF002 - Escalabilidade
- Arquitetura deve permitir escalar horizontalmente
- Suporte a múltiplas execuções de equipe simultâneas
- Isolamento completo entre execuções diferentes

### RNF003 - Confiabilidade
- Sistema deve ter 99.9% de uptime
- Recuperação automática de falhas de agentes individuais
- Backup automático de contexto compartilhado

### RNF004 - Segurança
- Isolamento completo entre equipes de diferentes usuários
- Auditoria completa de todas as ações
- Controle de acesso baseado em roles

### RNF005 - Usabilidade
- Interface intuitiva para usuários não técnicos
- Tempo máximo de 5 minutos para criar primeira equipe
- Documentação e tutoriais integrados

## Casos de Uso Prioritários

### CU001 - Equipe de Análise de Mercado
**Agentes:**
- Pesquisador: Coleta dados de mercado e concorrentes
- Analista: Processa dados e identifica tendências
- Relator: Gera relatório executivo final

**Fluxo:** Sequencial (Pesquisador → Analista → Relator)

### CU002 - Equipe de Desenvolvimento de Software
**Agentes:**
- Arquiteto: Define estrutura e tecnologias
- Desenvolvedor: Implementa código
- Testador: Executa testes e validações

**Fluxo:** Pipeline com feedback loops

### CU003 - Equipe de Atendimento ao Cliente
**Agentes:**
- Triagem: Classifica e prioriza solicitações
- Especialista: Resolve problemas específicos
- Seguimento: Acompanha satisfação do cliente

**Fluxo:** Condicional baseado no tipo de solicitação

## Restrições e Limitações

### Técnicas
- Máximo de 10 agentes por equipe (Fase 1)
- Suporte inicial apenas para agentes do mesmo account_id
- Integração apenas com LLMs já suportados pela plataforma

### Negócio
- Funcionalidade disponível apenas para planos pagos
- Limite de execuções simultâneas baseado no plano do usuário
- Auditoria obrigatória para todas as execuções

## Dependências

### Internas
- Sistema de agentes existente
- ThreadManager e sistema de mensagens
- Redis para comunicação assíncrona
- Supabase para persistência
- Sistema de billing existente

### Externas
- Nenhuma dependência externa adicional identificada

## Critérios de Sucesso

### Técnicos
- [ ] 100% dos casos de uso prioritários implementados
- [ ] Testes automatizados com cobertura > 90%
- [ ] Performance dentro dos limites especificados
- [ ] Zero regressões na funcionalidade existente

### Negócio
- [ ] Usuários conseguem criar equipes em < 5 minutos
- [ ] Taxa de sucesso de execuções > 95%
- [ ] Feedback positivo de usuários beta > 4.5/5
- [ ] Aumento de 30% no engagement dos usuários

## Riscos Identificados

### Alto Risco
- **Complexidade de coordenação**: Deadlocks e condições de corrida
- **Performance com múltiplos agentes**: Sobrecarga do sistema
- **Consistência de estado**: Estado inconsistente entre agentes

### Médio Risco
- **Complexidade da interface**: UX muito complexa para usuários
- **Custos de execução**: Custos elevados com múltiplos LLMs
- **Integração com sistema existente**: Conflitos com funcionalidades atuais

### Baixo Risco
- **Adoção pelos usuários**: Resistência a nova funcionalidade
- **Documentação**: Falta de documentação adequada

## Próximos Passos

1. **Aprovação da Spec**: Validar requisitos com stakeholders
2. **Design Técnico**: Detalhar arquitetura e componentes
3. **Prototipagem**: Criar MVP da orquestração básica
4. **Desenvolvimento Iterativo**: Implementar por fases
5. **Testes com Usuários**: Validar com usuários beta

## Glossário

- **Equipe de Agentes**: Conjunto coordenado de agentes que trabalham juntos
- **Orquestração**: Coordenação automática da execução dos agentes
- **Contexto Compartilhado**: Área de memória compartilhada entre agentes da equipe
- **Estratégia de Execução**: Padrão de como os agentes executam (sequencial, paralelo, etc.)
- **Message Bus**: Sistema de mensagens entre agentes
- **Execution Plan**: Plano detalhado de como a equipe será executada