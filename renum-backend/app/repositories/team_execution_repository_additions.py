"""
Adições ao repositório de execuções de equipes.

Este arquivo contém métodos adicionais para o repositório de execuções de equipes,
que serão adicionados à classe TeamExecutionRepository.
"""

async def count_active_executions(self, user_id: UUID) -> int:
    """
    Conta o número de execuções ativas do usuário.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Número de execuções ativas
    """
    try:
        # Constrói a query
        query = self.db.table('renum_team_executions') \
            .select('*', count='exact') \
            .eq('user_id', str(user_id)) \
            .in_('status', ['pending', 'running'])
        
        # Executa a query
        result = await query.execute()
        
        return result.count
        
    except Exception as e:
        logger.error(f"Failed to count active executions: {str(e)}")
        return 0

async def list_executions_by_date(
    self, 
    user_id: UUID, 
    start_date: str,
    end_date: Optional[str] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Lista execuções do usuário em um período específico.
    
    Args:
        user_id: ID do usuário
        start_date: Data de início (formato ISO)
        end_date: Data de fim (formato ISO, opcional)
        limit: Limite de resultados
        
    Returns:
        Lista de execuções
    """
    try:
        # Constrói a query
        query = self.db.table('renum_team_executions') \
            .select('*') \
            .eq('user_id', str(user_id)) \
            .gte('created_at', start_date)
        
        # Adiciona filtro de data final se fornecido
        if end_date:
            query = query.lte('created_at', end_date)
        
        # Aplica ordenação e limite
        query = query.order('created_at', desc=True) \
            .limit(limit)
        
        # Executa a query
        result = await query.execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Failed to list executions by date: {str(e)}")
        return []

async def register_usage(
    self,
    execution_id: UUID,
    agent_id: str,
    usage_metrics: Dict[str, Any],
    cost_metrics: Dict[str, Any]
) -> bool:
    """
    Registra métricas de uso e custo no banco de dados.
    
    Args:
        execution_id: ID da execução
        agent_id: ID do agente
        usage_metrics: Métricas de uso
        cost_metrics: Métricas de custo
        
    Returns:
        True se o registro foi bem-sucedido
    """
    try:
        # Obtém a execução para obter o user_id
        execution = await self.db.table('renum_team_executions') \
            .select('user_id') \
            .eq('execution_id', str(execution_id)) \
            .execute()
        
        if not execution.data:
            logger.error(f"Execution {execution_id} not found")
            return False
        
        user_id = execution.data[0]['user_id']
        
        # Prepara os dados para inserção
        usage_log = {
            'user_id': user_id,
            'execution_id': str(execution_id),
            'agent_id': agent_id,
            'model_provider': usage_metrics.get('model_provider'),
            'model_name': usage_metrics.get('model_name'),
            'api_key_type': usage_metrics.get('api_key_type'),
            'tokens_input': usage_metrics.get('tokens_input', 0),
            'tokens_output': usage_metrics.get('tokens_output', 0),
            'cost_usd': cost_metrics.get('cost_usd', 0),
            'created_at': datetime.now().isoformat()
        }
        
        # Insere no banco de dados
        await self.db.table('renum_ai_usage_logs').insert(usage_log).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to register usage: {str(e)}")
        return False