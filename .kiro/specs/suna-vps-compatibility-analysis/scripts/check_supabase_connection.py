#!/usr/bin/env python3
"""
Script para verificar a configuração de conexão com o Supabase a partir da VPS.
Este script analisa as variáveis de ambiente de conexão, testa a conexão direta e verifica logs.
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
    parser = argparse.ArgumentParser(description='Check Supabase connection configuration')
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

def get_container_logs(client, container_id, lines=100, filter_text='supabase'):
    """Get filtered logs from a container."""
    output = execute_command(client, f"docker logs --tail {lines} {container_id} | grep -i {filter_text}")
    return output

def test_supabase_connection(client, container_id):
    """Test Supabase connection from a container."""
    # Create a temporary Python script to test the connection
    script_content = """
import os
import sys
import json
try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase-py package not installed")
    sys.exit(1)

def test_connection():
    try:
        # Get Supabase URL and key from environment variables
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        
        if not url or not key:
            print("Error: SUPABASE_URL or SUPABASE_KEY environment variables not set")
            return False
        
        print(f"Connecting to Supabase at {url}")
        
        # Create Supabase client
        supabase: Client = create_client(url, key)
        
        # Test connection by fetching a small amount of data
        response = supabase.table('_test_connection').select('*').limit(1).execute()
        
        # If we get here without an exception, the connection is successful
        print("Supabase connection successful!")
        print(f"Response: {json.dumps(response.model_dump(), indent=2)}")
        return True
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
"""
    
    # Create a temporary file in the container
    temp_script = "/tmp/test_supabase.py"
    execute_command(client, f"docker exec {container_id} bash -c 'cat > {temp_script} << EOL\n{script_content}\nEOL'")
    
    # Make the script executable
    execute_command(client, f"docker exec {container_id} chmod +x {temp_script}")
    
    # Run the script
    print(f"Testing Supabase connection from container {container_id}...")
    output = execute_command(client, f"docker exec {container_id} python {temp_script}")
    
    # Clean up
    execute_command(client, f"docker exec {container_id} rm {temp_script}")
    
    return output

def test_database_connection(client, container_id):
    """Test direct database connection from a container."""
    # Create a temporary Python script to test the connection
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

def test_connection():
    try:
        # Get database connection string from environment variables
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            print("Error: DATABASE_URL environment variable not set")
            return False
        
        print(f"Connecting to database with URL: {db_url.split('@')[1] if '@' in db_url else 'masked'}")
        
        # Connect to the database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test connection by executing a simple query
        cursor.execute("SELECT current_database(), current_user")
        result = cursor.fetchone()
        
        # If we get here without an exception, the connection is successful
        print("Database connection successful!")
        print(f"Connected to database: {result['current_database']} as user: {result['current_user']}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
"""
    
    # Create a temporary file in the container
    temp_script = "/tmp/test_database.py"
    execute_command(client, f"docker exec {container_id} bash -c 'cat > {temp_script} << EOL\n{script_content}\nEOL'")
    
    # Make the script executable
    execute_command(client, f"docker exec {container_id} chmod +x {temp_script}")
    
    # Run the script
    print(f"Testing direct database connection from container {container_id}...")
    output = execute_command(client, f"docker exec {container_id} python {temp_script}")
    
    # Clean up
    execute_command(client, f"docker exec {container_id} rm {temp_script}")
    
    return output

def analyze_supabase_config(env_vars):
    """Analyze Supabase configuration from environment variables."""
    analysis = {
        'has_supabase_url': 'SUPABASE_URL' in env_vars,
        'has_supabase_key': 'SUPABASE_KEY' in env_vars,
        'has_database_url': 'DATABASE_URL' in env_vars,
        'issues': [],
        'status': 'OK'
    }
    
    # Check for missing variables
    if not analysis['has_supabase_url']:
        analysis['issues'].append("SUPABASE_URL não encontrada nas variáveis de ambiente")
        analysis['status'] = 'ERROR'
    
    if not analysis['has_supabase_key']:
        analysis['issues'].append("SUPABASE_KEY não encontrada nas variáveis de ambiente")
        analysis['status'] = 'ERROR'
    
    if not analysis['has_database_url']:
        analysis['issues'].append("DATABASE_URL não encontrada nas variáveis de ambiente")
        analysis['status'] = 'ERROR'
    
    # Check URL format
    if analysis['has_supabase_url']:
        supabase_url = env_vars['SUPABASE_URL']
        if not supabase_url.startswith('https://'):
            analysis['issues'].append("SUPABASE_URL não usa HTTPS")
            analysis['status'] = 'WARNING'
    
    # Check if DATABASE_URL includes SSL parameters
    if analysis['has_database_url']:
        database_url = env_vars['DATABASE_URL']
        if 'sslmode=require' not in database_url and 'sslmode=verify-full' not in database_url:
            analysis['issues'].append("DATABASE_URL não especifica sslmode=require ou sslmode=verify-full")
            analysis['status'] = 'WARNING'
    
    return analysis

def analyze_connection_test(test_output):
    """Analyze Supabase connection test output."""
    analysis = {
        'connection_successful': 'connection successful' in test_output.lower(),
        'error_message': None,
        'status': 'OK'
    }
    
    # Check for errors
    if 'error' in test_output.lower():
        # Extract error message
        error_lines = [line for line in test_output.split('\n') if 'error' in line.lower()]
        if error_lines:
            analysis['error_message'] = error_lines[0]
            analysis['status'] = 'ERROR'
    
    if not analysis['connection_successful']:
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
    all_config_analyses = {}
    all_connection_tests = {}
    all_connection_analyses = {}
    all_database_tests = {}
    all_supabase_logs = {}
    
    for container in relevant_containers:
        container_id = container['id']
        container_name = container['name']
        category = container['category']
        
        print(f"\nAnalisando configuração do Supabase para: {container_name} ({category})")
        
        # Get environment variables
        env_vars = get_container_env_vars(client, container_id)
        all_env_vars[container_name] = env_vars
        save_to_file(env_vars, os.path.join(args.output_dir, f'{container_name}_env_vars.json'))
        
        # Analyze Supabase configuration
        config_analysis = analyze_supabase_config(env_vars)
        all_config_analyses[container_name] = config_analysis
        save_to_file(config_analysis, os.path.join(args.output_dir, f'{container_name}_supabase_config_analysis.json'))
        
        # Test Supabase connection if configuration is present
        if config_analysis['has_supabase_url'] and config_analysis['has_supabase_key']:
            connection_test = test_supabase_connection(client, container_id)
            all_connection_tests[container_name] = connection_test
            save_to_file(connection_test, os.path.join(args.output_dir, f'{container_name}_supabase_connection_test.txt'))
            
            # Analyze connection test
            connection_analysis = analyze_connection_test(connection_test)
            all_connection_analyses[container_name] = connection_analysis
            save_to_file(connection_analysis, os.path.join(args.output_dir, f'{container_name}_supabase_connection_analysis.json'))
        
        # Test direct database connection if configuration is present
        if config_analysis['has_database_url']:
            database_test = test_database_connection(client, container_id)
            all_database_tests[container_name] = database_test
            save_to_file(database_test, os.path.join(args.output_dir, f'{container_name}_database_connection_test.txt'))
        
        # Get Supabase-related logs
        supabase_logs = get_container_logs(client, container_id, filter_text='supabase')
        all_supabase_logs[container_name] = supabase_logs
        save_to_file(supabase_logs, os.path.join(args.output_dir, f'{container_name}_supabase_logs.txt'))
    
    # Generate summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'containers_analyzed': len(relevant_containers),
        'containers_with_supabase_config': sum(1 for analysis in all_config_analyses.values() if analysis['has_supabase_url'] and analysis['has_supabase_key']),
        'containers_with_database_config': sum(1 for analysis in all_config_analyses.values() if analysis['has_database_url']),
        'successful_connections': sum(1 for analysis in all_connection_analyses.values() if analysis['connection_successful']),
        'failed_connections': sum(1 for analysis in all_connection_analyses.values() if not analysis['connection_successful']),
        'containers_by_status': {
            'OK': sum(1 for analysis in all_config_analyses.values() if analysis['status'] == 'OK'),
            'WARNING': sum(1 for analysis in all_config_analyses.values() if analysis['status'] == 'WARNING'),
            'ERROR': sum(1 for analysis in all_config_analyses.values() if analysis['status'] == 'ERROR')
        },
        'issues_by_container': {
            name: {
                'config_issues': analysis['issues'],
                'connection_error': all_connection_analyses.get(name, {}).get('error_message')
            }
            for name, analysis in all_config_analyses.items()
            if analysis['issues'] or (name in all_connection_analyses and not all_connection_analyses[name]['connection_successful'])
        }
    }
    
    save_to_file(summary, os.path.join(args.output_dir, 'supabase_connection_summary.json'))
    
    # Generate text report
    report = f"""
=======================================================
RELATÓRIO DE CONEXÃO COM SUPABASE - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

Contêineres analisados: {summary['containers_analyzed']}
Contêineres com configuração do Supabase: {summary['containers_with_supabase_config']}
Contêineres com configuração de banco de dados: {summary['containers_with_database_config']}

Conexões bem-sucedidas: {summary['successful_connections']}
Conexões com falha: {summary['failed_connections']}

Status:
- OK: {summary['containers_by_status']['OK']}
- AVISO: {summary['containers_by_status']['WARNING']}
- ERRO: {summary['containers_by_status']['ERROR']}

"""
    
    # Add details for each container
    for container in relevant_containers:
        container_name = container['name']
        config_analysis = all_config_analyses.get(container_name, {})
        connection_analysis = all_connection_analyses.get(container_name, {})
        
        status_icon = "✅" if config_analysis.get('status') == 'OK' and connection_analysis.get('connection_successful', False) else "⚠️" if config_analysis.get('status') == 'WARNING' else "❌"
        report += f"\n{status_icon} {container_name}:\n"
        
        # Configuration details
        report += "  Configuração:\n"
        report += f"  - SUPABASE_URL: {'Presente' if config_analysis.get('has_supabase_url', False) else 'Ausente'}\n"
        report += f"  - SUPABASE_KEY: {'Presente' if config_analysis.get('has_supabase_key', False) else 'Ausente'}\n"
        report += f"  - DATABASE_URL: {'Presente' if config_analysis.get('has_database_url', False) else 'Ausente'}\n"
        
        # Connection test results
        if container_name in all_connection_tests:
            connection_status = "Sucesso" if connection_analysis.get('connection_successful', False) else "Falha"
            report += f"  Teste de conexão Supabase: {connection_status}\n"
            
            if not connection_analysis.get('connection_successful', False) and connection_analysis.get('error_message'):
                report += f"  - Erro: {connection_analysis['error_message']}\n"
        
        # Database test results
        if container_name in all_database_tests:
            database_test = all_database_tests[container_name]
            database_success = "connection successful" in database_test.lower()
            database_status = "Sucesso" if database_success else "Falha"
            report += f"  Teste de conexão direta com banco de dados: {database_status}\n"
            
            if not database_success and "error" in database_test.lower():
                error_lines = [line for line in database_test.split('\n') if 'error' in line.lower()]
                if error_lines:
                    report += f"  - Erro: {error_lines[0]}\n"
        
        # Issues
        if config_analysis.get('issues'):
            report += "  Problemas detectados:\n"
            for issue in config_analysis['issues']:
                report += f"  - {issue}\n"
    
    # Add recommendations
    report += "\nRECOMENDAÇÕES:\n"
    
    if summary['containers_with_supabase_config'] < summary['containers_analyzed']:
        report += "- Configurar SUPABASE_URL e SUPABASE_KEY em todos os contêineres que precisam acessar o Supabase\n"
    
    if summary['containers_with_database_config'] < summary['containers_analyzed']:
        report += "- Configurar DATABASE_URL em todos os contêineres que precisam acessar o banco de dados diretamente\n"
    
    if summary['failed_connections'] > 0:
        report += "- Verificar erros de conexão com o Supabase e corrigir problemas de configuração\n"
    
    if summary['containers_by_status']['WARNING'] > 0:
        report += "- Revisar avisos de configuração e considerar melhorias de segurança (como usar HTTPS e SSL)\n"
    
    save_to_file(report, os.path.join(args.output_dir, 'supabase_connection_report.txt'))
    print(report)
    
    client.close()
    print("Conexão SSH encerrada")
    print(f"Análise de conexão com Supabase concluída. Resultados salvos em {args.output_dir}")

if __name__ == "__main__":
    main()