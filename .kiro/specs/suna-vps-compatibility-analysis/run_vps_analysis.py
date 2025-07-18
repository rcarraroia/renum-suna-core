#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script principal para executar a análise de compatibilidade Suna VPS.
Este script executa todos os scripts de análise e gera um relatório final consolidado.
"""

import os
import sys
import subprocess
import argparse
import datetime
from pathlib import Path

def parse_arguments():
    """Analisa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Executa análise de compatibilidade Suna VPS")
    parser.add_argument("--remote", action="store_true", help="Executar análise remotamente na VPS")
    parser.add_argument("--host", default="157.180.39.41", help="Endereço IP ou hostname da VPS")
    parser.add_argument("--user", default="root", help="Usuário SSH para conexão")
    parser.add_argument("--key", default="~/.ssh/id_rsa", help="Caminho para a chave SSH")
    return parser.parse_args()

def run_command(command: str) -> bool:
    """
    Executa um comando shell e retorna se foi bem-sucedido.
    
    Args:
        command: Comando a ser executado
        
    Returns:
        True se o comando foi executado com sucesso, False caso contrário
    """
    print(f"Executando: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True
        )
        print(f"✅ Comando executado com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando: {e}")
        return False

def run_local_analysis():
    """Executa a análise localmente."""
    print("Executando análise localmente...")
    
    # Diretório base dos scripts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, "scripts")
    
    # Executar script de compilação do relatório final
    compile_script = os.path.join(scripts_dir, "compile_final_report.py")
    
    if os.path.exists(compile_script):
        return run_command(f"{sys.executable} {compile_script}")
    else:
        print(f"❌ Script não encontrado: {compile_script}")
        return False

def run_remote_analysis(host: str, user: str, key_path: str):
    """
    Executa a análise remotamente na VPS.
    
    Args:
        host: Endereço IP ou hostname da VPS
        user: Usuário SSH para conexão
        key_path: Caminho para a chave SSH
        
    Returns:
        True se a análise foi executada com sucesso, False caso contrário
    """
    print(f"Executando análise remotamente na VPS {host}...")
    
    # Diretório base dos scripts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, "scripts")
    
    # Executar script de análise remota
    remote_script = os.path.join(scripts_dir, "run_vps_env_analysis.py")
    
    if os.path.exists(remote_script):
        return run_command(f"{sys.executable} {remote_script} --host {host} --user {user} --key {key_path}")
    else:
        print(f"❌ Script não encontrado: {remote_script}")
        return False

def main():
    """Função principal do script."""
    args = parse_arguments()
    
    print(f"{'='*80}")
    print(f"Análise de Compatibilidade Suna VPS")
    print(f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    if args.remote:
        success = run_remote_analysis(args.host, args.user, args.key)
    else:
        success = run_local_analysis()
    
    if success:
        print("\n✅ Análise concluída com sucesso!")
        
        # Diretório para relatórios
        base_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(base_dir, "reports")
        final_report = os.path.join(reports_dir, "final_report.md")
        
        if os.path.exists(final_report):
            print(f"Relatório final disponível em: {final_report}")
        else:
            print(f"Relatórios disponíveis em: {reports_dir}")
    else:
        print("\n❌ Análise concluída com erros.")
        print("Verifique os logs para mais detalhes.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())