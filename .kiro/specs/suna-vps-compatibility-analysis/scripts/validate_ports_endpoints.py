#!/usr/bin/env python3
"""
Script para validar a configuração de portas e endpoints dos serviços Renum e Suna.
Este script verifica a exposição correta de portas e testa o acesso externo aos serviços.
"""

import os
import sys
import json
import argparse
import paramiko
import getpass
import re
from pathlib import Path
from datetime import datetime

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Validate ports and endpoints configuration')
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
    output = execute_command(client, "docker ps -a --format '{{.ID}},{{.Names}},{{.Status}},{{.Image}},{{.Ports}}'")
    containers = []
    
    if output:
        for line in output.strip().split('\n'):
            if line:
                parts = line.split(',', 4)
                if len(parts) >= 5:
                    container_id, name, status, image, ports = parts
                    containers.append({
                        'id': container_id,
                        'name': name,
                        'status': status,
                        'image': image,
                        'ports': ports,
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

def get_exposed_ports(client, container_id):
    """Get exposed ports of a container."""
    output = execute_command(client, f"docker port {container_id}")
    
    ports = {}
    if output:
        for line in output.strip().split('\n'):
            if '->' in line:
                container_port, host_mapping = line.split('->', 1)
                container_port = container_port.strip()
                host_mapping = host_mapping.strip()
                ports[container_port] = host_mapping
    
    return ports

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

def test_external_access(client, host, port, path='/'):
    """Test external access to a service."""
    # Test using curl from the host
    command = f"curl -s -o /dev/null -w '%{{http_code}}' http://{host}:{port}{path}"
    status_code = execute_command(client, command).strip()
    
    if status_code and status_code.startswith('2'):  # 2xx status code
        return True, int(status_code)
    elif status_code:
        return False, int(status_code)
    else:
        return False, 0

def get_open_ports(client):
    """Get list of open ports on the host."""
    output = execute_command(client, "netstat -tuln")
    
    open_ports = []
    if output:
        for line in output.strip().split('\n'):
            if 'LISTEN' in line:
                # Extract port from the line
                match = re.search(r':(\d+)\s', line)
                if match:
                    port = match.group(1)
                    open_ports.append(port)
    
    return open_ports

def get_firewall_rules(client):
    """Get firewall rules."""
    # Try ufw first
    output = execute_command(client, "ufw status")
    
    if output and 'Status: active' in output:
        return output
    
    # Try iptables
    output = execute_command(client, "iptables -L -n")
    
    if output:
        return output
    
    return "No firewall rules found"

def validate_ports_configuration(containers, exposed_ports, open_ports, firewall_rules):
    """Validate ports configuration."""
    validation = {
        'containers_with_ports': sum(1 for c in containers if c['ports'] and c['ports'] != ''),
        'containers_without_ports': sum(1 for c in containers if not c['ports'] or c['ports'] == ''),
        'total_exposed_ports': sum(len(ports) for ports in exposed_ports.values()),
        'open_ports': len(open_ports),
        'issues': [],
        'status': 'OK'
    }
    
    # Check if critical containers have exposed ports
    for container in containers:
        if container['category'] in ['renum', 'suna'] and container['is_running']:
            if not container['ports'] or container['ports'] == '':
                validation['issues'].append(f"Contêiner crítico {container['name']} não tem portas expostas")
    
    # Check if exposed ports are actually open
    for container_name, ports in exposed_ports.items():
        for container_port, host_mapping in ports.items():
            if ':' in host_mapping:
                host_port = host_mapping.split(':')[1]
                if host_port not in open_ports:
                    validation['issues'].append(f"Porta {host_port} mapeada para {container_name} não está aberta no host")
    
    # Check firewall rules for exposed ports
    if 'ufw' in firewall_rules.lower() and 'Status: active' in firewall_rules:
        for container_name, ports in exposed_ports.items():
            for container_port, host_mapping in ports.items():
                if ':' in host_mapping:
                    host_port = host_mapping.split(':')[1]
                    if host_port not in firewall_rules:
                        validation['issues'].append(f"Porta {host_port} pode estar bloqueada pelo firewall")
    
    if validation['issues']:
        validation['status'] = 'WARNING'
    
    return validation

def validate_endpoints_configuration(containers, exposed_ports, external_access_tests):
    """Validate endpoints configuration."""
    validation = {
        'total_endpoints_tested': sum(len(tests) for tests in external_access_tests.values()),
        'accessible_endpoints': sum(
            1 for container_tests in external_access_tests.values() 
            for test in container_tests 
            if test['success']
        ),
        'inaccessible_endpoints': sum(
            1 for container_tests in external_access_tests.values() 
            for test in container_tests 
            if not test['success']
        ),
        'issues': [],
        'status': 'OK'
    }
    
    # Check if critical endpoints are accessible
    for container in containers:
        if container['category'] in ['renum', 'suna'] and container['is_running']:
            container_name = container['name']
            if container_name in external_access_tests:
                # Check if at least one endpoint is accessible
                if not any(test['success'] for test in external_access_tests[container_name]):
                    validation['issues'].append(f"Nenhum endpoint do contêiner {container_name} está acessível externamente")
            else:
                validation['issues'].append(f"Nenhum teste de acesso externo realizado para o contêiner {container_name}")
    
    if validation['issues']:
        validation['status'] = 'WARNING'
    
    return validation

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
    
    # Get exposed ports for each container
    exposed_ports = {}
    for container in containers:
        if container['is_running']:
            container_id = container['id']
            container_name = container['name']
            print(f"Obtendo portas expostas do contêiner: {container_name}")
            
            ports = get_exposed_ports(client, container_id)
            exposed_ports[container_name] = ports
            save_to_file(ports, os.path.join(args.output_dir, f'{container_name}_exposed_ports.json'))
    
    # Get open ports on the host
    print("Obtendo portas abertas no host...")
    open_ports = get_open_ports(client)
    save_to_file(open_ports, os.path.join(args.output_dir, 'open_ports.json'))
    
    # Get firewall rules
    print("Obtendo regras de firewall...")
    firewall_rules = get_firewall_rules(client)
    save_to_file(firewall_rules, os.path.join(args.output_dir, 'firewall_rules.txt'))
    
    # Test external access to services
    external_access_tests = {}
    
    for container in containers:
        if container['is_running'] and container['category'] in ['renum', 'suna']:
            container_name = container['name']
            container_id = container['id']
            print(f"Testando acesso externo ao contêiner: {container_name}")
            
            # Get environment variables to find API endpoints
            env_vars = get_container_env_vars(client, container_id)
            
            # Get ports
            ports = exposed_ports.get(container_name, {})
            
            # Test endpoints
            container_tests = []
            
            # Test each exposed port
            for container_port, host_mapping in ports.items():
                if ':' in host_mapping:
                    host_ip, host_port = host_mapping.rsplit(':', 1)
                    
                    # Test root path
                    print(f"  Testando acesso a http://{args.host}:{host_port}/")
                    success, status_code = test_external_access(client, args.host, host_port, '/')
                    container_tests.append({
                        'endpoint': f"http://{args.host}:{host_port}/",
                        'success': success,
                        'status_code': status_code
                    })
                    
                    # Test health endpoint
                    print(f"  Testando acesso a http://{args.host}:{host_port}/health")
                    success, status_code = test_external_access(client, args.host, host_port, '/health')
                    container_tests.append({
                        'endpoint': f"http://{args.host}:{host_port}/health",
                        'success': success,
                        'status_code': status_code
                    })
                    
                    # Test docs endpoint
                    print(f"  Testando acesso a http://{args.host}:{host_port}/docs")
                    success, status_code = test_external_access(client, args.host, host_port, '/docs')
                    container_tests.append({
                        'endpoint': f"http://{args.host}:{host_port}/docs",
                        'success': success,
                        'status_code': status_code
                    })
                    
                    # Test API endpoint
                    print(f"  Testando acesso a http://{args.host}:{host_port}/api")
                    success, status_code = test_external_access(client, args.host, host_port, '/api')
                    container_tests.append({
                        'endpoint': f"http://{args.host}:{host_port}/api",
                        'success': success,
                        'status_code': status_code
                    })
            
            external_access_tests[container_name] = container_tests
            save_to_file(container_tests, os.path.join(args.output_dir, f'{container_name}_external_access_tests.json'))
    
    # Validate ports configuration
    print("Validando configuração de portas...")
    ports_validation = validate_ports_configuration(containers, exposed_ports, open_ports, firewall_rules)
    save_to_file(ports_validation, os.path.join(args.output_dir, 'ports_validation.json'))
    
    # Validate endpoints configuration
    print("Validando configuração de endpoints...")
    endpoints_validation = validate_endpoints_configuration(containers, exposed_ports, external_access_tests)
    save_to_file(endpoints_validation, os.path.join(args.output_dir, 'endpoints_validation.json'))
    
    # Generate summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'containers_analyzed': len(containers),
        'containers_with_ports': ports_validation['containers_with_ports'],
        'containers_without_ports': ports_validation['containers_without_ports'],
        'total_exposed_ports': ports_validation['total_exposed_ports'],
        'open_ports': ports_validation['open_ports'],
        'total_endpoints_tested': endpoints_validation['total_endpoints_tested'],
        'accessible_endpoints': endpoints_validation['accessible_endpoints'],
        'inaccessible_endpoints': endpoints_validation['inaccessible_endpoints'],
        'ports_status': ports_validation['status'],
        'endpoints_status': endpoints_validation['status'],
        'overall_status': 'OK' if ports_validation['status'] == 'OK' and endpoints_validation['status'] == 'OK' else 'WARNING'
    }
    
    save_to_file(summary, os.path.join(args.output_dir, 'ports_endpoints_summary.json'))
    
    # Generate text report
    report = f"""
=======================================================
RELATÓRIO DE CONFIGURAÇÃO DE PORTAS E ENDPOINTS - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

Contêineres analisados: {summary['containers_analyzed']}
Contêineres com portas expostas: {summary['containers_with_ports']}
Contêineres sem portas expostas: {summary['containers_without_ports']}
Total de portas expostas: {summary['total_exposed_ports']}
Portas abertas no host: {summary['open_ports']}

Endpoints testados: {summary['total_endpoints_tested']}
Endpoints acessíveis: {summary['accessible_endpoints']}
Endpoints inacessíveis: {summary['inaccessible_endpoints']}

Status da configuração de portas: {summary['ports_status']}
Status da configuração de endpoints: {summary['endpoints_status']}
Status geral: {summary['overall_status']}

"""
    
    # Add details about exposed ports
    report += "PORTAS EXPOSTAS POR CONTÊINER:\n"
    for container_name, ports in exposed_ports.items():
        report += f"\n{container_name}:\n"
        if ports:
            for container_port, host_mapping in ports.items():
                report += f"  - {container_port} -> {host_mapping}\n"
        else:
            report += "  Nenhuma porta exposta\n"
    
    # Add details about external access tests
    report += "\nTESTES DE ACESSO EXTERNO:\n"
    for container_name, tests in external_access_tests.items():
        report += f"\n{container_name}:\n"
        for test in tests:
            status = "✅ Sucesso" if test['success'] else f"❌ Falha (Status: {test['status_code']})"
            report += f"  - {test['endpoint']}: {status}\n"
    
    # Add issues
    if ports_validation['issues'] or endpoints_validation['issues']:
        report += "\nPROBLEMAS DETECTADOS:\n"
        
        if ports_validation['issues']:
            report += "\nProblemas de configuração de portas:\n"
            for issue in ports_validation['issues']:
                report += f"- {issue}\n"
        
        if endpoints_validation['issues']:
            report += "\nProblemas de configuração de endpoints:\n"
            for issue in endpoints_validation['issues']:
                report += f"- {issue}\n"
    else:
        report += "\nNenhum problema detectado na configuração de portas e endpoints.\n"
    
    # Add recommendations
    report += "\nRECOMENDAÇÕES:\n"
    
    if ports_validation['containers_without_ports'] > 0:
        report += "- Verificar se todos os contêineres críticos têm portas expostas\n"
    
    if ports_validation['total_exposed_ports'] > ports_validation['open_ports']:
        report += "- Verificar se todas as portas mapeadas estão realmente abertas no host\n"
    
    if 'ufw' in firewall_rules.lower() and 'Status: active' in firewall_rules:
        report += "- Confirmar que o firewall permite acesso às portas necessárias\n"
    
    if endpoints_validation['inaccessible_endpoints'] > 0:
        report += "- Investigar por que alguns endpoints não estão acessíveis externamente\n"
    
    save_to_file(report, os.path.join(args.output_dir, 'ports_endpoints_report.txt'))
    print(report)
    
    client.close()
    print("Conexão SSH encerrada")
    print(f"Validação de portas e endpoints concluída. Resultados salvos em {args.output_dir}")

if __name__ == "__main__":
    main()