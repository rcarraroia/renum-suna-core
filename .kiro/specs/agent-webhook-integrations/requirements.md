# Requirements Document

## Introduction

O Painel de Integrações de Agentes + Webhooks Externos é um módulo híbrido e seguro que permite que agentes da plataforma RENUM sejam acionados por sistemas externos (apps, WhatsApp, Telegram, sites, n8n, Zapier etc) através de webhooks autenticados. O sistema oferece painéis de gestão visual diferenciados para Administradores e Clientes, garantindo segurança, controle de acesso e facilidade de uso.

## Requirements

### Requirement 1

**User Story:** Como administrador da plataforma, eu quero gerenciar todas as integrações de agentes com sistemas externos, para que eu possa ter controle total sobre as conexões e monitorar o uso da plataforma.

#### Acceptance Criteria

1. WHEN o administrador acessa o painel de integrações THEN o sistema SHALL exibir todos os agentes e seus canais conectados
2. WHEN o administrador cria uma nova integração THEN o sistema SHALL gerar um token único e URL de webhook
3. WHEN o administrador testa uma integração THEN o sistema SHALL permitir envio de payload simulado e exibir a resposta
4. WHEN o administrador regenera um token THEN o sistema SHALL invalidar o token anterior e criar um novo
5. WHEN o administrador visualiza integrações THEN o sistema SHALL mostrar status (ativo/inativo) de cada integração

### Requirement 2

**User Story:** Como cliente da plataforma, eu quero conectar meus agentes a sistemas externos de forma autônoma, para que eu possa integrar os agentes aos meus fluxos de trabalho sem depender de suporte técnico.

#### Acceptance Criteria

1. WHEN o cliente acessa suas integrações THEN o sistema SHALL exibir apenas os agentes do próprio cliente
2. WHEN o cliente ativa um canal externo THEN o sistema SHALL permitir seleção via dropdown (WhatsApp, Zapier, etc)
3. WHEN o cliente gera um webhook THEN o sistema SHALL criar token exclusivo e URL específica para o agente
4. WHEN o cliente testa a integração THEN o sistema SHALL permitir envio de JSON e exibir resposta do agente
5. WHEN o cliente desativa uma integração THEN o sistema SHALL invalidar o token e marcar como inativo

### Requirement 3

**User Story:** Como sistema externo, eu quero acionar agentes da plataforma RENUM via webhook, para que eu possa integrar a inteligência artificial aos meus processos automatizados.

#### Acceptance Criteria

1. WHEN um sistema externo faz POST para /webhook/{agent_id} THEN o sistema SHALL validar o token Bearer
2. WHEN o token é válido THEN o sistema SHALL verificar se agente e cliente estão ativos
3. WHEN as validações passam THEN o sistema SHALL executar o agente e retornar resposta JSON
4. WHEN há erro de autenticação THEN o sistema SHALL retornar status 403 com mensagem apropriada
5. WHEN há limite de uso excedido THEN o sistema SHALL retornar status 429 com informações do limite

### Requirement 4

**User Story:** Como administrador de segurança, eu quero que todas as integrações sejam seguras e auditáveis, para que a plataforma mantenha integridade e controle de acesso adequados.

#### Acceptance Criteria

1. WHEN uma integração é criada THEN o sistema SHALL gerar token único e criptografado
2. WHEN há tentativa de acesso THEN o sistema SHALL validar escopo limitado por cliente e agente
3. WHEN há múltiplas chamadas THEN o sistema SHALL aplicar rate limiting por cliente/minuto
4. WHEN há atividade suspeita THEN o sistema SHALL registrar tentativas de acesso inválidas
5. WHEN tokens são regenerados THEN o sistema SHALL invalidar imediatamente tokens anteriores

### Requirement 5

**User Story:** Como desenvolvedor integrando sistemas, eu quero documentação clara e testes funcionais, para que eu possa implementar a integração de forma eficiente e confiável.

#### Acceptance Criteria

1. WHEN acesso a documentação THEN o sistema SHALL fornecer exemplos de payload e resposta
2. WHEN testo a integração THEN o sistema SHALL permitir simulação com diferentes tipos de dados
3. WHEN há erro na integração THEN o sistema SHALL retornar mensagens de erro descritivas
4. WHEN consulto status THEN o sistema SHALL fornecer informações sobre saúde da integração
5. WHEN implemento rate limiting THEN o sistema SHALL informar limites atuais nos headers de resposta

### Requirement 6

**User Story:** Como cliente, eu quero monitorar o uso das minhas integrações, para que eu possa acompanhar a performance e identificar possíveis problemas.

#### Acceptance Criteria

1. WHEN cliente acessa histórico THEN o sistema SHALL exibir últimas chamadas realizadas
2. WHEN há falhas na integração THEN o sistema SHALL registrar e exibir erros ocorridos
3. WHEN consulta métricas THEN o sistema SHALL mostrar quantidade de chamadas por período
4. WHEN verifica status THEN o sistema SHALL indicar se integração está funcionando corretamente
5. WHEN há limite próximo THEN o sistema SHALL alertar sobre aproximação do rate limit