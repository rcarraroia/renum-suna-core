# Editor de Membros da Equipe

## Visão Geral

O editor de membros da equipe permite aos usuários configurar os agentes que fazem parte de uma equipe, definindo suas funções, ordem de execução e visualizando como eles interagem entre si.

## Componentes Implementados

### Página Principal (`[id]/members.tsx`)

- **Editor de Membros**: Interface para configurar os membros da equipe
- **Preview da Ordem de Execução**: Visualização da ordem de execução dos agentes
- **Gerenciamento de Estado**: Estado local para dados dos agentes
- **Integração com API**: Uso do hook `useUpdateTeam` para enviar as alterações

### Componentes Específicos

- **TeamMembersEditor**: Componente para edição de membros com drag & drop
- **ExecutionOrderPreview**: Componente para visualização da ordem de execução

## Funcionalidades

1. **Drag & Drop para Reordenar Agentes**
   - Interface intuitiva para arrastar e soltar agentes
   - Atualização automática da ordem de execução
   - Feedback visual durante o arrasto

2. **Configuração de Roles e Dependências**
   - Seleção de papel para cada agente (Líder, Coordenador, Membro, Revisor)
   - Configuração de ordem de execução para workflows sequenciais
   - Validação de configurações

3. **Preview da Ordem de Execução**
   - Visualização gráfica da ordem de execução
   - Representação diferente para cada tipo de workflow
   - Exibição de papéis e dependências

4. **Salvamento de Alterações**
   - Botão para salvar alterações
   - Feedback de sucesso ou erro
   - Validação antes do envio

## Tipos de Workflow

O editor se adapta ao tipo de workflow da equipe:

1. **Workflow Sequencial**
   - Exibe campos para definir a ordem de execução
   - Permite reordenar agentes com drag & drop
   - Mostra um preview linear da sequência de execução

2. **Workflow Paralelo**
   - Permite reordenar agentes para fins de organização
   - Mostra um preview em grid dos agentes executados em paralelo

3. **Workflow Condicional**
   - Permite reordenar agentes para fins de organização
   - Exibe uma mensagem informando que a configuração detalhada é feita no editor avançado

## Integração com React Beautiful DnD

O componente utiliza a biblioteca React Beautiful DnD para implementar a funcionalidade de drag & drop:

- **DragDropContext**: Contexto que gerencia o estado de drag & drop
- **Droppable**: Área onde os itens podem ser soltos
- **Draggable**: Item que pode ser arrastado

## Fluxo de Uso

1. O usuário acessa a página de edição de membros da equipe
2. O sistema carrega os dados da equipe e exibe os membros atuais
3. O usuário pode arrastar e soltar os agentes para reordená-los
4. O usuário pode alterar o papel de cada agente
5. O usuário pode visualizar a ordem de execução no preview
6. O usuário salva as alterações
7. O sistema atualiza a equipe e exibe uma mensagem de sucesso

## Próximos Passos

1. **Implementar Visualizador de Fluxo** (T031)
   - Componente com React Flow ou similar
   - Visualização de agentes e conexões
   - Indicadores de status em tempo real

2. **Implementar Editor Visual de Fluxo** (T032)
   - Arrastar e conectar agentes
   - Edição de propriedades inline
   - Validação visual de dependências