"""
Gerenciador de contexto compartilhado para equipes de agentes.

Este módulo fornece funcionalidades para gerenciar o contexto compartilhado entre
agentes de uma equipe, incluindo armazenamento, versionamento e notificações de mudanças.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime
from uuid import UUID

from app.models.team_models import TeamContext, ContextChange

logger = logging.getLogger(__name__)


class TeamContextManager:
    """Gerenciador de contexto compartilhado para equipes de agentes."""
    
    def __init__(self, redis_client, db_client=None):
        """
        Inicializa o gerenciador de contexto.
        
        Args:
            redis_client: Cliente Redis para armazenamento em memória
            db_client: Cliente de banco de dados para persistência (opcional)
        """
        self.redis = redis_client
        self.db = db_client
        self.context_key_prefix = "team_context:"
        self.context_changes_channel = "team_context_changes:"
        self.snapshot_interval = 10  # Número de alterações antes de criar um snapshot
    
    async def create_context(self, execution_id: str, initial_data: Optional[Dict[str, Any]] = None) -> TeamContext:
        """
        Cria um novo contexto para uma execução de equipe.
        
        Args:
            execution_id: ID da execução
            initial_data: Dados iniciais para o contexto
            
        Returns:
            Objeto TeamContext criado
        """
        context_key = f"{self.context_key_prefix}{execution_id}"
        
        # Cria o contexto com dados iniciais
        context = TeamContext(
            execution_id=execution_id,
            variables=initial_data or {},
            metadata={
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": 1
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1
        )
        
        # Armazena no Redis
        await self.redis.hset(
            context_key,
            mapping={
                "variables": json.dumps(context.variables),
                "metadata": json.dumps(context.metadata),
                "version": context.version
            }
        )
        
        # Define TTL (24 horas)
        await self.redis.expire(context_key, 86400)
        
        logger.info(f"Created new context for execution {execution_id}")
        
        # Se tiver DB client, cria snapshot inicial
        if self.db:
            await self._create_snapshot(execution_id, context.variables, context.version)
        
        return context
    
    async def get_context(self, execution_id: str) -> TeamContext:
        """
        Obtém o contexto atual de uma execução.
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Objeto TeamContext atual
            
        Raises:
            ValueError: Se o contexto não existir
        """
        context_key = f"{self.context_key_prefix}{execution_id}"
        
        # Verifica se o contexto existe
        if not await self.redis.exists(context_key):
            raise ValueError(f"Context for execution {execution_id} not found")
        
        # Obtém dados do Redis
        variables = await self.redis.hget(context_key, "variables")
        metadata = await self.redis.hget(context_key, "metadata")
        version = int(await self.redis.hget(context_key, "version") or 1)
        
        # Converte de JSON
        variables_dict = json.loads(variables) if variables else {}
        metadata_dict = json.loads(metadata) if metadata else {}
        
        # Cria objeto TeamContext
        return TeamContext(
            execution_id=execution_id,
            variables=variables_dict,
            metadata=metadata_dict,
            created_at=datetime.fromisoformat(metadata_dict.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(metadata_dict.get("updated_at", datetime.now().isoformat())),
            version=version
        )
    
    async def set_variable(
        self, 
        execution_id: str, 
        key: str, 
        value: Any, 
        agent_id: str,
        ttl: Optional[int] = None
    ) -> None:
        """
        Define uma variável no contexto compartilhado.
        
        Args:
            execution_id: ID da execução
            key: Chave da variável
            value: Valor da variável
            agent_id: ID do agente que está definindo a variável
            ttl: Tempo de vida da variável em segundos (opcional)
        """
        context_key = f"{self.context_key_prefix}{execution_id}"
        
        # Verifica se o contexto existe
        if not await self.redis.exists(context_key):
            raise ValueError(f"Context for execution {execution_id} not found")
        
        # Obtém o contexto atual
        context = await self.get_context(execution_id)
        
        # Obtém o valor anterior (se existir)
        previous_value = context.variables.get(key)
        
        # Atualiza a variável
        context.variables[key] = value
        context.version += 1
        context.updated_at = datetime.now()
        context.metadata["updated_at"] = context.updated_at.isoformat()
        context.metadata["version"] = context.version
        context.metadata["last_updated_by"] = agent_id
        
        # Atualiza no Redis
        await self.redis.hset(
            context_key,
            mapping={
                "variables": json.dumps(context.variables),
                "metadata": json.dumps(context.metadata),
                "version": context.version
            }
        )
        
        # Se TTL for especificado, define para a variável específica
        if ttl:
            variable_key = f"{context_key}:var:{key}"
            await self.redis.set(variable_key, json.dumps(value), ex=ttl)
        
        # Publica mudança no canal
        change = ContextChange(
            key=key,
            value=value,
            previous_value=previous_value,
            changed_by=agent_id,
            timestamp=datetime.now()
        )
        
        await self.redis.publish(
            f"{self.context_changes_channel}{execution_id}",
            json.dumps(change.dict())
        )
        
        logger.debug(f"Set variable {key} in context {execution_id} by agent {agent_id}")
        
        # Verifica se deve criar snapshot
        if context.version % self.snapshot_interval == 0 and self.db:
            await self._create_snapshot(execution_id, context.variables, context.version, agent_id)
    
    async def get_variable(self, execution_id: str, key: str) -> Any:
        """
        Obtém uma variável do contexto compartilhado.
        
        Args:
            execution_id: ID da execução
            key: Chave da variável
            
        Returns:
            Valor da variável ou None se não existir
        """
        context_key = f"{self.context_key_prefix}{execution_id}"
        
        # Verifica se existe uma variável com TTL específico
        variable_key = f"{context_key}:var:{key}"
        if await self.redis.exists(variable_key):
            value_json = await self.redis.get(variable_key)
            return json.loads(value_json)
        
        # Caso contrário, obtém do contexto geral
        context = await self.get_context(execution_id)
        return context.variables.get(key)
    
    async def get_all_variables(self, execution_id: str) -> Dict[str, Any]:
        """
        Obtém todas as variáveis do contexto compartilhado.
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Dicionário com todas as variáveis
        """
        context = await self.get_context(execution_id)
        
        # Obtém variáveis com TTL específico
        context_key = f"{self.context_key_prefix}{execution_id}"
        ttl_keys = await self.redis.keys(f"{context_key}:var:*")
        
        # Cria uma cópia das variáveis do contexto
        variables = context.variables.copy()
        
        # Adiciona variáveis com TTL
        for key in ttl_keys:
            var_name = key.split(":")[-1]
            value_json = await self.redis.get(key)
            variables[var_name] = json.loads(value_json)
        
        return variables
    
    async def delete_variable(self, execution_id: str, key: str, agent_id: str) -> None:
        """
        Remove uma variável do contexto compartilhado.
        
        Args:
            execution_id: ID da execução
            key: Chave da variável
            agent_id: ID do agente que está removendo a variável
        """
        context_key = f"{self.context_key_prefix}{execution_id}"
        variable_key = f"{context_key}:var:{key}"
        
        # Remove variável com TTL específico, se existir
        if await self.redis.exists(variable_key):
            await self.redis.delete(variable_key)
        
        # Obtém o contexto atual
        context = await self.get_context(execution_id)
        
        # Verifica se a variável existe no contexto geral
        if key not in context.variables:
            return
        
        # Obtém o valor anterior
        previous_value = context.variables.get(key)
        
        # Remove a variável
        del context.variables[key]
        context.version += 1
        context.updated_at = datetime.now()
        context.metadata["updated_at"] = context.updated_at.isoformat()
        context.metadata["version"] = context.version
        context.metadata["last_updated_by"] = agent_id
        
        # Atualiza no Redis
        await self.redis.hset(
            context_key,
            mapping={
                "variables": json.dumps(context.variables),
                "metadata": json.dumps(context.metadata),
                "version": context.version
            }
        )
        
        # Publica mudança no canal
        change = ContextChange(
            key=key,
            value=None,
            previous_value=previous_value,
            changed_by=agent_id,
            timestamp=datetime.now()
        )
        
        await self.redis.publish(
            f"{self.context_changes_channel}{execution_id}",
            json.dumps(change.dict())
        )
        
        logger.debug(f"Deleted variable {key} from context {execution_id} by agent {agent_id}")
    
    async def update_context(self, execution_id: str, updates: Dict[str, Any], agent_id: str) -> None:
        """
        Atualiza múltiplas variáveis no contexto de uma vez.
        
        Args:
            execution_id: ID da execução
            updates: Dicionário com as atualizações (chave -> valor)
            agent_id: ID do agente que está atualizando o contexto
        """
        context_key = f"{self.context_key_prefix}{execution_id}"
        
        # Verifica se o contexto existe
        if not await self.redis.exists(context_key):
            raise ValueError(f"Context for execution {execution_id} not found")
        
        # Obtém o contexto atual
        context = await self.get_context(execution_id)
        
        # Armazena valores anteriores para notificações
        previous_values = {}
        for key in updates:
            previous_values[key] = context.variables.get(key)
        
        # Atualiza as variáveis
        context.variables.update(updates)
        context.version += 1
        context.updated_at = datetime.now()
        context.metadata["updated_at"] = context.updated_at.isoformat()
        context.metadata["version"] = context.version
        context.metadata["last_updated_by"] = agent_id
        
        # Atualiza no Redis usando pipeline para eficiência
        pipeline = self.redis.pipeline()
        
        # Atualiza o contexto principal
        pipeline.hset(
            context_key,
            mapping={
                "variables": json.dumps(context.variables),
                "metadata": json.dumps(context.metadata),
                "version": context.version
            }
        )
        
        # Publica mudanças no canal
        for key, value in updates.items():
            change = ContextChange(
                key=key,
                value=value,
                previous_value=previous_values.get(key),
                changed_by=agent_id,
                timestamp=datetime.now()
            )
            
            pipeline.publish(
                f"{self.context_changes_channel}{execution_id}",
                json.dumps(change.dict())
            )
        
        # Executa o pipeline
        await pipeline.execute()
        
        logger.debug(f"Updated {len(updates)} variables in context {execution_id} by agent {agent_id}")
        
        # Verifica se deve criar snapshot
        if context.version % self.snapshot_interval == 0 and self.db:
            await self._create_snapshot(execution_id, context.variables, context.version, agent_id)
    
    async def subscribe_to_changes(self, execution_id: str) -> AsyncIterator[ContextChange]:
        """
        Inscreve para receber notificações de mudanças no contexto.
        
        Args:
            execution_id: ID da execução
            
        Yields:
            Objetos ContextChange com as mudanças
        """
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"{self.context_changes_channel}{execution_id}")
        
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    change_dict = json.loads(message['data'])
                    yield ContextChange(**change_dict)
        finally:
            await pubsub.unsubscribe(f"{self.context_changes_channel}{execution_id}")
    
    async def _create_snapshot(
        self, 
        execution_id: str, 
        context_data: Dict[str, Any], 
        version: int,
        agent_id: Optional[str] = None
    ) -> None:
        """
        Cria um snapshot do contexto no banco de dados.
        
        Args:
            execution_id: ID da execução
            context_data: Dados do contexto
            version: Versão do contexto
            agent_id: ID do agente que causou o snapshot
        """
        if not self.db:
            return
        
        try:
            await self.db.table('renum_team_context_snapshots').insert({
                'execution_id': str(execution_id),
                'snapshot_at': datetime.now().isoformat(),
                'context_data': context_data,
                'version': version,
                'created_by_agent': agent_id
            }).execute()
            
            logger.debug(f"Created snapshot for context {execution_id} version {version}")
        except Exception as e:
            logger.error(f"Failed to create context snapshot: {str(e)}")
    
    async def get_context_history(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de snapshots do contexto.
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Lista de snapshots em ordem cronológica
        """
        if not self.db:
            return []
        
        try:
            result = await self.db.table('renum_team_context_snapshots') \
                .select('*') \
                .eq('execution_id', str(execution_id)) \
                .order('snapshot_at') \
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Failed to get context history: {str(e)}")
            return []
    
    async def restore_context_from_snapshot(self, execution_id: str, snapshot_at: datetime) -> bool:
        """
        Restaura o contexto a partir de um snapshot.
        
        Args:
            execution_id: ID da execução
            snapshot_at: Data/hora do snapshot
            
        Returns:
            True se a restauração foi bem-sucedida
        """
        if not self.db:
            return False
        
        try:
            # Obtém o snapshot
            result = await self.db.table('renum_team_context_snapshots') \
                .select('*') \
                .eq('execution_id', str(execution_id)) \
                .eq('snapshot_at', snapshot_at.isoformat()) \
                .execute()
            
            if not result.data:
                return False
            
            snapshot = result.data[0]
            
            # Restaura o contexto no Redis
            context_key = f"{self.context_key_prefix}{execution_id}"
            
            metadata = {
                "created_at": snapshot['snapshot_at'],
                "updated_at": datetime.now().isoformat(),
                "version": snapshot['version'],
                "restored_from": snapshot['snapshot_at'],
                "restored_at": datetime.now().isoformat()
            }
            
            await self.redis.hset(
                context_key,
                mapping={
                    "variables": json.dumps(snapshot['context_data']),
                    "metadata": json.dumps(metadata),
                    "version": snapshot['version']
                }
            )
            
            logger.info(f"Restored context {execution_id} from snapshot at {snapshot_at}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore context from snapshot: {str(e)}")
            return False
    
    async def add_message_to_context(
        self, 
        thread_id: str, 
        type: str, 
        content: Any, 
        **kwargs
    ) -> None:
        """
        Adiciona uma mensagem ao contexto compartilhado.
        
        Este método é usado para integração com o ThreadManager do Suna Core.
        
        Args:
            thread_id: ID da thread
            type: Tipo da mensagem
            content: Conteúdo da mensagem
            **kwargs: Argumentos adicionais
        """
        # Obtém execution_id a partir de kwargs ou metadata
        execution_id = kwargs.get('execution_id')
        if not execution_id:
            metadata = kwargs.get('metadata', {})
            execution_id = metadata.get('execution_id')
        
        if not execution_id:
            # Não está associado a uma execução de equipe
            return
        
        # Obtém agent_id
        agent_id = kwargs.get('agent_id')
        if not agent_id:
            metadata = kwargs.get('metadata', {})
            agent_id = metadata.get('agent_id', 'unknown')
        
        # Adiciona a mensagem ao contexto
        try:
            context = await self.get_context(execution_id)
            
            # Adiciona à lista de mensagens no contexto
            messages = context.variables.get('messages', [])
            
            # Formata a mensagem
            message = {
                'type': type,
                'content': content,
                'agent_id': agent_id,
                'timestamp': datetime.now().isoformat()
            }
            
            messages.append(message)
            
            # Atualiza o contexto
            await self.set_variable(execution_id, 'messages', messages, agent_id)
            
            # Se for uma mensagem de ferramenta, adiciona ao histórico de ferramentas
            if type == 'tool_call' or type == 'tool':
                tool_history = context.variables.get('tool_history', [])
                tool_history.append(message)
                await self.set_variable(execution_id, 'tool_history', tool_history, agent_id)
            
        except ValueError:
            # Contexto não existe, ignora
            pass
        except Exception as e:
            logger.error(f"Failed to add message to context: {str(e)}")
    
    async def batch_update_context(self, updates: List[Dict[str, Any]]) -> None:
        """
        Atualiza múltiplos contextos em lote.
        
        Args:
            updates: Lista de atualizações, cada uma com execution_id, key, value, agent_id
        """
        pipeline = self.redis.pipeline()
        
        for update in updates:
            execution_id = update['execution_id']
            key = update['key']
            value = update['value']
            agent_id = update['agent_id']
            
            context_key = f"{self.context_key_prefix}{execution_id}"
            
            # Obtém o contexto atual (não podemos usar pipeline para isso)
            try:
                context = await self.get_context(execution_id)
                
                # Atualiza a variável
                context.variables[key] = value
                context.version += 1
                context.updated_at = datetime.now()
                context.metadata["updated_at"] = context.updated_at.isoformat()
                context.metadata["version"] = context.version
                context.metadata["last_updated_by"] = agent_id
                
                # Adiciona ao pipeline
                pipeline.hset(
                    context_key,
                    mapping={
                        "variables": json.dumps(context.variables),
                        "metadata": json.dumps(context.metadata),
                        "version": context.version
                    }
                )
                
                # Publica mudança no canal
                change = ContextChange(
                    key=key,
                    value=value,
                    previous_value=context.variables.get(key),
                    changed_by=agent_id,
                    timestamp=datetime.now()
                )
                
                pipeline.publish(
                    f"{self.context_changes_channel}{execution_id}",
                    json.dumps(change.dict())
                )
                
            except ValueError:
                # Contexto não existe, ignora
                continue
        
        # Executa o pipeline
        await pipeline.execute()
        
        logger.debug(f"Batch updated {len(updates)} context variables")