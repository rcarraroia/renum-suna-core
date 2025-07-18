#!/usr/bin/env python3
"""
Script para coletar informações sobre variáveis de ambiente e estrutura de diretórios
dos contêineres Docker do Renum e Suna na VPS.
"""

import os
import sys
import json
import argparse
import paramiko
import getpass
from pathlib import Path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Collect environment and directory structure information')
    parser.add_argument('--host', default='157.180.39.41', help='VPS hostname or IP address')
    parser.add_argument('--port', type=int, default=22, help='SSH port')
    parser.add_argument('--user', default='root', help='SSH username')
    parser.add_argument('--key-file', help='Path to SSH private key file')
    parser.add_argument('--output-dir', default='./output', help='Directory to save output files')
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
        
        if error and not output:
            print(f"Error executing command: {error}")
        
        return output
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        return None

def get_docker_containers(client):
    """Get list of Docker containers."""
    output = execute_command(client, "docker ps -a --format '{{.ID}},{{.Names}},{{.Status}},{{.Image}}'")
    containers = []
    
    if output:
        for line in output.strip().split('\n'):
            if line:
                parts = line.split(',')
                if len(parts) >= 4:
                    container_id, name, status, image = parts[0], parts[1], parts[2], parts[3]
                    containers.append({
                        'id': container_id,
                        'name': name,
                        'status': status,
                        'image': image
                    })
    
    return containers

def get_container_env_vars(client, container_id):
    """Get environment variables for a Docker container."""
    output = execute_command(client, f"docker inspect -f '{{{{json .Config.Env}}}}' {container_id}")
    
    if output:
        try:
            # Clean the output (remove extra quotes)
            output = output.strip().strip("'")
            env_vars = json.loads(output)
            
            # Convert list of "KEY=VALUE" to dictionary
            env_dict = {}
            for env in env_vars:
                if '=' in env:
                    key, value = env.split('=', 1)
                    # Mask sensitive values
                    if any(sensitive in key.lower() for sensitive in ['key', 'token', 'secret', 'password', 'auth']):
                        env_dict[key] = '******'
                    else:
                        env_dict[key] = value
            
            return env_dict
        except json.JSONDecodeError as e:
            print(f"Error parsing environment variables: {str(e)}")
            return {}
    
    return {}

def get_container_volumes(client, container_id):
    """Get volumes for a Docker container."""
    output = execute_command(client, f"docker inspect -f '{{{{json .Mounts}}}}' {container_id}")
    
    if output:
        try:
            # Clean the output (remove extra quotes)
            output = output.strip().strip("'")
            return json.loads(output)
        except json.JSONDecodeError as e:
            print(f"Error parsing volumes: {str(e)}")
            return []
    
    return []

def get_directory_structure(client, path):
    """Get directory structure for a path."""
    output = execute_command(client, f"find {path} -type d -not -path '*/\\.*' | sort")
    
    if output:
        return output.strip().split('\n')
    
    return []

def get_file_permissions(client, path):
    """Get file permissions for a path."""
    output = execute_command(client, f"ls -la {path}")
    
    if output:
        return output.strip().split('\n')
    
    return []

def save_to_file(data, filename):
    """Save data to a file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if isinstance(data, (dict, list)):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(filename, 'w') as f:
            f.write(data)

def main():
    """Main function."""
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Connecting to {args.user}@{args.host}:{args.port}...")
    client = create_ssh_client(args.host, args.port, args.user, args.key_file)
    
    if client:
        print("✅ SSH connection established")
        
        # Get Docker containers
        print("Collecting Docker container information...")
        containers = get_docker_containers(client)
        save_to_file(containers, os.path.join(args.output_dir, 'containers.json'))
        
        # Process each container
        for container in containers:
            container_id = container['id']
            container_name = container['name']
            print(f"Processing container: {container_name} ({container_id})")
            
            # Get environment variables
            env_vars = get_container_env_vars(client, container_id)
            save_to_file(env_vars, os.path.join(args.output_dir, f'{container_name}_env.json'))
            
            # Get volumes
            volumes = get_container_volumes(client, container_id)
            save_to_file(volumes, os.path.join(args.output_dir, f'{container_name}_volumes.json'))
            
            # For each volume, get directory structure and permissions
            for volume in volumes:
                if 'Source' in volume and volume['Source'].startswith('/'):
                    source_path = volume['Source']
                    dir_name = os.path.basename(source_path)
                    
                    print(f"Collecting directory structure for: {source_path}")
                    dirs = get_directory_structure(client, source_path)
                    save_to_file('\n'.join(dirs), os.path.join(args.output_dir, f'{container_name}_{dir_name}_dirs.txt'))
                    
                    print(f"Collecting file permissions for: {source_path}")
                    perms = get_file_permissions(client, source_path)
                    save_to_file('\n'.join(perms), os.path.join(args.output_dir, f'{container_name}_{dir_name}_perms.txt'))
        
        # Get Docker network information
        print("Collecting Docker network information...")
        networks = execute_command(client, "docker network ls --format '{{.ID}},{{.Name}},{{.Driver}}'")
        save_to_file(networks, os.path.join(args.output_dir, 'networks.txt'))
        
        # Get detailed network information
        network_details = {}
        for line in networks.strip().split('\n'):
            if line:
                parts = line.split(',')
                if len(parts) >= 2:
                    network_id, network_name = parts[0], parts[1]
                    print(f"Collecting details for network: {network_name}")
                    details = execute_command(client, f"docker network inspect {network_id}")
                    try:
                        network_details[network_name] = json.loads(details)
                    except json.JSONDecodeError:
                        network_details[network_name] = details
        
        save_to_file(network_details, os.path.join(args.output_dir, 'network_details.json'))
        
        client.close()
        print("SSH connection closed")
        print(f"All data collected and saved to {args.output_dir}")

if __name__ == "__main__":
    main()