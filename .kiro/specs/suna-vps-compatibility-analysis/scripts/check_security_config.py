#!/usr/bin/env python3
"""
Script para verificar configurações de segurança dos serviços Renum e Suna.
Este script analisa exposição de serviços, configurações de firewall e identifica vulnerabilidades potenciais.
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
    parser = argparse.ArgumentParser(description='Check security configuration')
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

def check_firewall_config(client):
    """Check firewall configuration."""
    # Check UFW status
    ufw_status = execute_command(client, "ufw status 2>/dev/null || echo 'UFW not installed'")
    
    # Check iptables rules
    iptables_rules = execute_command(client, "iptables -L -n 2>/dev/null || echo 'iptables not available'")
    
    # Check if firewall is active
    firewall_active = False
    if 'Status: active' in ufw_status:
        firewall_active = True
    elif 'Chain INPUT' in iptables_rules and 'policy DROP' in iptables_rules:
        firewall_active = True
    
    return {
        'ufw_status': ufw_status,
        'iptables_rules': iptables_rules,
        'firewall_active': firewall_active
    }

def check_open_ports(client):
    """Check for open ports on the host."""
    # Get listening ports
    netstat_output = execute_command(client, "netstat -tuln || ss -tuln")
    
    # Parse open ports
    open_ports = []
    if netstat_output:
        for line in netstat_output.split('\n'):
            if ('LISTEN' in line or 'ESTAB' in line) and ':' in line:
                # Extract port number
                parts = line.split()
                for part in parts:
                    if ':' in part:
                        try:
                            address = part.split(':')[-1]
                            if address.isdigit():
                                port = int(address)
                                if port not in open_ports:
                                    open_ports.append(port)
                        except:
                            pass
    
    return {
        'netstat_output': netstat_output,
        'open_ports': sorted(open_ports)
    }

def check_ssh_config(client):
    """Check SSH configuration for security issues."""
    # Get SSH config
    ssh_config = execute_command(client, "cat /etc/ssh/sshd_config 2>/dev/null || echo 'SSH config not found'")
    
    # Check for security issues
    issues = []
    
    # Check if root login is allowed
    if 'PermitRootLogin yes' in ssh_config:
        issues.append("Root login is allowed")
    
    # Check if password authentication is allowed
    if 'PasswordAuthentication yes' in ssh_config or 'PasswordAuthentication' not in ssh_config:
        issues.append("Password authentication is allowed")
    
    # Check if SSH is running on default port
    if 'Port 22' in ssh_config or 'Port' not in ssh_config:
        issues.append("SSH is running on default port (22)")
    
    return {
        'ssh_config': ssh_config,
        'issues': issues
    }

def check_docker_security(client):
    """Check Docker security configuration."""
    # Check Docker daemon configuration
    daemon_config = execute_command(client, "cat /etc/docker/daemon.json 2>/dev/null || echo '{}'")
    
    try:
        config = json.loads(daemon_config)
    except json.JSONDecodeError:
        config = {}
    
    # Check for security issues
    issues = []
    
    # Check if Docker socket is exposed
    socket_exposed = execute_command(client, "ls -la /var/run/docker.sock 2>/dev/null || echo 'Socket not found'")
    socket_permissions = None
    
    if 'Socket not found' not in socket_exposed:
        # Check socket permissions
        socket_permissions = socket_exposed.split()[0] if len(socket_exposed.split()) > 0 else None
        if socket_permissions and ('rw-rw-' in socket_permissions or 'rw-r--' in socket_permissions):
            issues.append("Docker socket has loose permissions")
    
    # Check if Docker API is exposed
    docker_api_exposed = False
    open_ports_output = execute_command(client, "netstat -tuln | grep -E ':(2375|2376)'")
    if open_ports_output:
        docker_api_exposed = True
        issues.append("Docker API is exposed on network")
    
    # Check if Docker is running in privileged mode
    privileged_containers = []
    for container_id in execute_command(client, "docker ps -q").strip().split('\n'):
        if container_id:
            inspect_output = execute_command(client, f"docker inspect --format='{{{{.HostConfig.Privileged}}}}' {container_id}")
            if inspect_output and inspect_output.strip() == 'true':
                container_name = execute_command(client, f"docker inspect --format='{{{{.Name}}}}' {container_id}").strip()
                privileged_containers.append(container_name)
    
    if privileged_containers:
        issues.append(f"Containers running in privileged mode: {', '.join(privileged_containers)}")
    
    return {
        'daemon_config': config,
        'socket_exposed': 'Socket not found' not in socket_exposed,
        'socket_permissions': socket_permissions,
        'docker_api_exposed': docker_api_exposed,
        'privileged_containers': privileged_containers,
        'issues': issues
    }

def check_container_security(client, container_id, container_name):
    """Check security configuration for a container."""
    # Check if container is running as root
    user_output = execute_command(client, f"docker exec {container_id} whoami 2>/dev/null || echo 'unknown'")
    running_as_root = user_output.strip() == 'root'
    
    # Check if container has sensitive mounts
    sensitive_mounts = []
    mounts_output = execute_command(client, f"docker inspect -f '{{{{json .Mounts}}}}' {container_id}")
    
    if mounts_output:
        try:
            mounts = json.loads(mounts_output.strip().strip("'"))
            for mount in mounts:
                if 'Source' in mount and 'Destination' in mount:
                    source = mount['Source']
                    destination = mount['Destination']
                    
                    # Check for sensitive mounts
                    if source == '/var/run/docker.sock':
                        sensitive_mounts.append(f"{source} -> {destination}")
                    elif source.startswith('/etc'):
                        sensitive_mounts.append(f"{source} -> {destination}")
                    elif source == '/':
                        sensitive_mounts.append(f"{source} -> {destination}")
        except json.JSONDecodeError:
            pass
    
    # Check if container has capabilities
    capabilities_output = execute_command(client, f"docker inspect -f '{{{{json .HostConfig.CapAdd}}}}' {container_id}")
    capabilities = []
    
    if capabilities_output and capabilities_output.strip() != 'null':
        try:
            caps = json.loads(capabilities_output.strip().strip("'"))
            if caps:
                capabilities = caps
        except json.JSONDecodeError:
            pass
    
    # Check if container is using host network
    network_output = execute_command(client, f"docker inspect -f '{{{{.HostConfig.NetworkMode}}}}' {container_id}")
    host_network = network_output.strip() == 'host'
    
    # Check for security issues
    issues = []
    
    if running_as_root:
        issues.append("Container is running as root")
    
    if sensitive_mounts:
        issues.append(f"Container has sensitive mounts: {', '.join(sensitive_mounts)}")
    
    if capabilities and any(cap in ['SYS_ADMIN', 'ALL'] for cap in capabilities):
        issues.append(f"Container has dangerous capabilities: {', '.join(capabilities)}")
    
    if host_network:
        issues.append("Container is using host network")
    
    return {
        'running_as_root': running_as_root,
        'sensitive_mounts': sensitive_mounts,
        'capabilities': capabilities,
        'host_network': host_network,
        'issues': issues
    }

def check_api_security(client, container_id, container_name, category):
    """Check API security configuration for a container."""
    # Get container IP
    container_ip = execute_command(client, f"docker inspect -f '{{{{.NetworkSettings.IPAddress}}}}' {container_id}")
    
    if not container_ip or not container_ip.strip():
        # Try to get IP from networks
        networks_output = execute_command(client, f"docker inspect -f '{{{{json .NetworkSettings.Networks}}}}' {container_id}")
        
        if networks_output:
            try:
                networks = json.loads(networks_output.strip().strip("'"))
                for network in networks.values():
                    if 'IPAddress' in network and network['IPAddress']:
                        container_ip = network['IPAddress']
                        break
            except:
                pass
    
    if not container_ip or not container_ip.strip():
        return {
            'issues': ["Could not determine container IP"]
        }
    
    container_ip = container_ip.strip()
    
    # Check if API requires authentication
    auth_required = False
    auth_endpoints = []
    
    # Define endpoints to test based on category
    if category == 'renum':
        endpoints = [
            {'path': '/api/v1/rag/search', 'method': 'POST'},
            {'path': '/api/v1/auth/me', 'method': 'GET'}
        ]
    elif category == 'suna':
        endpoints = [
            {'path': '/api/agent/status', 'method': 'GET'},
            {'path': '/api/agent/list', 'method': 'GET'}
        ]
    else:
        endpoints = []
    
    # Test endpoints
    for endpoint in endpoints:
        path = endpoint['path']
        method = endpoint['method']
        url = f"http://{container_ip}:8000{path}"
        
        # Use curl to check if authentication is required
        command = f"docker exec {container_id} curl -s -o /dev/null -w '%{{http_code}}' -X {method} {url}"
        status_code = execute_command(client, command).strip()
        
        if status_code in ['401', '403']:
            auth_required = True
            auth_endpoints.append(path)
    
    # Check for HTTPS
    https_enabled = False
    env_vars = get_container_env_vars(client, container_id)
    
    if any('HTTPS' in key and value.lower() in ['true', '1', 'yes'] for key, value in env_vars.items()):
        https_enabled = True
    
    # Check for issues
    issues = []
    
    if not auth_required and endpoints:
        issues.append("API does not require authentication")
    
    if not https_enabled:
        issues.append("HTTPS is not enabled")
    
    return {
        'auth_required': auth_required,
        'auth_endpoints': auth_endpoints,
        'https_enabled': https_enabled,
        'issues': issues
    }

def analyze_security_config(firewall_config, open_ports, ssh_config, docker_security, container_security, api_security):
    """Analyze security configuration."""
    analysis = {
        'firewall_active': firewall_config['firewall_active'],
        'open_ports': len(open_ports['open_ports']),
        'ssh_issues': len(ssh_config['issues']),
        'docker_issues': len(docker_security['issues']),
        'container_issues': sum(len(security['issues']) for security in container_security.values()),
        'api_issues': sum(len(security['issues']) for security in api_security.values()),
        'issues': [],
        'status': 'OK'
    }
    
    # Check for firewall issues
    if not analysis['firewall_active']:
        analysis['issues'].append("Firewall não está ativo")
        analysis['status'] = 'WARNING'
    
    # Check for SSH issues
    if analysis['ssh_issues'] > 0:
        analysis['issues'].append(f"{analysis['ssh_issues']} problemas de segurança no SSH")
        analysis['status'] = 'WARNING'
    
    # Check for Docker issues
    if analysis['docker_issues'] > 0:
        analysis['issues'].append(f"{analysis['docker_issues']} problemas de segurança no Docker")
        analysis['status'] = 'WARNING'
    
    # Check for container issues
    if analysis['container_issues'] > 0:
        analysis['issues'].append(f"{analysis['container_issues']} problemas de segurança nos contêineres")
        analysis['status'] = 'WARNING'
    
    # Check for API issues
    if analysis['api_issues'] > 0:
        analysis['issues'].append(f"{analysis['api_issues']} problemas de segurança nas APIs")
        analysis['status'] = 'WARNING'
    
    # Check for critical ports
    critical_ports = [22, 80, 443, 3306, 5432, 6379, 27017]
    exposed_critical_ports = [port for port in open_ports['open_ports'] if port in critical_ports]
    
    if exposed_critical_ports:
        analysis['issues'].append(f"Portas críticas expostas: {', '.join(map(str, exposed_critical_ports))}")
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
    
    # Filter for running containers
    running_containers = [c for c in containers if c['is_running']]
    
    if not running_containers:
        print("❌ Nenhum contêiner em execução encontrado")
        client.close()
        sys.exit(1)
    
    # Check firewall configuration
    print("Verificando configuração de firewall...")
    firewall_config = check_firewall_config(client)
    save_to_file(firewall_config, os.path.join(args.output_dir, 'firewall_config.json'))
    
    # Check open ports
    print("Verificando portas abertas...")
    open_ports = check_open_ports(client)
    save_to_file(open_ports, os.path.join(args.output_dir, 'open_ports.json'))
    
    # Check SSH configuration
    print("Verificando configuração de SSH...")
    ssh_config = check_ssh_config(client)
    save_to_file(ssh_config, os.path.join(args.output_dir, 'ssh_config.json'))
    
    # Check Docker security
    print("Verificando segurança do Docker...")
    docker_security = check_docker_security(client)
    save_to_file(docker_security, os.path.join(args.output_dir, 'docker_security.json'))
    
    # Check container security
    print("Verificando segurança dos contêineres...")
    container_security = {}
    for container in running_containers:
        container_id = container['id']
        container_name = container['name']
        
        security = check_container_security(client, container_id, container_name)
        container_security[container_name] = security
        save_to_file(security, os.path.join(args.output_dir, f'{container_name}_security.json'))
    
    # Check API security
    print("Verificando segurança das APIs...")
    api_security = {}
    for container in running_containers:
        if container['category'] in ['renum', 'suna']:
            container_id = container['id']
            container_name = container['name']
            category = container['category']
            
            security = check_api_security(client, container_id, container_name, category)
            api_security[container_name] = security
            save_to_file(security, os.path.join(args.output_dir, f'{container_name}_api_security.json'))
    
    # Analyze security configuration
    security_analysis = analyze_security_config(
        firewall_config,
        open_ports,
        ssh_config,
        docker_security,
        container_security,
        api_security
    )
    save_to_file(security_analysis, os.path.join(args.output_dir, 'security_analysis.json'))
    
    # Generate summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'firewall_active': security_analysis['firewall_active'],
        'open_ports': security_analysis['open_ports'],
        'ssh_issues': security_analysis['ssh_issues'],
        'docker_issues': security_analysis['docker_issues'],
        'container_issues': security_analysis['container_issues'],
        'api_issues': security_analysis['api_issues'],
        'status': security_analysis['status'],
        'issues': security_analysis['issues']
    }
    
    save_to_file(summary, os.path.join(args.output_dir, 'security_summary.json'))
    
    # Generate text report
    report = f"""
=======================================================
RELATÓRIO DE SEGURANÇA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

Firewall ativo: {'✅ Sim' if security_analysis['firewall_active'] else '❌ Não'}
Portas abertas: {security_analysis['open_ports']}
Problemas de segurança no SSH: {security_analysis['ssh_issues']}
Problemas de segurança no Docker: {security_analysis['docker_issues']}
Problemas de segurança nos contêineres: {security_analysis['container_issues']}
Problemas de segurança nas APIs: {security_analysis['api_issues']}

Status: {security_analysis['status']}

"""
    
    # Add details about firewall
    report += "CONFIGURAÇÃO DE FIREWALL:\n"
    if firewall_config['firewall_active']:
        report += "✅ Firewall está ativo\n"
    else:
        report += "❌ Firewall não está ativo\n"
    
    # Add details about open ports
    report += "\nPORTAS ABERTAS:\n"
    for port in open_ports['open_ports']:
        service = ""
        if port == 22:
            service = "(SSH)"
        elif port == 80:
            service = "(HTTP)"
        elif port == 443:
            service = "(HTTPS)"
        elif port == 3306:
            service = "(MySQL)"
        elif port == 5432:
            service = "(PostgreSQL)"
        elif port == 6379:
            service = "(Redis)"
        elif port == 27017:
            service = "(MongoDB)"
        
        report += f"- {port} {service}\n"
    
    # Add details about SSH issues
    if ssh_config['issues']:
        report += "\nPROBLEMAS DE SEGURANÇA NO SSH:\n"
        for issue in ssh_config['issues']:
            report += f"- {issue}\n"
    
    # Add details about Docker security issues
    if docker_security['issues']:
        report += "\nPROBLEMAS DE SEGURANÇA NO DOCKER:\n"
        for issue in docker_security['issues']:
            report += f"- {issue}\n"
    
    # Add details about container security issues
    container_issues_found = False
    for container_name, security in container_security.items():
        if security['issues']:
            if not container_issues_found:
                report += "\nPROBLEMAS DE SEGURANÇA NOS CONTÊINERES:\n"
                container_issues_found = True
            
            report += f"\n{container_name}:\n"
            for issue in security['issues']:
                report += f"- {issue}\n"
    
    # Add details about API security issues
    api_issues_found = False
    for container_name, security in api_security.items():
        if security['issues']:
            if not api_issues_found:
                report += "\nPROBLEMAS DE SEGURANÇA NAS APIs:\n"
                api_issues_found = True
            
            report += f"\n{container_name}:\n"
            for issue in security['issues']:
                report += f"- {issue}\n"
    
    # Add recommendations
    report += "\nRECOMENDAÇÕES:\n"
    
    if not security_analysis['firewall_active']:
        report += "- Ativar o firewall (ufw ou iptables) e configurar regras para permitir apenas o tráfego necessário\n"
    
    if security_analysis['ssh_issues'] > 0:
        report += "- Desativar login SSH como root\n"
        report += "- Desativar autenticação por senha e usar apenas chaves SSH\n"
        report += "- Alterar a porta padrão do SSH (22) para uma porta não padrão\n"
    
    if security_analysis['docker_issues'] > 0:
        report += "- Restringir permissões do socket Docker (/var/run/docker.sock)\n"
        report += "- Não expor a API Docker na rede\n"
        report += "- Evitar executar contêineres em modo privilegiado\n"
    
    if security_analysis['container_issues'] > 0:
        report += "- Executar contêineres como usuário não-root\n"
        report += "- Evitar montar diretórios sensíveis nos contêineres\n"
        report += "- Limitar capacidades dos contêineres ao mínimo necessário\n"
        report += "- Evitar usar a rede do host nos contêineres\n"
    
    if security_analysis['api_issues'] > 0:
        report += "- Implementar autenticação em todas as APIs\n"
        report += "- Habilitar HTTPS para todas as comunicações\n"
    
    save_to_file(report, os.path.join(args.output_dir, 'security_report.txt'))
    print(report)
    
    client.close()
    print("Conexão SSH encerrada")
    print(f"Verificação de segurança concluída. Resultados salvos em {args.output_dir}")

if __name__ == "__main__":
    main()