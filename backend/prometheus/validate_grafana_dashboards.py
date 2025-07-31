#!/usr/bin/env python3
"""
Script para validar dashboards do Grafana
Verifica se os dashboards estão bem formados e contêm as métricas necessárias
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

def validate_json_file(file_path: Path) -> Dict[str, Any]:
    """Valida se um arquivo JSON está bem formado"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Erro de JSON em {file_path}: {e}")
        return {}
    except Exception as e:
        print(f"❌ Erro ao ler {file_path}: {e}")
        return {}

def validate_dashboard_structure(dashboard: Dict[str, Any], file_name: str) -> bool:
    """Valida a estrutura básica de um dashboard"""
    required_fields = ['title', 'panels', 'time', 'timepicker']
    missing_fields = []
    
    for field in required_fields:
        if field not in dashboard:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ {file_name}: Campos obrigatórios ausentes: {missing_fields}")
        return False
    
    return True

def validate_panels(panels: List[Dict[str, Any]], file_name: str) -> bool:
    """Valida os painéis do dashboard"""
    if not panels:
        print(f"❌ {file_name}: Dashboard sem painéis")
        return False
    
    valid_panels = 0
    total_panels = len(panels)
    
    for i, panel in enumerate(panels):
        panel_valid = True
        
        # Verificar campos obrigatórios do painel
        required_panel_fields = ['id', 'title', 'type']
        for field in required_panel_fields:
            if field not in panel:
                print(f"⚠️  {file_name}: Painel {i+1} sem campo '{field}'")
                panel_valid = False
        
        # Verificar se tem targets (queries)
        if 'targets' in panel and panel['targets']:
            for j, target in enumerate(panel['targets']):
                if 'expr' not in target and 'query' not in target:
                    print(f"⚠️  {file_name}: Painel {i+1}, target {j+1} sem query")
                    panel_valid = False
        else:
            # Alguns tipos de painel não precisam de targets (text, etc.)
            if panel.get('type') not in ['text', 'dashlist', 'row']:
                print(f"⚠️  {file_name}: Painel {i+1} sem targets/queries")
                panel_valid = False
        
        if panel_valid:
            valid_panels += 1
    
    print(f"📊 {file_name}: {valid_panels}/{total_panels} painéis válidos")
    return valid_panels > 0

def check_prometheus_queries(dashboard: Dict[str, Any], file_name: str) -> List[str]:
    """Extrai e valida queries do Prometheus"""
    queries = []
    
    if 'panels' not in dashboard:
        return queries
    
    for panel in dashboard['panels']:
        if 'targets' in panel:
            for target in panel['targets']:
                if 'expr' in target and target['expr']:
                    queries.append(target['expr'])
                elif 'query' in target and target['query']:
                    queries.append(target['query'])
    
    print(f"🔍 {file_name}: {len(queries)} queries encontradas")
    return queries

def validate_datasource_references(dashboard: Dict[str, Any], file_name: str) -> bool:
    """Valida se as referências de datasource estão corretas"""
    expected_datasource_uid = 'prometheus-uid'
    valid_references = 0
    total_references = 0
    
    if 'panels' not in dashboard:
        return True
    
    for panel in dashboard['panels']:
        # Verificar datasource no painel
        if 'datasource' in panel:
            total_references += 1
            if isinstance(panel['datasource'], dict):
                if panel['datasource'].get('uid') == expected_datasource_uid:
                    valid_references += 1
            elif panel['datasource'] == expected_datasource_uid:
                valid_references += 1
        
        # Verificar datasource nos targets
        if 'targets' in panel:
            for target in panel['targets']:
                if 'datasource' in target:
                    total_references += 1
                    if isinstance(target['datasource'], dict):
                        if target['datasource'].get('uid') == expected_datasource_uid:
                            valid_references += 1
                    elif target['datasource'] == expected_datasource_uid:
                        valid_references += 1
    
    if total_references > 0:
        print(f"🔗 {file_name}: {valid_references}/{total_references} referências de datasource válidas")
        return valid_references == total_references
    
    return True

def analyze_dashboard_metrics(queries: List[str], file_name: str) -> Dict[str, int]:
    """Analisa os tipos de métricas usadas no dashboard"""
    metrics_count = {
        'http_requests': 0,
        'database_queries': 0,
        'redis_operations': 0,
        'system_metrics': 0,
        'worker_tasks': 0,
        'agent_executions': 0,
        'llm_requests': 0,
        'websocket_connections': 0
    }
    
    for query in queries:
        query_lower = query.lower()
        
        if 'http_request' in query_lower:
            metrics_count['http_requests'] += 1
        if 'database_query' in query_lower or 'db_' in query_lower:
            metrics_count['database_queries'] += 1
        if 'redis_' in query_lower:
            metrics_count['redis_operations'] += 1
        if 'node_' in query_lower or 'process_' in query_lower:
            metrics_count['system_metrics'] += 1
        if 'worker_task' in query_lower:
            metrics_count['worker_tasks'] += 1
        if 'agent_execution' in query_lower:
            metrics_count['agent_executions'] += 1
        if 'llm_request' in query_lower:
            metrics_count['llm_requests'] += 1
        if 'websocket' in query_lower or 'ws_' in query_lower:
            metrics_count['websocket_connections'] += 1
    
    # Mostrar métricas encontradas
    found_metrics = {k: v for k, v in metrics_count.items() if v > 0}
    if found_metrics:
        print(f"📈 {file_name}: Métricas encontradas: {found_metrics}")
    
    return metrics_count

def main():
    """Função principal"""
    print("🔍 Validando Dashboards do Grafana")
    print("=" * 50)
    
    # Diretório dos dashboards
    dashboards_dir = Path(__file__).parent / 'grafana' / 'dashboards'
    
    if not dashboards_dir.exists():
        print(f"❌ Diretório de dashboards não encontrado: {dashboards_dir}")
        sys.exit(1)
    
    # Encontrar todos os arquivos JSON
    dashboard_files = list(dashboards_dir.glob('*.json'))
    
    if not dashboard_files:
        print(f"❌ Nenhum dashboard encontrado em {dashboards_dir}")
        sys.exit(1)
    
    print(f"📊 Encontrados {len(dashboard_files)} dashboards para validar\n")
    
    # Estatísticas gerais
    total_dashboards = len(dashboard_files)
    valid_dashboards = 0
    total_queries = 0
    all_metrics = {
        'http_requests': 0,
        'database_queries': 0,
        'redis_operations': 0,
        'system_metrics': 0,
        'worker_tasks': 0,
        'agent_executions': 0,
        'llm_requests': 0,
        'websocket_connections': 0
    }
    
    # Validar cada dashboard
    for dashboard_file in dashboard_files:
        print(f"🔍 Validando: {dashboard_file.name}")
        print("-" * 30)
        
        # Carregar e validar JSON
        dashboard = validate_json_file(dashboard_file)
        if not dashboard:
            continue
        
        dashboard_valid = True
        
        # Validar estrutura
        if not validate_dashboard_structure(dashboard, dashboard_file.name):
            dashboard_valid = False
        
        # Validar painéis
        if 'panels' in dashboard:
            if not validate_panels(dashboard['panels'], dashboard_file.name):
                dashboard_valid = False
        
        # Validar referências de datasource
        if not validate_datasource_references(dashboard, dashboard_file.name):
            dashboard_valid = False
        
        # Analisar queries
        queries = check_prometheus_queries(dashboard, dashboard_file.name)
        total_queries += len(queries)
        
        # Analisar métricas
        dashboard_metrics = analyze_dashboard_metrics(queries, dashboard_file.name)
        for metric, count in dashboard_metrics.items():
            all_metrics[metric] += count
        
        if dashboard_valid:
            valid_dashboards += 1
            print(f"✅ {dashboard_file.name}: Dashboard válido")
        else:
            print(f"❌ {dashboard_file.name}: Dashboard com problemas")
        
        print()
    
    # Relatório final
    print("📊 RELATÓRIO FINAL")
    print("=" * 50)
    print(f"Dashboards válidos: {valid_dashboards}/{total_dashboards}")
    print(f"Total de queries: {total_queries}")
    print()
    
    print("📈 Distribuição de Métricas:")
    for metric, count in all_metrics.items():
        if count > 0:
            print(f"  • {metric.replace('_', ' ').title()}: {count} queries")
    
    print()
    
    # Recomendações
    print("💡 RECOMENDAÇÕES:")
    
    if all_metrics['http_requests'] == 0:
        print("⚠️  Considere adicionar métricas de HTTP requests")
    
    if all_metrics['database_queries'] == 0:
        print("⚠️  Considere adicionar métricas de database queries")
    
    if all_metrics['redis_operations'] == 0:
        print("⚠️  Considere adicionar métricas de Redis operations")
    
    if all_metrics['websocket_connections'] == 0:
        print("⚠️  Considere adicionar métricas de WebSocket connections")
    
    if valid_dashboards == total_dashboards:
        print("✅ Todos os dashboards estão válidos!")
        return 0
    else:
        print(f"❌ {total_dashboards - valid_dashboards} dashboards precisam de correção")
        return 1

if __name__ == '__main__':
    sys.exit(main())