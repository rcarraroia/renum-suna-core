#!/usr/bin/env python3
"""
Script para verificar a configuração de rede Docker na VPS.
Este script analisa as redes Docker, a comunicação entre contêineres e a configuração de rede.
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
    parser = argparse.ArgumentParser(description='Check Docker network configuration')
    parser.add_argument('--host', default='157.180.39.41', help='VPS hostname or IP address')
    parser.add_argument('--port', type=int, default=22, help='SSH port')
    parser.add_argument('--user', default='root', help='SSH username')
    parser.add_argument('--key-file', help='Path to SSH private key file')
    parser.add_argument('--output-dir', default='./output', help='Directory to save output files')
    parser.add_argument('--containers-file', help='Path to containers JSON file (optional)')
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
                        'image': image,
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

def get_docker_networks(client):
    """Get Docker networks."""
    output = execute_command(client, "docker network ls --format '{{.ID}},{{.Name}},{{.Driver}},{{.Scope}}'")
    networks = []
    
    if output:
        for line in output.strip().split('\n'):
            if line:
                parts = line.split(',')
                if len(parts) >= 4:
                    network_id, name, driver, scope = parts
                    networks.append({
                        'id': network_id,
                        'name': name,
                        'driver': driver,
                        'scope': scope
                    })
    
    return networks

def get_network_details(client, network_id):
    """Get detailed information about a Docker network."""
    output = execute_command(client, f"docker network inspect {network_id}")
    
    if output:
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            print(f"Error parsing network details: {str(e)}")
            return {}
    
    return {}

def get_container_network_settings(client, container_id):
    """Get network settings for a Docker container."""
    output = execute_command(client, f"docker inspect -f '{{{{json .NetworkSettings}}}}' {container_id}")
    
    if output:
        try:
            # Clean the output (remove extra quotes)
            output = output.strip().strip("'")
            return json.loads(output)
        except json.JSONDecodeError as e:
            print(f"Error parsing network settings: {str(e)}")
            return {}
    
    return {}

def test_container_connectivity(client, source_container, target_container):
    """Test connectivity between two containers."""
    # First, get the IP address of the target container
    output = execute_command(client, f"docker inspect -f '{{{{.NetworkSettings.IPAddress}}}}' {target_container}")
    
    if not output or output.strip() == '':
        # Try to get IP from networks
        output = execute_command(client, f"docker inspect -f '{{{{json .NetworkSettings.Networks}}}}' {target_container}")
        
        if output:
            try:
                # Clean the output (remove extra quotes)
                output = output.strip().strip("'")
                networks = json.loads(output)
                
                # Get the first IP address found
                for network in networks.values():
                    if 'IPAddress' in network and network['IPAddress']:
                        target_ip = network['IPAddress']
                        break
                else:
                    print(f"Could not find IP address for container {target_container}")
                    return False, "No IP address found"
            except json.JSONDecodeError as e:
                print(f"Error parsing network settings: {str(e)}")
                return False, "Error parsing network settings"
        else:
            print(f"Could not find IP address for container {target_container}")
            return False, "No IP address found"
    else:
        target_ip = output.strip()
    
    # Test connectivity using ping
    ping_output = execute_command(client, f"docker exec {source_container} ping -c 3 {target_ip}")
    
    if ping_output and "bytes from" in ping_output:
        return True, ping_output
    
    # If ping fails, try to use wget or curl
    wget_output = execute_command(client, f"docker exec {source_container} wget -q -O - http://{target_ip}:80 || echo 'Connection failed'")
    
    if wget_output and "Connection failed" not in wget_output:
        return True, wget_output
    
    curl_output = execute_command(client, f"docker exec {source_container} curl -s http://{target_ip}:80 || echo 'Connection failed'")
    
    if curl_output and "Connection failed" not in curl_output:
        return True, curl_output
    
    return False, "All connection attempts failed"

def analyze_network_configuration(networks, containers):
    """Analyze Docker network configuration."""
    analysis = {
        'total_networks': len(networks),
        'network_types': {},
        'containers_without_network': [],
        'isolated_containers': [],
        'issues': [],
        'status': 'OK'
    }
    
    # Count network types
    for network in networks:
        driver = network['driver']
        if driver not in analysis['network_types']:
            analysis['network_types'][driver] = 0
        analysis['network_types'][driver] += 1
    
    # Check for containers without network
    container_networks = {}
    for container in containers:
        if container['is_running']:
            container_networks[container['name']] = []
    
    # Map containers to networks
    for network in networks:
        if 'containers' in network:
            for container_name in network['containers']:
                if container_name in container_networks:
                    container_networks[container_name].append(network['name'])
    
    # Check for containers without network
    for container_name, container_nets in container_networks.items():
        if not container_nets:
            analysis['containers_without_network'].append(container_name)
            analysis['issues'].append(f"Container {container_name} não está conectado a nenhuma rede")
    
    # Check for isolated containers (only connected to default bridge)
    for container_name, container_nets in container_networks.items():
        if len(container_nets) == 1 and container_nets[0] == 'bridge':
            analysis['isolated_containers'].append(container_name)
            analysis['issues'].append(f"Container {container_name} está isolado na rede bridge padrão")
    
    # Check for network issues
    if not any(network['driver'] == 'bridge' for network in networks):
        analysis['issues'].append("Nenhuma rede bridge personalizada encontrada")
    
    if analysis['issues']:
        analysis['status'] = 'WARNING'
    
    return analysis

def save_to_file(data, filename):
    """Save data to a file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if isinstance(data, (dict, list)):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(filename, 'w') as f:
            f.write(data if isinstance(data, str) else '\n'.join(data))

def main():
    """Main function."""
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load containers from file if provided
    containers = None
    if args.containers_file and os.path.exists(args.containers_file):
        try:
            with open(args.containers_file, 'r') as f:
                containers = json.load(f)
            print(f"Carregados {len(containers)} contêineres do arquivo {args.containers_file}")
        except Exception as e:
            print(f"Erro ao carregar contêineres do arquivo: {str(e)}")
            containers = None
    
    # Connect to SSH
    print(f"Conectando a {args.user}@{args.host}:{args.port}...")
    client = create_ssh_client(args.host, args.port, args.user, args.key_file)
    
    if not client:
        print("❌ Falha ao estabelecer conexão SSH")
        sys.exit(1)
    
    print("✅ Conexão SSH estabelecida")
    
    # Get containers if not loaded from file
    if not containers:
        containers = get_docker_containers(client)
        save_to_file(containers, os.path.join(args.output_dir, 'containers.json'))
    
    # Get Docker networks
    print("Obtendo redes Docker...")
    networks = get_docker_networks(client)
    save_to_file(networks, os.path.join(args.output_dir, 'networks.json'))
    
    # Get detailed information for each network
    network_details = {}
    for network in networks:
        network_id = network['id']
        network_name = network['name']
        print(f"Obtendo detalhes da rede: {network_name} ({network_id})")
        
        details = get_network_details(client, network_id)
        network_details[network_name] = details
        save_to_file(details, os.path.join(args.output_dir, f'network_{network_name}_details.json'))
    
    # Get network settings for each container
    container_networks = {}
    for container in containers:
        if container['is_running']:
            container_id = container['id']
            container_name = container['name']
            print(f"Obtendo configurações de rede do contêiner: {container_name}")
            
            settings = get_container_network_settings(client, container_id)
            container_networks[container_name] = settings
            save_to_file(settings, os.path.join(args.output_dir, f'{container_name}_network_settings.json'))
    
    # Test connectivity between key containers
    print("Testando conectividade entre contêineres...")
    connectivity_tests = {}
    
    # Find Renum and Suna containers
    renum_containers = [c for c in containers if c['is_running'] and c.get('category') == 'renum']
    suna_containers = [c for c in containers if c['is_running'] and c.get('category') == 'suna']
    db_containers = [c for c in containers if c['is_running'] and c.get('category') == 'database']
    
    # Test Renum -> Suna connectivity
    for renum in renum_containers:
        for suna in suna_containers:
            test_name = f"{renum['name']} -> {suna['name']}"
            print(f"Testando conectividade: {test_name}")
            
            success, output = test_container_connectivity(client, renum['id'], suna['id'])
            connectivity_tests[test_name] = {
                'success': success,
                'output': output
            }
    
    # Test Suna -> Renum connectivity
    for suna in suna_containers:
        for renum in renum_containers:
            test_name = f"{suna['name']} -> {renum['name']}"
            print(f"Testando conectividade: {test_name}")
            
            success, output = test_container_connectivity(client, suna['id'], renum['id'])
            connectivity_tests[test_name] = {
                'success': success,
                'output': output
            }
    
    # Test connectivity to database
    for container in renum_containers + suna_containers:
        for db in db_containers:
            test_name = f"{container['name']} -> {db['name']}"
            print(f"Testando conectividade: {test_name}")
            
            success, output = test_container_connectivity(client, container['id'], db['id'])
            connectivity_tests[test_name] = {
                'success': success,
                'output': output
            }
    
    save_to_file(connectivity_tests, os.path.join(args.output_dir, 'connectivity_tests.json'))
    
    # Analyze network configuration
    print("Analisando configuração de rede...")
    
    # Enhance networks with container information
    for network in networks:
        network_name = network['name']
        if network_name in network_details:
            details = network_details[network_name]
            if isinstance(details, list) and len(details) > 0:
                details = details[0]  # Docker inspect returns a list
            
            if 'Containers' in details:
                network['containers'] = list(details['Containers'].keys())
            else:
                network['containers'] = []
    
    analysis = analyze_network_configuration(networks, containers)
    save_to_file(analysis, os.path.join(args.output_dir, 'network_analysis.json'))
    
    # Generate report
    report = f"""
=======================================================
RELATÓRIO DE CONFIGURAÇÃO DE REDE DOCKER - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

Total de redes: {analysis['total_networks']}
Tipos de rede: {json.dumps(analysis['network_types'], indent=2)}

Redes disponíveis:
"""
    
    for network in networks:
        report += f"- {network['name']} ({network['driver']})\n"
        if 'containers' in network:
            for container in network['containers']:
                report += f"  - {container}\n"
    
    report += "\nTestes de conectividade:\n"
    
    for test_name, test_result in connectivity_tests.items():
        status = "✅ Sucesso" if test_result['success'] else "❌ Falha"
        report += f"- {test_name}: {status}\n"
    
    if analysis['issues']:
        report += "\nPROBLEMAS DETECTADOS:\n"
        for issue in analysis['issues']:
            report += f"- {issue}\n"
    else:
        report += "\nNenhum problema de rede detectado.\n"
    
    save_to_file(report, os.path.join(args.output_dir, 'network_report.txt'))
    print(report)
    
    client.close()
    print("Conexão SSH encerrada")
    print(f"Análise de rede concluída. Resultados salvos em {args.output_dir}")

if __name__ == "__main__":
    main()