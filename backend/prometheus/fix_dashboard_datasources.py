#!/usr/bin/env python3
"""
Script para corrigir referências de datasource nos dashboards do Grafana
"""

import json
import os
from pathlib import Path

def fix_datasource_references(dashboard_data):
    """Corrige as referências de datasource no dashboard"""
    def fix_datasource_in_object(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'datasource' and isinstance(value, dict):
                    if value.get('type') == 'prometheus' and value.get('uid') == 'prometheus':
                        value['uid'] = 'prometheus-uid'
                        print(f"  ✅ Corrigido datasource: {value}")
                elif isinstance(value, (dict, list)):
                    fix_datasource_in_object(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_datasource_in_object(item)
    
    fix_datasource_in_object(dashboard_data)
    return dashboard_data

def main():
    """Função principal"""
    print("🔧 Corrigindo referências de datasource nos dashboards")
    print("=" * 60)
    
    # Diretório dos dashboards
    dashboards_dir = Path(__file__).parent / 'grafana' / 'dashboards'
    
    if not dashboards_dir.exists():
        print(f"❌ Diretório não encontrado: {dashboards_dir}")
        return 1
    
    # Encontrar dashboards JSON
    dashboard_files = list(dashboards_dir.glob('*.json'))
    
    if not dashboard_files:
        print(f"❌ Nenhum dashboard encontrado em {dashboards_dir}")
        return 1
    
    print(f"📊 Encontrados {len(dashboard_files)} dashboards para corrigir\n")
    
    fixed_count = 0
    
    for dashboard_file in dashboard_files:
        print(f"🔍 Processando: {dashboard_file.name}")
        
        try:
            # Ler dashboard
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                dashboard_data = json.load(f)
            
            # Fazer backup
            backup_file = dashboard_file.with_suffix('.json.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2)
            print(f"  💾 Backup criado: {backup_file.name}")
            
            # Corrigir referências
            original_data = json.dumps(dashboard_data)
            fixed_data = fix_datasource_references(dashboard_data)
            
            # Verificar se houve mudanças
            if json.dumps(fixed_data) != original_data:
                # Salvar dashboard corrigido
                with open(dashboard_file, 'w', encoding='utf-8') as f:
                    json.dump(fixed_data, f, indent=2)
                
                print(f"  ✅ Dashboard corrigido e salvo")
                fixed_count += 1
            else:
                print(f"  ℹ️  Nenhuma correção necessária")
                # Remover backup desnecessário
                backup_file.unlink()
            
        except json.JSONDecodeError as e:
            print(f"  ❌ Erro de JSON: {e}")
        except Exception as e:
            print(f"  ❌ Erro: {e}")
        
        print()
    
    print("📊 RESULTADO FINAL")
    print("=" * 30)
    print(f"Dashboards corrigidos: {fixed_count}/{len(dashboard_files)}")
    
    if fixed_count > 0:
        print(f"✅ {fixed_count} dashboards foram corrigidos com sucesso!")
        print("💡 Backups foram criados com extensão .backup")
    else:
        print("ℹ️  Nenhum dashboard precisou de correção")
    
    return 0

if __name__ == '__main__':
    exit(main())