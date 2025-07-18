#!/usr/bin/env python3
"""
Script para estabelecer conexão segura com a VPS do Suna e verificar acesso aos contêineres Docker.
Este script utiliza a biblioteca paramiko para conexão SSH.
"""

import os
import sys
import paramiko
import argparse
import getpass
from pathlib import Path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Connect to Suna VPS and verify Docker access')
    parser.add_argument('--host', default='157.180.39.41', help='VPS hostname or IP address')
    parser.add_argument('--port', type=int, default=22, help='SSH port')
    parser.add_argument('--user', default='root', help='SSH username')
    parser.add_argument('--key-file', help='Path to SSH private key file')
    parser.add_argument('--command', default='docker ps -a', help='Command to execute')
    return parser.parse_args()

def create_ssh_client(host, port, user, key_file=None):
    """Create an SSH client connection."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if key_file:
            key_path = os.path.expanduser(key_file)
            if not os.path.exists(key_path):
                print(f"Error: Key file {key_path} does not exist.")
                sys.exit(1)
            
            try:
                key = paramiko.RSAKey.from_private_key_file(key_path)
                client.connect(host, port=port, username=user, pkey=key)
            except paramiko.ssh_exception.PasswordRequiredException:
                passphrase = getpass.getpass("Enter passphrase for key: ")
                key = paramiko.RSAKey.from_private_key_file(key_path, password=passphrase)
                client.connect(host, port=port, username=user, pkey=key)
        else:
            password = getpass.getpass("Enter password for {user}@{host}: ")
            client.connect(host, port=port, username=user, password=password)
        
        return client
    except Exception as e:
        print(f"Error connecting to {host}: {str(e)}")
        sys.exit(1)

def execute_command(client, command):
    """Execute a command on the remote server."""
    try:
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if error:
            print(f"Error executing command: {error}")
        
        return output
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        return None

def check_docker_access(client):
    """Check if we have access to Docker on the remote server."""
    print("Checking Docker access...")
    output = execute_command(client, "docker ps -a")
    
    if output and "CONTAINER ID" in output:
        print("✅ Docker access confirmed")
        print("\nDocker containers:")
        print(output)
        return True
    else:
        print("❌ No Docker access or Docker not installed")
        return False

def main():
    """Main function."""
    args = parse_arguments()
    
    print(f"Connecting to {args.user}@{args.host}:{args.port}...")
    client = create_ssh_client(args.host, args.port, args.user, args.key_file)
    
    if client:
        print("✅ SSH connection established")
        
        # Check Docker access
        has_docker_access = check_docker_access(client)
        
        if has_docker_access and args.command != "docker ps -a":
            print(f"\nExecuting command: {args.command}")
            output = execute_command(client, args.command)
            if output:
                print("\nCommand output:")
                print(output)
        
        client.close()
        print("SSH connection closed")

if __name__ == "__main__":
    main()