#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para executar a análise de variáveis de ambiente diretamente na VPS.
Este script se conecta à VPS via SSH, copia os scripts de análise e os executa remotamente.
"""

import os
import sys
import subprocess
import argparse
import tempfile
import datetime
from pathlib import Path

# Configuração da VPS
VPS_HOST = "157.180.39.41"
VPS_USER = "root"
SSH_KEY_PATH = "~/.ssh/id_rsa"  # Caminho para a chave SSH

def parse_arguments():
    """Analisa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Executa análise de variáveis de ambiente na VPS")
    parser.add_argument("--host", default=VPS_HOST, help="Endereço IP ou hostname da VPS")
    parser.add_argument("--user", default=VPS_USER, help="Usuário SSH para conexão")
    parser.add_argument("--key", default=SSH_KEY_PATH, help="Caminho para a chave SSH")
    parser.add_argument("--remote-dir", default="/tmp/env-analysis", help="Diretório remoto para os scripts")
    return parser.parse_args()

def run_local_command(command):
    """Executa um comando local e retorna a saída."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, f"Erro: {e.stderr}"

def run_ssh_command(host, user, key_path, command):
    """Executa um comando via SSH na VPS."""
    ssh_command = f'ssh -i {key_path} {user}@{host} "{command}"'
    return run_local_command(ssh_command)

def copy_file_to_vps(host, user, key_path, local_path, remote_path):
    """Copia um arquivo para a VPS via SCP."""
    scp_command = f'scp -i {key_path} {local_path} {user}@{host}:{remote_path}'
    stdout, error = run_local_command(scp_command)
    if error:
        print(f"Erro ao copiar arquivo {local_path}: {error}")
        return False
    return True

def copy_directory_from_vps(host, user, key_path, remote_path, local_path):
    """Copia um diretório da VPS via SCP."""
    scp_command = f'scp -r -i {key_path} {user}@{host}:{remote_path} {local_path}'
    stdout, error = run_local_command(scp_command)
    if error:
        print(f"Erro ao copiar diretório {remote_path}: {error}")
        return False
    return True

def main():
    """Função principal do script."""
    args = parse_arguments()
    
    print(f"Iniciando análise de variáveis de ambiente na VPS {args.host}...")
    
    # Verificar conexão SSH
    print("Verificando conexão SSH...")
    stdout, error = run_ssh_command(args.host, args.user, args.key, "echo 'Conexão SSH estabelecida'")
    if error:
        print(f"Erro ao conectar via SSH: {error}")
        return 1
    print(stdout)
    
    # Criar diretório remoto
    print(f"Criando diretório remoto {args.remote_dir}...")
    run_ssh_command(args.host, args.user, args.key, f"mkdir -p {args.remote_dir}/scripts {args.remote_dir}/reports")
    
    # Obter diretório dos scripts locais
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Copiar scripts para a VPS
    print("Copiando scripts para a VPS...")
    scripts = [
        "analyze_environment_variables.py",
        "validate_env_variables.py",
        "compare_env_files.py",
        "run_env_analysis.py"
    ]
    
    for script in scripts:
        local_path = os.path.join(script_dir, script)
        remote_path = f"{args.remote_dir}/scripts/{script}"
        print(f"Copiando {script}...")
        if not copy_file_to_vps(args.host, args.user, args.key, local_path, remote_path):
            print(f"Falha ao copiar {script}. Abortando.")
            return 1
    
    # Dar permissão de execução aos scripts
    print("Configurando permissões dos scripts...")
    run_ssh_command(args.host, args.user, args.key, f"chmod +x {args.remote_dir}/scripts/*.py")
    
    # Executar análise na VPS
    print("Executando análise na VPS...")
    stdout, error = run_ssh_command(
        args.host, 
        args.user, 
        args.key, 
        f"cd {args.remote_dir} && python3 scripts/run_env_analysis.py"
    )
    
    if error:
        print(f"Erro durante a execução da análise: {error}")
    else:
        print("Análise concluída com sucesso!")
        
    # Criar diretório local para relatórios
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    local_reports_dir = os.path.join(os.path.dirname(script_dir), "reports", f"vps_analysis_{timestamp}")
    os.makedirs(local_reports_dir, exist_ok=True)
    
    # Copiar relatórios da VPS
    print(f"Copiando relatórios para {local_reports_dir}...")
    if copy_directory_from_vps(args.host, args.user, args.key, f"{args.remote_dir}/reports/*", local_reports_dir):
        print(f"Relatórios copiados com sucesso para {local_reports_dir}")
    else:
        print("Falha ao copiar relatórios.")
    
    # Limpar arquivos temporários na VPS
    print("Limpando arquivos temporários na VPS...")
    run_ssh_command(args.host, args.user, args.key, f"rm -rf {args.remote_dir}")
    
    print("Análise de variáveis de ambiente concluída!")
    return 0

if __name__ == "__main__":
    sys.exit(main())