#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para executar a análise de estrutura de diretórios e permissões na VPS.
Este script se conecta à VPS via SSH, copia o script de análise e o executa remotamente.
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
    parser = argparse.ArgumentParser(description="Executa análise de estrutura de diretórios na VPS")
    parser.add_argument("--host", default=VPS_HOST, help="Endereço IP ou hostname da VPS")
    parser.add_argument("--user", default=VPS_USER, help="Usuário SSH para conexão")
    parser.add_argument("--key", default=SSH_KEY_PATH, help="Caminho para a chave SSH")
    parser.add_argument("--remote-dir", default="/tmp/dir-analysis", help="Diretório remoto para os scripts")
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
    
    print(f"Iniciando análise de estrutura de diretórios na VPS {args.host}...")
    
    # Verificar conexão SSH
    print("Verificando conexão SSH...")
    stdout, error = run_ssh_command(args.host, args.user, args.key, "echo 'Conexão SSH estabelecida'")
    if error:
        print(f"Erro ao conectar via SSH: {error}")
        return 1
    print(stdout)
    
    # Criar diretório remoto
    print(f"Criando diretório remoto {args.remote_dir}...")
    run_ssh_command(args.host, args.user, args.key, f"mkdir -p {args.remote_dir}/reports")
    
    # Obter caminho do script local
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "check_directory_structure.py")
    
    # Copiar script para a VPS
    print("Copiando script para a VPS...")
    remote_script_path = f"{args.remote_dir}/check_directory_structure.py"
    if not copy_file_to_vps(args.host, args.user, args.key, script_path, remote_script_path):
        print("Falha ao copiar script. Abortando.")
        return 1
    
    # Dar permissão de execução ao script
    print("Configurando permissões do script...")
    run_ssh_command(args.host, args.user, args.key, f"chmod +x {remote_script_path}")
    
    # Executar análise na VPS
    print("Executando análise na VPS...")
    stdout, error = run_ssh_command(
        args.host, 
        args.user, 
        args.key, 
        f"cd {args.remote_dir} && python3 check_directory_structure.py"
    )
    
    if error:
        print(f"Erro durante a execução da análise: {error}")
    else:
        print("Análise concluída com sucesso!")
        
    # Criar diretório local para relatórios
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    local_reports_dir = os.path.join(os.path.dirname(script_dir), "reports", f"dir_analysis_{timestamp}")
    os.makedirs(local_reports_dir, exist_ok=True)
    
    # Copiar relatório da VPS
    print(f"Copiando relatório para {local_reports_dir}...")
    if copy_directory_from_vps(args.host, args.user, args.key, f"{args.remote_dir}/reports/*", local_reports_dir):
        print(f"Relatório copiado com sucesso para {local_reports_dir}")
    else:
        print("Falha ao copiar relatório.")
    
    # Limpar arquivos temporários na VPS
    print("Limpando arquivos temporários na VPS...")
    run_ssh_command(args.host, args.user, args.key, f"rm -rf {args.remote_dir}")
    
    print("Análise de estrutura de diretórios concluída!")
    return 0

if __name__ == "__main__":
    sys.exit(main())