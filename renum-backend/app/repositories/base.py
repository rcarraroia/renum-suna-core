"""
Módulo que define as interfaces base para os repositórios da Plataforma Renum.

Este módulo implementa o padrão Repository para abstrair o acesso ao banco de dados,
fornecendo uma interface consistente para operações CRUD.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Dict, Any, Optional, Union

# Tipo genérico para entidades
T = TypeVar('T')

class Repository(Generic[T], ABC):
    """Interface base para repositórios."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Recupera uma entidade pelo ID.
        
        Args:
            id: Identificador único da entidade.
            
        Returns:
            A entidade encontrada ou None se não existir.
        """
        pass
    
    @abstractmethod
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        limit: int = 100, 
        offset: int = 0,
        order_by: Optional[str] = None
    ) -> List[T]:
        """Lista entidades com filtros opcionais.
        
        Args:
            filters: Dicionário de filtros a serem aplicados.
            limit: Número máximo de entidades a serem retornadas.
            offset: Número de entidades a serem puladas.
            order_by: Campo para ordenação dos resultados.
            
        Returns:
            Lista de entidades que correspondem aos filtros.
        """
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Cria uma nova entidade.
        
        Args:
            entity: Entidade a ser criada.
            
        Returns:
            A entidade criada com ID atribuído.
        """
        pass
    
    @abstractmethod
    async def update(self, id: str, entity: T) -> T:
        """Atualiza uma entidade existente.
        
        Args:
            id: Identificador único da entidade.
            entity: Entidade com dados atualizados.
            
        Returns:
            A entidade atualizada.
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Exclui uma entidade pelo ID.
        
        Args:
            id: Identificador único da entidade.
            
        Returns:
            True se a entidade foi excluída com sucesso, False caso contrário.
        """
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """Verifica se uma entidade existe pelo ID.
        
        Args:
            id: Identificador único da entidade.
            
        Returns:
            True se a entidade existe, False caso contrário.
        """
        pass


class SupabaseRepository(Repository[T], ABC):
    """Implementação base de repositório usando Supabase."""
    
    def __init__(self, supabase_client, table_name: str):
        """Inicializa o repositório.
        
        Args:
            supabase_client: Cliente Supabase para acesso ao banco de dados.
            table_name: Nome da tabela no Supabase.
        """
        self.supabase = supabase_client
        self.table_name = table_name
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Recupera uma entidade pelo ID.
        
        Args:
            id: Identificador único da entidade.
            
        Returns:
            A entidade encontrada ou None se não existir.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("id", id).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        return None
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        limit: int = 100, 
        offset: int = 0,
        order_by: Optional[str] = None
    ) -> List[T]:
        """Lista entidades com filtros opcionais.
        
        Args:
            filters: Dicionário de filtros a serem aplicados.
            limit: Número máximo de entidades a serem retornadas.
            offset: Número de entidades a serem puladas.
            order_by: Campo para ordenação dos resultados.
            
        Returns:
            Lista de entidades que correspondem aos filtros.
        """
        query = self.supabase.from_(self.table_name).select("*").limit(limit).offset(offset)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        if order_by:
            query = query.order(order_by)
        
        result = await query.execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def create(self, entity: T) -> T:
        """Cria uma nova entidade.
        
        Args:
            entity: Entidade a ser criada.
            
        Returns:
            A entidade criada com ID atribuído.
        """
        data = self._map_to_dict(entity)
        result = await self.supabase.from_(self.table_name).insert(data).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao criar entidade na tabela {self.table_name}")
    
    async def update(self, id: str, entity: T) -> T:
        """Atualiza uma entidade existente.
        
        Args:
            id: Identificador único da entidade.
            entity: Entidade com dados atualizados.
            
        Returns:
            A entidade atualizada.
        """
        data = self._map_to_dict(entity)
        # Remover o ID do dicionário para evitar tentativa de atualização
        if "id" in data:
            del data["id"]
            
        result = await self.supabase.from_(self.table_name).update(data).eq("id", id).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao atualizar entidade com ID {id} na tabela {self.table_name}")
    
    async def delete(self, id: str) -> bool:
        """Exclui uma entidade pelo ID.
        
        Args:
            id: Identificador único da entidade.
            
        Returns:
            True se a entidade foi excluída com sucesso, False caso contrário.
        """
        result = await self.supabase.from_(self.table_name).delete().eq("id", id).execute()
        return result.data is not None and len(result.data) > 0
    
    async def exists(self, id: str) -> bool:
        """Verifica se uma entidade existe pelo ID.
        
        Args:
            id: Identificador único da entidade.
            
        Returns:
            True se a entidade existe, False caso contrário.
        """
        result = await self.supabase.from_(self.table_name).select("id").eq("id", id).execute()
        return result.data is not None and len(result.data) > 0
    
    @abstractmethod
    def _map_to_entity(self, data: Dict[str, Any]) -> T:
        """Converte um dicionário de dados em uma entidade.
        
        Args:
            data: Dicionário com os dados da entidade.
            
        Returns:
            A entidade correspondente aos dados.
        """
        pass
    
    @abstractmethod
    def _map_to_dict(self, entity: T) -> Dict[str, Any]:
        """Converte uma entidade em um dicionário de dados.
        
        Args:
            entity: Entidade a ser convertida.
            
        Returns:
            Dicionário com os dados da entidade.
        """
        pass


class PaginatedResult(Generic[T]):
    """Resultado paginado para consultas que retornam muitos registros."""
    
    def __init__(self, items: List[T], total: int, page: int, page_size: int):
        """Inicializa o resultado paginado.
        
        Args:
            items: Lista de itens na página atual.
            total: Número total de itens em todas as páginas.
            page: Número da página atual (começando em 1).
            page_size: Tamanho da página.
        """
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.pages = (total + page_size - 1) // page_size if total > 0 else 0
        self.has_next = page < self.pages
        self.has_prev = page > 1