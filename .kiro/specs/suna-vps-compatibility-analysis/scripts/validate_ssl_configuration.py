#!/usr/bin/env python3
"""
Script para validar a configuração SSL para conexão segura com o Supabase.
Este script verifica a presença e validade de certificados SSL e testa a conexão SSL.
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
    parser = argparse.ArgumentParser(description='Validate SSL configuration for Supabase connection')
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

def test_ssl_configuration(client, container_id):
    """Test SSL configuration for Supabase connection."""
    # Create a temporary Python script to test SSL configuration
    script_content = """
import os
import sys
import json
import ssl
import socket
import urllib.parse

def test_ssl():
    try:
        # Get Supabase URL from environment variable
        url = os.environ.get('SUPABASE_URL')
        
        if not url:
            print("Error: SUPABASE_URL environment variable not set")
            return False
        
        # Parse URL to get hostname
        parsed_url = urllib.parse.urlparse(url)
        hostname = parsed_url.netloc
        
        print(f"Testing SSL connection to {hostname}")
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Connect to the server
        with socket.create_connection((hostname, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"SSL connection established with {hostname}")
                print(f"SSL version: {ssock.version()}")
                print(f"Cipher: {ssock.cipher()}")
                cert = ssock.getpeercert()
                print(f"Certificate subject: {dict(x[0] for x in cert['subject'])}")
                print(f"Certificate issuer: {dict(x[0] for x in cert['issuer'])}")
                print(f"Certificate valid from: {cert['notBefore']}")
                print(f"Certificate valid until: {cert['notAfter']}")
                return True
    except Exception as e:
        print(f"Error testing SSL connection: {str(e)}")
        return False

if __name__ == "__main__":
    test_ssl()
"""
    
    # Create a temporary file in the container
    temp_script = "/tmp/test_ssl.py"
    execute_command(client, f"docker exec {container_id} bash -c 'cat > {temp_script} << EOL\n{script_content}\nEOL'")
    
    # Make the script executable
    execute_command(client, f"docker exec {container_id} chmod +x {temp_script}")
    
    # Run the script
    print(f"Testing SSL configuration from container {container_id}...")
    output = execute_command(client, f"docker exec {container_id} python {temp_script}")
    
    # Clean up
    execute_command(client, f"docker exec {container_id} rm {temp_script}")
    
    return output

def test_database_ssl(client, container_id):
    """Test SSL configuration for direct database connection."""
    # Create a temporary Python script to test database SSL
    script_content = """
import os
import sys
import json
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: psycopg2 package not installed")
    sys.exit(1)

def test_ssl():
    try:
        # Get database connection string from environment variables
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            print("Error: DATABASE_URL environment variable not set")
            return False
        
        print(f"Testing database SSL connection")
        
        # Connect to the database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check SSL status
        cursor.execute("SELECT ssl_is_used()")
        ssl_used = cursor.fetchone()['ssl_is_used']
        
        if ssl_used:
            print("Database connection is using SSL")
            
            # Get SSL details
            cursor.execute("SELECT ssl_version(), ssl_cipher()")
            ssl_info = cursor.fetchone()
            print(f"SSL version: {ssl_info['ssl_version']}")
            print(f"SSL cipher: {ssl_info['ssl_cipher']}")
        else:
            print("Database connection is NOT using SSL")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return ssl_used
    except Exception as e:
        print(f"Error testing database SSL: {str(e)}")
        return False

if __name__ == "__main__":
    test_ssl()
"""
    
    # Create a temporary file in the container
    temp_script = "/tmp/test_db_ssl.py"
    execute_command(client, f"docker exec {container_id} bash -c 'cat > {temp_script} << EOL\n{script_content}\nEOL'")
    
    # Make the script executable
    execute_command(client, f"docker exec {container_id} chmod +x {temp_script}")
    
    # Run the script
    print(f"Testing database SSL configuration from container {container_id}...")
    output = execute_command(client, f"docker exec {container_id} python {temp_script}")
    
    # Clean up
    execute_command(client, f"docker exec {container_id} rm {temp_script}")
    
    return output

def check_ssl_certificates(client, container_id):
    """Check for SSL certificates in the container."""
    # Check for common certificate locations
    cert_locations = [
        '/etc/ssl/certs',
        '/usr/local/share/ca-certificates',
        '/etc/pki/tls/certs',
        '/app/certs',
        '/certs'
    ]
    
    results = {}
    
    for location in cert_locations:
        output = execute_command(client, f"docker exec {container_id} ls -la {location} 2>/dev/null || echo 'Directory not found'")
        
        if output and 'Directory not found' not in output:
            results[location] = output
    
    # Check for CA certificates bundle
    ca_bundle = execute_command(client, f"docker exec {container_id} ls -la /etc/ssl/certs/ca-certificates.crt 2>/dev/null || echo 'File not found'")
    
    if ca_bundle and 'File not found' not in ca_bundle:
        results['ca_bundle'] = ca_bundle
    
    return results

def analyze_ssl_test(test_output):
    """Analyze SSL test output."""
    analysis = {
        'ssl_connection_successful': 'SSL connection established' in test_output,
        'ssl_version': None,
        'cipher': None,
        'certificate_valid': False,
        'error_message': None,
        'status': 'OK'
    }
    
    # Extract SSL version
    for line in test_output.split('\n'):
        if 'SSL version:' in line:
            analysis['ssl_version'] = line.split('SSL version:')[1].strip()
        elif 'Cipher:' in line:
            analysis['cipher'] = line.split('Cipher:')[1].strip()
        elif 'Certificate valid until:' in line:
            # Certificate is valid
            analysis['certificate_valid'] = True
    
    # Check for errors
    if 'error' in test_output.lower():
        # Extract error message
        error_lines = [line for line in test_output.split('\n') if 'error' in line.lower()]
        if error_lines:
            analysis['error_message'] = error_lines[0]
            analysis['status'] = 'ERROR'
    
    if not analysis['ssl_connection_successful']:
        analysis['status'] = 'ERROR'
    
    return analysis

def analyze_db_ssl_test(test_output):
    """Analyze database SSL test output."""
    analysis = {
        'ssl_used': 'Database connection is using SSL' in test_output,
        'ssl_version': None,
        'cipher': None,
        'error_message': None,
        'status': 'OK'
    }
    
    # Extract SSL version and cipher
    for line in test_output.split('\n'):
        if 'SSL version:' in line:
            analysis['ssl_version'] = line.split('SSL version:')[1].strip()
        elif 'SSL cipher:' in line:
            analysis['cipher'] = line.split('SSL cipher:')[1].strip()
    
    # Check for errors
    if 'error' in test_output.lower():
        # Extract error message
        error_lines = [line for line in test_output.split('\n') if 'error' in line.lower()]
        if error_lines:
            analysis['error_message'] = error_lines[0]
            analysis['status'] = 'ERROR'
    
    if not analysis['ssl_used']:
        analysis['status'] = 'WARNING'
    
    return analysis

def analyze_ssl_config(env_vars):
    """Analyze SSL configuration from environment variables."""
    analysis = {
        'has_supabase_url': 'SUPABASE_URL' in env_vars,
        'has_database_url': 'DATABASE_URL' in env_vars,
        'supabase_uses_https': False,
        'database_uses_ssl': False,
        'issues': [],
        'status': 'OK'
    }
    
    # Check Supabase URL
    if analysis['has_supabase_url']:
        supabase_url = env_vars['SUPABASE_URL']
        analysis['supabase_uses_https'] = supabase_url.startswith('https://')
        
        if not analysis['supabase_uses_https']:
            analysis['issues'].append("SUPABASE_URL não usa HTTPS")
            analysis['status'] = 'WARNING'
    else:
        analysis['issues'].append("SUPABASE_URL não encontrada nas variáveis de ambiente")
        analysis['status'] = 'ERROR'
    
    # Check DATABASE_URL
    if analysis['has_database_url']:
        database_url = env_vars['DATABASE_URL']
        analysis['database_uses_ssl'] = 'sslmode=require' in database_url or 'sslmode=verify-full' in database_url
        
        if not analysis['database_uses_ssl']:
            analysis['issues'].append("DATABASE_URL não especifica sslmode=require ou sslmode=verify-full")
            analysis['status'] = 'WARNING'
    else:
        analysis['issues'].append("DATABASE_URL não encontrada nas variáveis de ambiente")
        analysis['status'] = 'ERROR'
    
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
    all_env_vars = {}
    all_ssl_configs = {}
    all_ssl_tests = {}
    all_ssl_analyses = {}
    all_db_ssl_tests = {}
    all_db_ssl_analyses = {}
    all_cert_checks = {}
    
    for container in relevant_containers:
        container_id = container['id']
        container_name = container['name']
        category = container['category']
        
        print(f"\nValidando configuração SSL para: {container_name} ({category})")
        
        # Get environment variables
        env_vars = get_container_env_vars(client, container_id)
        all_env_vars[container_name] = env_vars
        
        # Analyze SSL configuration
        ssl_config = analyze_ssl_config(env_vars)
        all_ssl_configs[container_name] = ssl_config
        save_to_file(ssl_config, os.path.join(args.output_dir, f'{container_name}_ssl_config_analysis.json'))
        
        # Test SSL configuration if Supabase URL is present
        if ssl_config['has_supabase_url']:
            ssl_test = test_ssl_configuration(client, container_id)
            all_ssl_tests[container_name] = ssl_test
            save_to_file(ssl_test, os.path.join(args.output_dir, f'{container_name}_ssl_test.txt'))
            
            # Analyze SSL test
            ssl_analysis = analyze_ssl_test(ssl_test)
            all_ssl_analyses[container_name] = ssl_analysis
            save_to_file(ssl_analysis, os.path.join(args.output_dir, f'{container_name}_ssl_analysis.json'))
        
        # Test database SSL if DATABASE_URL is present
        if ssl_config['has_database_url']:
            db_ssl_test = test_database_ssl(client, container_id)
            all_db_ssl_tests[container_name] = db_ssl_test
            save_to_file(db_ssl_test, os.path.join(args.output_dir, f'{container_name}_db_ssl_test.txt'))
            
            # Analyze database SSL test
            db_ssl_analysis = analyze_db_ssl_test(db_ssl_test)
            all_db_ssl_analyses[container_name] = db_ssl_analysis
            save_to_file(db_ssl_analysis, os.path.join(args.output_dir, f'{container_name}_db_ssl_analysis.json'))
        
        # Check for SSL certificates
        cert_check = check_ssl_certificates(client, container_id)
        all_cert_checks[container_name] = cert_check
        save_to_file(cert_check, os.path.join(args.output_dir, f'{container_name}_ssl_certificates.json'))
    
    # Generate summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'containers_analyzed': len(relevant_containers),
        'containers_with_supabase_https': sum(1 for config in all_ssl_configs.values() if config['supabase_uses_https']),
        'containers_with_database_ssl': sum(1 for config in all_ssl_configs.values() if config['database_uses_ssl']),
        'successful_ssl_connections': sum(1 for analysis in all_ssl_analyses.values() if analysis['ssl_connection_successful']),
        'failed_ssl_connections': sum(1 for analysis in all_ssl_analyses.values() if not analysis['ssl_connection_successful']),
        'databases_using_ssl': sum(1 for analysis in all_db_ssl_analyses.values() if analysis['ssl_used']),
        'databases_not_using_ssl': sum(1 for analysis in all_db_ssl_analyses.values() if not analysis['ssl_used']),
        'containers_by_status': {
            'OK': sum(1 for config in all_ssl_configs.values() if config['status'] == 'OK'),
            'WARNING': sum(1 for config in all_ssl_configs.values() if config['status'] == 'WARNING'),
            'ERROR': sum(1 for config in all_ssl_configs.values() if config['status'] == 'ERROR')
        },
        'issues_by_container': {
            name: {
                'config_issues': config['issues'],
                'ssl_error': all_ssl_analyses.get(name, {}).get('error_message'),
                'db_ssl_error': all_db_ssl_analyses.get(name, {}).get('error_message')
            }
            for name, config in all_ssl_configs.items()
            if config['issues'] or 
               (name in all_ssl_analyses and all_ssl_analyses[name].get('error_message')) or
               (name in all_db_ssl_analyses and all_db_ssl_analyses[name].get('error_message'))
        }
    }
    
    save_to_file(summary, os.path.join(args.output_dir, 'ssl_validation_summary.json'))
    
    # Generate text report
    report = f"""
=======================================================
RELATÓRIO DE CONFIGURAÇÃO SSL - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

Contêineres analisados: {summary['containers_analyzed']}
Contêineres usando HTTPS para Supabase: {summary['containers_with_supabase_https']}
Contêineres usando SSL para banco de dados: {summary['containers_with_database_ssl']}

Conexões SSL bem-sucedidas: {summary['successful_ssl_connections']}
Conexões SSL com falha: {summary['failed_ssl_connections']}

Bancos de dados usando SSL: {summary['databases_using_ssl']}
Bancos de dados sem SSL: {summary['databases_not_using_ssl']}

Status:
- OK: {summary['containers_by_status']['OK']}
- AVISO: {summary['containers_by_status']['WARNING']}
- ERRO: {summary['containers_by_status']['ERROR']}

"""
    
    # Add details for each container
    for container in relevant_containers:
        container_name = container['name']
        ssl_config = all_ssl_configs.get(container_name, {})
        ssl_analysis = all_ssl_analyses.get(container_name, {})
        db_ssl_analysis = all_db_ssl_analyses.get(container_name, {})
        
        status_icon = "✅" if ssl_config.get('status') == 'OK' else "⚠️" if ssl_config.get('status') == 'WARNING' else "❌"
        report += f"\n{status_icon} {container_name}:\n"
        
        # Configuration details
        report += "  Configuração:\n"
        report += f"  - SUPABASE_URL usa HTTPS: {'Sim' if ssl_config.get('supabase_uses_https', False) else 'Não'}\n"
        report += f"  - DATABASE_URL usa SSL: {'Sim' if ssl_config.get('database_uses_ssl', False) else 'Não'}\n"
        
        # SSL test results
        if container_name in all_ssl_tests:
            ssl_status = "Sucesso" if ssl_analysis.get('ssl_connection_successful', False) else "Falha"
            report += f"  Teste de conexão SSL com Supabase: {ssl_status}\n"
            
            if ssl_analysis.get('ssl_connection_successful', False):
                report += f"  - Versão SSL: {ssl_analysis.get('ssl_version', 'N/A')}\n"
                report += f"  - Cifra: {ssl_analysis.get('cipher', 'N/A')}\n"
            
            if not ssl_analysis.get('ssl_connection_successful', False) and ssl_analysis.get('error_message'):
                report += f"  - Erro: {ssl_analysis['error_message']}\n"
        
        # Database SSL test results
        if container_name in all_db_ssl_tests:
            db_ssl_status = "Sim" if db_ssl_analysis.get('ssl_used', False) else "Não"
            report += f"  Banco de dados usa SSL: {db_ssl_status}\n"
            
            if db_ssl_analysis.get('ssl_used', False):
                report += f"  - Versão SSL: {db_ssl_analysis.get('ssl_version', 'N/A')}\n"
                report += f"  - Cifra: {db_ssl_analysis.get('cipher', 'N/A')}\n"
            
            if db_ssl_analysis.get('error_message'):
                report += f"  - Erro: {db_ssl_analysis['error_message']}\n"
        
        # Certificate check results
        if container_name in all_cert_checks:
            cert_check = all_cert_checks[container_name]
            if cert_check:
                report += "  Certificados SSL encontrados:\n"
                for location in cert_check.keys():
                    report += f"  - {location}\n"
            else:
                report += "  Nenhum certificado SSL encontrado\n"
        
        # Issues
        if ssl_config.get('issues'):
            report += "  Problemas detectados:\n"
            for issue in ssl_config['issues']:
                report += f"  - {issue}\n"
    
    # Add recommendations
    report += "\nRECOMENDAÇÕES:\n"
    
    if summary['containers_with_supabase_https'] < summary['containers_analyzed']:
        report += "- Configurar SUPABASE_URL para usar HTTPS em todos os contêineres\n"
    
    if summary['containers_with_database_ssl'] < summary['containers_analyzed']:
        report += "- Configurar DATABASE_URL para usar SSL (sslmode=require) em todos os contêineres\n"
    
    if summary['failed_ssl_connections'] > 0:
        report += "- Verificar erros de conexão SSL e corrigir problemas de configuração\n"
    
    if summary['databases_not_using_ssl'] > 0:
        report += "- Configurar conexões de banco de dados para usar SSL\n"
    
    save_to_file(report, os.path.join(args.output_dir, 'ssl_validation_report.txt'))
    print(report)
    
    client.close()
    print("Conexão SSH encerrada")
    print(f"Validação de configuração SSL concluída. Resultados salvos em {args.output_dir}")

if __name__ == "__main__":
    main()