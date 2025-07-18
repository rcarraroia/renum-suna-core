#!/usr/bin/env python3
"""
Script para verificar mecanismos de autenticação e autorização dos serviços Renum e Suna.
Este script testa endpoints protegidos, verifica mecanismos de autenticação e valida controle de acesso.
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
    parser = argparse.ArgumentParser(description='Verify authentication and authorization mechanisms')
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

def get_container_ip(client, container_id):
    """Get IP address of a container."""
    # Try to get IP from networks
    output = execute_command(client, f"docker inspect -f '{{{{json .NetworkSettings.Networks}}}}' {container_id}")
    
    if output:
        try:
            # Clean the output (remove extra quotes)
            output = output.strip().strip("'")
            networks = json.loads(output)
            
            # Get the first IP address found
            for network in networks.values():
                if 'IPAddress' in network and network['IPAddress']:
                    return network['IPAddress']
        except json.JSONDecodeError as e:
            print(f"Error parsing network settings: {str(e)}")
    
    # Fallback to direct IP
    output = execute_command(client, f"docker inspect -f '{{{{.NetworkSettings.IPAddress}}}}' {container_id}")
    
    if output and output.strip():
        return output.strip()
    
    return None

def get_api_port(client, container_id):
    """Get API port for a container."""
    # Get exposed ports
    output = execute_command(client, f"docker port {container_id}")
    
    if output:
        # Look for common API ports
        for line in output.strip().split('\n'):
            if '->' in line:
                container_port, host_mapping = line.split('->', 1)
                container_port = container_port.strip()
                
                # Check for common API ports
                if '80/' in container_port or '8000/' in container_port or '8080/' in container_port:
                    return container_port.split('/')[0]
        
        # If no common port found, use the first one
        first_line = output.strip().split('\n')[0]
        if '->' in first_line:
            container_port = first_line.split('->')[0].strip()
            return container_port.split('/')[0]
    
    return None

def test_endpoint_auth(client, container_id, url, method='GET', headers=None, data=None):
    """Test an endpoint with authentication."""
    if headers is None:
        headers = {}
    
    header_args = ' '.join([f'-H "{k}: {v}"' for k, v in headers.items()])
    
    if method == 'GET':
        command = f"docker exec {container_id} curl -s -X GET {header_args} {url}"
    elif method == 'POST':
        if data:
            command = f"docker exec {container_id} curl -s -X POST {header_args} -d '{json.dumps(data)}' {url}"
        else:
            command = f"docker exec {container_id} curl -s -X POST {header_args} {url}"
    else:
        command = f"docker exec {container_id} curl -s -X {method} {header_args} {url}"
    
    # Get response
    response = execute_command(client, command)
    
    # Get status code
    status_command = f"docker exec {container_id} curl -s -o /dev/null -w '%{{http_code}}' -X {method} {header_args} {url}"
    status_code = execute_command(client, status_command).strip()
    
    return {
        'status_code': status_code,
        'response': response
    }

def get_auth_tokens(client, container_id, container_category, base_url):
    """Get authentication tokens for API requests."""
    tokens = {
        'valid_tokens': [],
        'invalid_tokens': ['invalid-token', 'Bearer invalid-token'],
        'login_endpoints': [],
        'auth_methods': []
    }
    
    # Get environment variables
    env_vars = get_container_env_vars(client, container_id)
    
    # Look for API keys in environment variables
    api_key_vars = [
        'API_KEY', 'SUNA_API_KEY', 'RENUM_API_KEY', 'AUTH_TOKEN', 
        'TEST_API_KEY', 'DEV_API_KEY', 'ADMIN_API_KEY'
    ]
    
    for var in api_key_vars:
        if var in env_vars:
            tokens['valid_tokens'].append({
                'type': 'Bearer',
                'token': env_vars[var],
                'source': f'env:{var}'
            })
            tokens['auth_methods'].append('API Key')
    
    # Try to find login endpoints
    login_endpoints = [
        {'path': '/api/v1/auth/login', 'method': 'POST', 'data': {"username": "test@example.com", "password": "password"}},
        {'path': '/api/auth/login', 'method': 'POST', 'data': {"email": "test@example.com", "password": "password"}},
        {'path': '/auth/login', 'method': 'POST', 'data': {"email": "test@example.com", "password": "password"}},
        {'path': '/api/v1/login', 'method': 'POST', 'data': {"username": "test@example.com", "password": "password"}},
        {'path': '/api/login', 'method': 'POST', 'data': {"username": "test@example.com", "password": "password"}},
        {'path': '/login', 'method': 'POST', 'data': {"username": "test@example.com", "password": "password"}}
    ]
    
    for endpoint in login_endpoints:
        url = f"{base_url}{endpoint['path']}"
        response = test_endpoint_auth(client, container_id, url, endpoint['method'], data=endpoint['data'])
        
        if response['status_code'].startswith('2'):
            try:
                response_data = json.loads(response['response'])
                token_fields = ['access_token', 'token', 'jwt', 'auth_token', 'id_token']
                
                for field in token_fields:
                    if field in response_data:
                        tokens['valid_tokens'].append({
                            'type': 'Bearer',
                            'token': response_data[field],
                            'source': f'login:{endpoint["path"]}'
                        })
                        tokens['login_endpoints'].append(endpoint)
                        tokens['auth_methods'].append('JWT/Token Login')
                        break
            except:
                pass
    
    return tokens

def test_auth_mechanisms(client, container_id, container_name, category):
    """Test authentication mechanisms for a container."""
    results = {
        'container_name': container_name,
        'category': category,
        'auth_tokens': None,
        'protected_endpoints': [],
        'unprotected_endpoints': [],
        'auth_methods': [],
        'auth_headers': [],
        'status': 'OK'
    }
    
    # Get container IP
    container_ip = get_container_ip(client, container_id)
    if not container_ip:
        results['status'] = 'ERROR'
        return results
    
    # Get API port
    api_port = get_api_port(client, container_id)
    if not api_port:
        results['status'] = 'ERROR'
        return results
    
    # Base URL for API
    base_url = f"http://{container_ip}:{api_port}"
    
    # Get authentication tokens
    auth_tokens = get_auth_tokens(client, container_id, category, base_url)
    results['auth_tokens'] = auth_tokens
    results['auth_methods'] = auth_tokens['auth_methods']
    
    # Define endpoints to test
    if category == 'renum':
        endpoints_to_test = [
            {'path': '/', 'method': 'GET', 'expected_protected': False},
            {'path': '/health', 'method': 'GET', 'expected_protected': False},
            {'path': '/docs', 'method': 'GET', 'expected_protected': False},
            {'path': '/api/v1', 'method': 'GET', 'expected_protected': False},
            {'path': '/api/v1/rag/search', 'method': 'POST', 'expected_protected': True},
            {'path': '/api/v1/auth/me', 'method': 'GET', 'expected_protected': True},
            {'path': '/api/v1/admin', 'method': 'GET', 'expected_protected': True}
        ]
    elif category == 'suna':
        endpoints_to_test = [
            {'path': '/', 'method': 'GET', 'expected_protected': False},
            {'path': '/health', 'method': 'GET', 'expected_protected': False},
            {'path': '/docs', 'method': 'GET', 'expected_protected': False},
            {'path': '/api/agent/status', 'method': 'GET', 'expected_protected': True},
            {'path': '/api/agent/list', 'method': 'GET', 'expected_protected': True},
            {'path': '/api/agent/create', 'method': 'POST', 'expected_protected': True}
        ]
    else:
        endpoints_to_test = [
            {'path': '/', 'method': 'GET', 'expected_protected': False},
            {'path': '/health', 'method': 'GET', 'expected_protected': False},
            {'path': '/api', 'method': 'GET', 'expected_protected': False}
        ]
    
    # Test each endpoint
    for endpoint in endpoints_to_test:
        path = endpoint['path']
        method = endpoint['method']
        url = f"{base_url}{path}"
        
        # Test without authentication
        no_auth_response = test_endpoint_auth(client, container_id, url, method)
        
        # Test with valid authentication if available
        auth_responses = []
        for token_info in auth_tokens['valid_tokens']:
            if token_info['type'] == 'Bearer':
                headers = {'Authorization': f"Bearer {token_info['token']}"}
                auth_response = test_endpoint_auth(client, container_id, url, method, headers=headers)
                auth_responses.append({
                    'token_source': token_info['source'],
                    'status_code': auth_response['status_code'],
                    'response': auth_response['response']
                })
                
                # Add to auth headers if not already present
                if 'Bearer' not in results['auth_headers']:
                    results['auth_headers'].append('Bearer')
        
        # Test with invalid authentication
        invalid_auth_responses = []
        for invalid_token in auth_tokens['invalid_tokens']:
            if invalid_token.startswith('Bearer'):
                headers = {'Authorization': invalid_token}
            else:
                headers = {'Authorization': f"Bearer {invalid_token}"}
            
            invalid_response = test_endpoint_auth(client, container_id, url, method, headers=headers)
            invalid_auth_responses.append({
                'token': invalid_token,
                'status_code': invalid_response['status_code'],
                'response': invalid_response['response']
            })
        
        # Determine if endpoint is protected
        is_protected = False
        auth_works = False
        
        # Check if unauthenticated request fails with 401/403
        if no_auth_response['status_code'] in ['401', '403']:
            is_protected = True
        
        # Check if authenticated request succeeds
        for auth_response in auth_responses:
            if auth_response['status_code'].startswith('2'):
                auth_works = True
                break
        
        # If unauthenticated request fails but authenticated succeeds, endpoint is protected
        if not no_auth_response['status_code'].startswith('2') and auth_works:
            is_protected = True
        
        # Store result
        endpoint_result = {
            'path': path,
            'method': method,
            'url': url,
            'is_protected': is_protected,
            'expected_protected': endpoint.get('expected_protected', False),
            'no_auth_status': no_auth_response['status_code'],
            'auth_responses': auth_responses,
            'invalid_auth_responses': invalid_auth_responses,
            'auth_works': auth_works,
            'matches_expectation': is_protected == endpoint.get('expected_protected', False)
        }
        
        if is_protected:
            results['protected_endpoints'].append(endpoint_result)
        else:
            results['unprotected_endpoints'].append(endpoint_result)
    
    return results

def analyze_auth_mechanisms(auth_results, category):
    """Analyze authentication mechanisms."""
    analysis = {
        'total_endpoints': len(auth_results['protected_endpoints']) + len(auth_results['unprotected_endpoints']),
        'protected_endpoints': len(auth_results['protected_endpoints']),
        'unprotected_endpoints': len(auth_results['unprotected_endpoints']),
        'auth_methods': auth_results['auth_methods'],
        'auth_headers': auth_results['auth_headers'],
        'has_valid_tokens': len(auth_results['auth_tokens']['valid_tokens']) > 0 if auth_results['auth_tokens'] else False,
        'has_login_endpoints': len(auth_results['auth_tokens']['login_endpoints']) > 0 if auth_results['auth_tokens'] else False,
        'mismatched_protection': sum(1 for e in auth_results['protected_endpoints'] + auth_results['unprotected_endpoints'] if not e['matches_expectation']),
        'issues': [],
        'status': 'OK'
    }
    
    # Check for issues
    if not analysis['has_valid_tokens']:
        analysis['issues'].append("Nenhum token de autenticação válido encontrado")
        analysis['status'] = 'WARNING'
    
    if analysis['protected_endpoints'] == 0:
        analysis['issues'].append("Nenhum endpoint protegido encontrado")
        analysis['status'] = 'WARNING'
    
    if analysis['mismatched_protection'] > 0:
        analysis['issues'].append(f"{analysis['mismatched_protection']} endpoints com proteção diferente do esperado")
        analysis['status'] = 'WARNING'
    
    # Check for expected auth methods based on category
    if category == 'renum':
        if 'JWT/Token Login' not in analysis['auth_methods'] and 'API Key' not in analysis['auth_methods']:
            analysis['issues'].append("Nenhum método de autenticação JWT/Token ou API Key encontrado")
            analysis['status'] = 'WARNING'
    
    elif category == 'suna':
        if 'API Key' not in analysis['auth_methods']:
            analysis['issues'].append("Método de autenticação API Key não encontrado")
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
    
    # Filter for Renum and Suna containers
    relevant_containers = [c for c in containers if c['is_running'] and c['category'] in ['renum', 'suna']]
    
    if not relevant_containers:
        print("❌ Nenhum contêiner Renum ou Suna em execução encontrado")
        client.close()
        sys.exit(1)
    
    # Process each container
    all_auth_results = {}
    all_auth_analyses = {}
    
    for container in relevant_containers:
        container_id = container['id']
        container_name = container['name']
        category = container['category']
        
        print(f"\nVerificando mecanismos de autenticação para: {container_name} ({category})")
        
        # Test authentication mechanisms
        auth_results = test_auth_mechanisms(client, container_id, container_name, category)
        all_auth_results[container_name] = auth_results
        save_to_file(auth_results, os.path.join(args.output_dir, f'{container_name}_auth_mechanisms.json'))
        
        # Analyze authentication mechanisms
        auth_analysis = analyze_auth_mechanisms(auth_results, category)
        all_auth_analyses[container_name] = auth_analysis
        save_to_file(auth_analysis, os.path.join(args.output_dir, f'{container_name}_auth_analysis.json'))
    
    # Generate summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'containers_analyzed': len(relevant_containers),
        'containers_with_auth': sum(1 for analysis in all_auth_analyses.values() if analysis['has_valid_tokens']),
        'total_protected_endpoints': sum(analysis['protected_endpoints'] for analysis in all_auth_analyses.values()),
        'total_unprotected_endpoints': sum(analysis['unprotected_endpoints'] for analysis in all_auth_analyses.values()),
        'auth_methods_found': list(set(method for analysis in all_auth_analyses.values() for method in analysis['auth_methods'])),
        'containers_by_status': {
            'OK': sum(1 for analysis in all_auth_analyses.values() if analysis['status'] == 'OK'),
            'WARNING': sum(1 for analysis in all_auth_analyses.values() if analysis['status'] == 'WARNING'),
            'ERROR': sum(1 for analysis in all_auth_analyses.values() if analysis['status'] == 'ERROR')
        },
        'issues_by_container': {
            name: analysis['issues']
            for name, analysis in all_auth_analyses.items()
            if analysis['issues']
        }
    }
    
    save_to_file(summary, os.path.join(args.output_dir, 'auth_mechanisms_summary.json'))
    
    # Generate text report
    report = f"""
=======================================================
RELATÓRIO DE AUTENTICAÇÃO E AUTORIZAÇÃO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

Contêineres analisados: {summary['containers_analyzed']}
Contêineres com autenticação: {summary['containers_with_auth']}

Total de endpoints protegidos: {summary['total_protected_endpoints']}
Total de endpoints não protegidos: {summary['total_unprotected_endpoints']}

Métodos de autenticação encontrados: {', '.join(summary['auth_methods_found']) if summary['auth_methods_found'] else 'Nenhum'}

Status:
- OK: {summary['containers_by_status']['OK']}
- AVISO: {summary['containers_by_status']['WARNING']}
- ERRO: {summary['containers_by_status']['ERROR']}

"""
    
    # Add details for each container
    for container in relevant_containers:
        container_name = container['name']
        auth_results = all_auth_results.get(container_name, {})
        auth_analysis = all_auth_analyses.get(container_name, {})
        
        status_icon = "✅" if auth_analysis.get('status') == 'OK' else "⚠️" if auth_analysis.get('status') == 'WARNING' else "❌"
        report += f"\n{status_icon} {container_name}:\n"
        
        # Auth details
        report += f"  Métodos de autenticação: {', '.join(auth_analysis.get('auth_methods', [])) if auth_analysis.get('auth_methods') else 'Nenhum'}\n"
        report += f"  Headers de autenticação: {', '.join(auth_analysis.get('auth_headers', [])) if auth_analysis.get('auth_headers') else 'Nenhum'}\n"
        report += f"  Endpoints protegidos: {auth_analysis.get('protected_endpoints', 0)}\n"
        report += f"  Endpoints não protegidos: {auth_analysis.get('unprotected_endpoints', 0)}\n"
        report += f"  Endpoints com proteção diferente do esperado: {auth_analysis.get('mismatched_protection', 0)}\n"
        
        # List tokens
        if auth_results.get('auth_tokens') and auth_results['auth_tokens'].get('valid_tokens'):
            report += "\n  Tokens de autenticação encontrados:\n"
            for token_info in auth_results['auth_tokens']['valid_tokens']:
                report += f"  - Tipo: {token_info['type']}, Fonte: {token_info['source']}\n"
        
        # List protected endpoints
        if auth_results.get('protected_endpoints'):
            report += "\n  Endpoints protegidos:\n"
            for endpoint in auth_results['protected_endpoints']:
                expected = "✅" if endpoint['expected_protected'] else "❌ (Esperado não protegido)"
                report += f"  - {endpoint['method']} {endpoint['path']}: {expected}\n"
        
        # List unprotected endpoints
        if auth_results.get('unprotected_endpoints'):
            report += "\n  Endpoints não protegidos:\n"
            for endpoint in auth_results['unprotected_endpoints']:
                expected = "✅" if not endpoint['expected_protected'] else "❌ (Esperado protegido)"
                report += f"  - {endpoint['method']} {endpoint['path']}: {expected}\n"
        
        # Issues
        if auth_analysis.get('issues'):
            report += "\n  Problemas detectados:\n"
            for issue in auth_analysis['issues']:
                report += f"  - {issue}\n"
    
    # Add recommendations
    report += "\nRECOMENDAÇÕES:\n"
    
    if summary['containers_with_auth'] < summary['containers_analyzed']:
        report += "- Implementar autenticação em todos os contêineres\n"
    
    if summary['total_protected_endpoints'] == 0:
        report += "- Proteger endpoints sensíveis com autenticação\n"
    
    if any('proteção diferente do esperado' in issue for issues in summary['issues_by_container'].values() for issue in issues):
        report += "- Revisar proteção dos endpoints para garantir que endpoints sensíveis estejam protegidos\n"
    
    if any('Método de autenticação' in issue and 'não encontrado' in issue for issues in summary['issues_by_container'].values() for issue in issues):
        report += "- Implementar métodos de autenticação adequados para cada serviço\n"
    
    save_to_file(report, os.path.join(args.output_dir, 'auth_mechanisms_report.txt'))
    print(report)
    
    client.close()
    print("Conexão SSH encerrada")
    print(f"Verificação de mecanismos de autenticação concluída. Resultados salvos em {args.output_dir}")

if __name__ == "__main__":
    main()