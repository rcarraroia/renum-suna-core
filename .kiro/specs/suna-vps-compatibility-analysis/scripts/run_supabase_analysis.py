#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para executar a análise completa da integração com Supabase via VPS.
Este script executa os testes de conexão com o Supabase e verificação das funções vetoriais.
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

def create_consolidated_report(reports_dir: str) -> str:
    """
    Cria um relatório consolidado a partir dos relatórios individuais.
    
    Args:
        reports_dir: Diretório com os relatórios
        
    Returns:
        Caminho para o relatório consolidado
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Caminho para o relatório consolidado
    consolidated_path = os.path.join(reports_dir, "supabase_analysis_consolidated.md")
    
    # Encontrar relatórios relacionados ao Supabase
    report_files = [
        f for f in os.listdir(reports_dir) 
        if f.endswith(".md") and ("supabase" in f.lower() or "vector" in f.lower())
    ]
    
    with open(consolidated_path, "w", encoding="utf-8") as out_file:
        # Cabeçalho
        out_file.write(f"# Relatório Consolidado de Análise de Integração com Supabase\n\n")
        out_file.write(f"Data: {now}\n\n")
        out_file.write("Este relatório consolida os resultados da análise de integração com Supabase,\n")
        out_file.write("incluindo testes de conexão e verificação de funções vetoriais.\n\n")
        
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
        
        # Conclusão
        out_file.write("## Conclusão\n\n")
        out_file.write("Esta análise identificou o estado atual da integração com Supabase na VPS.\n")
        out_file.write("Recomenda-se revisar os problemas identificados e implementar as correções\n")
        out_file.write("sugeridas para garantir o funcionamento adequado da integração.\n\n")
    
    return consolidated_path

def main():
    """Função principal do script."""
    # Diretório base dos scripts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Diretório para relatórios
    reports_dir = os.path.join(os.path.dirname(base_dir), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Lista de scripts a serem executados
    scripts = [
        os.path.join(base_dir, "test_supabase_connection.py"),
        os.path.join(base_dir, "check_vector_functions.py")
    ]
    
    # Executar cada script
    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"Resumo da execução: {success_count}/{len(scripts)} scripts executados com sucesso")
    print(f"{'='*80}\n")
    
    # Criar relatório consolidado
    if success_count > 0:
        consolidated_report = create_consolidated_report(reports_dir)
        print(f"Relatório consolidado criado em: {consolidated_report}")
    else:
        print("Nenhum relatório foi gerado com sucesso.")

if __name__ == "__main__":
    main()