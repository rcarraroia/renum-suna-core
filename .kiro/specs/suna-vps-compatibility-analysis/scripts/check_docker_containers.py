#!/usr/bin/env python3
"""
Script para listar e verificar contêineres Docker em execução na VPS.
Este script analisa detalhadamente os contêineres, identificando os relacionados ao Renum e Suna.
"""

import os
import sys
import json
import argparse
import paramiko
import getpass
from pathlib import Path
from datetime import datetime

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Check Docker containers')
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
            password = getpass.getpass(f"Enter password for {user}@{host}: ")
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
    """Get detailed information about Docker containers."""
    print("Listando contêineres Docker...")
    
    # Get basic container information
    output = execute_command(client, "docker ps -a --format '{{.ID}},{{.Names}},{{.Status}},{{.Image}},{{.Ports}},{{.Command}}'")
    containers = []
    
    if output:
        for line in output.strip().split('\n'):
            if line:
                parts = line.split(',', 5)
                if len(parts) >= 6:
                    container_id, name, status, image, ports, command = parts
                    containers.append({
                        'id': container_id,
                        'name': name,
                        'status': status,
                        'image': image,
                        'ports': ports,
                        'command': command,
                        'is_running': 'Up' in status
                    })
    
    # Categorize containers
    for container in containers:
        if 'renum' in container['name'].lower() or 'renum' in container['image'].lower():
            container['category'] = 'renum'
        elif 'suna' in container['name'].lower() or 'suna' in container['image'].lower():
            container['category'] = 'suna'
        elif 'postgres' in container['name'].lower() or 'postgres' in container['image'].lower():
            container['category'] = 'database'
        elif 'redis' in container['name'].lower() or 'redis' in container['image'].lower():
            container['category'] = 'cache'
        elif 'rabbitmq' in container['name'].lower() or 'rabbitmq' in container['image'].lower():
            container['category'] = 'message_queue'
        else:
            container['category'] = 'other'
    
    return containers

def get_container_details(client, container_id):
    """Get detailed information about a specific container."""
    output = execute_command(client, f"docker inspect {container_id}")
    
    if output:
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            print(f"Error parsing container details: {str(e)}")
            return {}
    
    return {}

def get_container_logs(client, container_id, lines=50):
    """Get logs from a container."""
    output = execute_command(client, f"docker logs --tail {lines} {container_id}")
    return output

def get_container_stats(client, container_id):
    """Get container stats."""
    output = execute_command(client, f"docker stats --no-stream --format '{{{{.Name}}}},{{{{.CPUPerc}}}},{{{{.MemUsage}}}},{{{{.NetIO}}}},{{{{.BlockIO}}}}' {container_id}")
    
    if output:
        lines = output.strip().split('\n')
        if len(lines) >= 2:  # Header + data
            parts = lines[1].split(',')
            if len(parts) >= 5:
                return {
                    'name': parts[0],
                    'cpu_percent': parts[1],
                    'memory_usage': parts[2],
                    'network_io': parts[3],
                    'block_io': parts[4]
                }
    
    return {}

def analyze_containers(containers):
    """Analyze containers and generate summary."""
    summary = {
        'total': len(containers),
        'running': sum(1 for c in containers if c.get('is_running', False)),
        'stopped': sum(1 for c in containers if not c.get('is_running', False)),
        'categories': {},
        'issues': []
    }
    
    # Count by category
    for container in containers:
        category = container.get('category', 'other')
        if category not in summary['categories']:
            summary['categories'][category] = 0
        summary['categories'][category] += 1
    
    # Check for issues
    for container in containers:
        # Check if critical containers are running
        if container.get('category') in ['renum', 'suna', 'database', 'cache', 'message_queue'] and not container.get('is_running', False):
            summary['issues'].append(f"Contêiner crítico parado: {container['name']} ({container['category']})")
    
    return summary

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
    
    print(f"Conectando a {args.user}@{args.host}:{args.port}...")
    client = create_ssh_client(args.host, args.port, args.user, args.key_file)
    
    if client:
        print("✅ Conexão SSH estabelecida")
        
        # Get Docker containers
        containers = get_docker_containers(client)
        save_to_file(containers, os.path.join(args.output_dir, 'containers_detailed.json'))
        
        # Get details for each container
        for container in containers:
            container_id = container['id']
            container_name = container['name']
            print(f"Obtendo detalhes do contêiner: {container_name} ({container_id})")
            
            # Get container details
            details = get_container_details(client, container_id)
            save_to_file(details, os.path.join(args.output_dir, f'{container_name}_details.json'))
            
            # Get container logs if running
            if container.get('is_running', False):
                print(f"Obtendo logs do contêiner: {container_name}")
                logs = get_container_logs(client, container_id)
                save_to_file(logs, os.path.join(args.output_dir, f'{container_name}_logs.txt'))
                
                # Get container stats
                print(f"Obtendo estatísticas do contêiner: {container_name}")
                stats = get_container_stats(client, container_id)
                save_to_file(stats, os.path.join(args.output_dir, f'{container_name}_stats.json'))
        
        # Analyze containers
        summary = analyze_containers(containers)
        save_to_file(summary, os.path.join(args.output_dir, 'containers_summary.json'))
        
        # Generate report
        report = f"""
=======================================================
RELATÓRIO DE CONTÊINERES DOCKER - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

Total de contêineres: {summary['total']}
Em execução: {summary['running']}
Parados: {summary['stopped']}

Categorias:
{json.dumps(summary['categories'], indent=2)}

Contêineres por categoria:
"""
        
        for category in summary['categories'].keys():
            report += f"\n[{category.upper()}]\n"
            for container in containers:
                if container.get('category') == category:
                    status = "✅ Em execução" if container.get('is_running', False) else "❌ Parado"
                    report += f"- {container['name']} ({container['image']}): {status}\n"
        
        if summary['issues']:
            report += "\nPROBLEMAS DETECTADOS:\n"
            for issue in summary['issues']:
                report += f"- {issue}\n"
        else:
            report += "\nNenhum problema crítico detectado.\n"
        
        save_to_file(report, os.path.join(args.output_dir, 'containers_report.txt'))
        print(report)
        
        client.close()
        print("Conexão SSH encerrada")
        print(f"Análise de contêineres concluída. Resultados salvos em {args.output_dir}")

if __name__ == "__main__":
    main()