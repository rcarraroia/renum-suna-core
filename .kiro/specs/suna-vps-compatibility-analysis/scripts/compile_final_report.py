#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para compilar um relatório final consolidado com os resultados de todas as análises.
Este script executa todos os scripts de análise e gera um relatório final com recomendações.
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

def run_script(script_path: str) -> bool:
    """
    Executa um script Python e retorna se foi bem-sucedido.
    
    Args:
        script_path: Caminho para o script
        
    Returns:
        True se o script foi executado com sucesso, False caso contrário
    """
    print(f"\n{'='*80}")
    print(f"Executando: {os.path.basename(script_path)}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            text=True
        )
        print(f"\n✅ Script {os.path.basename(script_path)} executado com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao executar script {os.path.basename(script_path)}: {e}")
        return False

def create_final_report(reports_dir: str) -> str:
    """
    Cria um relatório final consolidado a partir dos relatórios individuais.
    
    Args:
        reports_dir: Diretório com os relatórios
        
    Returns:
        Caminho para o relatório final
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Caminho para o relatório final
    final_report_path = os.path.join(reports_dir, "final_report.md")
    
    # Encontrar todos os relatórios .md
    report_files = [f for f in os.listdir(reports_dir) if f.endswith(".md") and f != "final_report.md"]
    
    with open(final_report_path, "w", encoding="utf-8") as out_file:
        # Cabeçalho
        out_file.write(f"# Relatório Final de Análise de Compatibilidade Suna VPS\n\n")
        out_file.write(f"Data: {now}\n\n")
        out_file.write("Este relatório consolida os resultados de todas as análises realizadas para verificar\n")
        out_file.write("a compatibilidade entre o ambiente Suna na VPS e o backend Renum.\n\n")
        
        # Sumário executivo
        out_file.write("## Sumário Executivo\n\n")
        out_file.write("A análise de compatibilidade entre o ambiente Suna na VPS e o backend Renum foi realizada\n")
        out_file.write("para identificar possíveis problemas e recomendar soluções. Foram analisados os seguintes aspectos:\n\n")
        out_file.write("1. **Variáveis de ambiente e estrutura de diretórios**\n")
        out_file.write("2. **Conexão entre serviços Renum e Suna**\n")
        out_file.write("3. **Integração com Supabase via VPS**\n")
        out_file.write("4. **Disponibilidade das APIs REST**\n")
        out_file.write("5. **Ajustes necessários para produção**\n\n")
        
        # Índice
        out_file.write("## Índice\n\n")
        for i, report_file in enumerate(report_files, 1):
            name = report_file.replace("_", " ").replace(".md", "").title()
            out_file.write(f"{i}. [{name}](#{name.lower().replace(' ', '-')})\n")
        
        out_file.write("\n---\n\n")
        
        # Conteúdo dos relatórios
        for report_file in report_files:
            report_path = os.path.join(reports_dir, report_file)
            name = report_file.replace("_", " ").replace(".md", "").title()
            
            out_file.write(f"## {name}\n\n")
            
            try:
                with open(report_path, "r", encoding="utf-8") as in_file:
                    # Pular o título original
                    lines = in_file.readlines()
                    if lines and lines[0].startswith("# "):
                        lines = lines[1:]
                    
                    # Ajustar níveis de cabeçalho
                    content = ""
                    for line in lines:
                        if line.startswith("#"):
                            # Adicionar um nível a todos os cabeçalhos
                            line = "#" + line
                        content += line
                    
                    out_file.write(content)
            except Exception as e:
                out_file.write(f"Erro ao ler o relatório {report_file}: {e}\n\n")
            
            out_file.write("\n---\n\n")
        
        # Conclusão e recomendações finais
        out_file.write("## Conclusão e Recomendações Finais\n\n")
        out_file.write("Com base nas análises realizadas, foram identificados os seguintes pontos principais:\n\n")
        
        # Variáveis de ambiente
        out_file.write("### 1. Variáveis de Ambiente\n\n")
        out_file.write("- Garantir que todas as variáveis de ambiente necessárias estejam configuradas\n")
        out_file.write("- Sincronizar variáveis entre arquivos .env e contêineres\n")
        out_file.write("- Documentar todas as variáveis de ambiente utilizadas\n\n")
        
        # Conexão entre serviços
        out_file.write("### 2. Conexão entre Serviços\n\n")
        out_file.write("- Verificar se os serviços estão na mesma rede Docker\n")
        out_file.write("- Garantir que os serviços possam se comunicar por nome de contêiner\n")
        out_file.write("- Configurar corretamente as URLs de comunicação entre serviços\n\n")
        
        # Integração com Supabase
        out_file.write("### 3. Integração com Supabase\n\n")
        out_file.write("- Verificar a configuração SSL para conexão segura\n")
        out_file.write("- Garantir que a extensão pgvector esteja instalada e configurada\n")
        out_file.write("- Testar funções de busca vetorial\n\n")
        
        # APIs REST
        out_file.write("### 4. APIs REST\n\n")
        out_file.write("- Documentar todos os endpoints disponíveis\n")
        out_file.write("- Implementar testes automatizados para os endpoints\n")
        out_file.write("- Garantir que a autenticação e autorização estejam funcionando corretamente\n\n")
        
        # Produção
        out_file.write("### 5. Ajustes para Produção\n\n")
        out_file.write("- Configurar rotação de logs\n")
        out_file.write("- Implementar monitoramento com ferramentas como Sentry e Prometheus\n")
        out_file.write("- Configurar backup e recuperação\n")
        out_file.write("- Verificar configurações de segurança\n\n")
        
        # Próximos passos
        out_file.write("## Próximos Passos\n\n")
        out_file.write("1. **Corrigir problemas críticos** - Priorizar a correção dos problemas que afetam o funcionamento básico\n")
        out_file.write("2. **Implementar melhorias** - Adicionar recursos de monitoramento, logging e backup\n")
        out_file.write("3. **Documentar** - Criar documentação detalhada sobre a configuração e operação do ambiente\n")
        out_file.write("4. **Automatizar** - Implementar scripts de automação para tarefas recorrentes\n")
        out_file.write("5. **Testar** - Realizar testes de carga e estresse para verificar a estabilidade do ambiente\n\n")
        
        out_file.write("Este relatório foi gerado automaticamente como parte da análise de compatibilidade Suna VPS.\n")
    
    return final_report_path

def main():
    """Função principal do script."""
    # Diretório base dos scripts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Diretório para relatórios
    reports_dir = os.path.join(os.path.dirname(base_dir), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Lista de scripts a serem executados
    scripts = [
        # Variáveis de ambiente e estrutura de diretórios
        os.path.join(base_dir, "analyze_environment_variables.py"),
        os.path.join(base_dir, "validate_env_variables.py"),
        os.path.join(base_dir, "compare_env_files.py"),
        
        # Conexão entre serviços
        os.path.join(base_dir, "check_docker_network.py"),
        os.path.join(base_dir, "test_service_communication.py"),
        
        # Integração com Supabase
        os.path.join(base_dir, "test_supabase_connection.py"),
        os.path.join(base_dir, "check_vector_functions.py"),
        
        # APIs REST
        os.path.join(base_dir, "map_available_endpoints.py"),
        os.path.join(base_dir, "test_endpoint_responses.py"),
        
        # Produção
        os.path.join(base_dir, "analyze_logs_monitoring.py")
    ]
    
    # Executar cada script
    success_count = 0
    for script in scripts:
        if os.path.exists(script):
            if run_script(script):
                success_count += 1
        else:
            print(f"❌ Script não encontrado: {script}")
    
    print(f"\n{'='*80}")
    print(f"Resumo da execução: {success_count}/{len(scripts)} scripts executados com sucesso")
    print(f"{'='*80}\n")
    
    # Criar relatório final
    if success_count > 0:
        final_report = create_final_report(reports_dir)
        print(f"Relatório final criado em: {final_report}")
    else:
        print("Nenhum relatório foi gerado com sucesso.")

if __name__ == "__main__":
    main()