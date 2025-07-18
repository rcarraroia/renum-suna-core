#!/usr/bin/env python3
"""
Script para testar a disponibilidade das APIs REST do Renum e Suna.
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
    parser = argparse.ArgumentParser(description='Test API endpoints')
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

def get_exposed_ports(client):
    """Get exposed ports from Docker containers."""
    output = execute_command(client, "docker ps --format '{{.Names}},{{.Ports}}'")
    ports = {}
    
    if output:
        for line in output.strip().split('\n'):
            if line and ',' in line:
                name, port_mappings = line.split(',', 1)
                ports[name] = port_mappings
    
    return ports

def discover_api_endpoints(client, container):
    """Discover API endpoints from a container."""
    # Try to get OpenAPI documentation
    print(f"Discovering API endpoints for container {container}...")
    
    # First, try to get the port mapping for the container
    port_output = execute_command(client, f"docker port {container}")
    
    if not port_output:
        print(f"No port mappings found for container {container}")
        return None
    
    # Parse port mappings
    port_mappings = {}
    for line in port_output.strip().split('\n'):
        if '->' in line:
            container_port, host_mapping = line.split('->', 1)
            container_port = container_port.strip()
            host_mapping = host_mapping.strip()
            port_mappings[container_port] = host_mapping
    
    # Try common API ports and paths
    api_paths = ['/docs', '/openapi.json', '/swagger', '/api', '/api/v1', '/api/docs']
    discovered_endpoints = {}
    
    for container_port, host_mapping in port_mappings.items():
        if ':' in host_mapping:
            host_ip, host_port = host_mapping.rsplit(':', 1)
            
            for path in api_paths:
                # Try to access the API documentation
                curl_command = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{host_port}{path}"
                status_code = execute_command(client, curl_command).strip()
                
                if status_code and status_code.startswith('2'):  # 2xx status code
                    print(f"Found API endpoint: http://localhost:{host_port}{path} (Status: {status_code})")
                    
                    # Get the actual content
                    content_command = f"curl -s http://localhost:{host_port}{path}"
                    content = execute_command(client, content_command)
                    
                    discovered_endpoints[f"{path} (Port {host_port})"] = {
                        'status_code': status_code,
                        'content': content[:1000] + '...' if content and len(content) > 1000 else content
                    }
    
    return discovered_endpoints

def test_api_endpoints(client, container, endpoints):
    """Test specific API endpoints."""
    # Create a temporary Python script to test the endpoints
    script_content = """
import os
import sys
import json
import requests

def test_endpoints(endpoints):
    results = {}
    
    for endpoint, config in endpoints.items():
        url = config['url']
        method = config.get('method', 'GET')
        headers = config.get('headers', {})
        data = config.get('data')
        
        try:
            print(f"Testing endpoint: {url} ({method})")
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                print(f"Unsupported method: {method}")
                continue
            
            results[endpoint] = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text[:1000] + '...' if len(response.text) > 1000 else response.text
            }
            
            print(f"Status code: {response.status_code}")
        except Exception as e:
            print(f"Error testing endpoint {url}: {str(e)}")
            results[endpoint] = {
                'error': str(e)
            }
    
    return results

# Define endpoints to test
endpoints = {
    endpoints_placeholder
}

if __name__ == "__main__":
    results = test_endpoints(endpoints)
    print(json.dumps(results, indent=2))
"""
    
    # Define endpoints to test based on discovered endpoints
    test_endpoints = {}
    
    # Add discovered endpoints
    for path, info in endpoints.items():
        if 'openapi.json' in path or 'docs' in path:
            url = f"http://localhost:{path.split('Port ')[1].split(')')[0]}{path.split(' (Port ')[0]}"
            test_endpoints[path] = {
                'url': url,
                'method': 'GET',
                'headers': {}
            }
    
    # Add common API endpoints for testing
    port = next(iter(endpoints)).split('Port ')[1].split(')')[0] if endpoints else '8000'
    
    common_endpoints = {
        'health': {
            'url': f'http://localhost:{port}/health',
            'method': 'GET',
            'headers': {}
        },
        'api_root': {
            'url': f'http://localhost:{port}/api',
            'method': 'GET',
            'headers': {}
        }
    }
    
    test_endpoints.update(common_endpoints)
    
    # Replace placeholder in script
    script_content = script_content.replace('endpoints_placeholder', json.dumps(test_endpoints, indent=4))
    
    # Create a temporary file in the container
    temp_script = f"/tmp/test_api_{container}.py"
    execute_command(client, f"docker exec {container} bash -c 'cat > {temp_script} << EOL\n{script_content}\nEOL'")
    
    # Make the script executable
    execute_command(client, f"docker exec {container} chmod +x {temp_script}")
    
    # Run the script
    print(f"Testing API endpoints from container {container}...")
    output = execute_command(client, f"docker exec {container} python {temp_script}")
    
    # Clean up
    execute_command(client, f"docker exec {container} rm {temp_script}")
    
    return output

def save_to_file(data, filename):
    """Save data to a file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write(data if isinstance(data, str) else json.dumps(data, indent=2))

def main():
    """Main function."""
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Connecting to {args.user}@{args.host}:{args.port}...")
    client = create_ssh_client(args.host, args.port, args.user, args.key_file)
    
    if client:
        print("✅ SSH connection established")
        
        # Get exposed ports
        ports = get_exposed_ports(client)
        save_to_file(ports, os.path.join(args.output_dir, 'exposed_ports.json'))
        
        # Get Docker containers
        containers_output = execute_command(client, "docker ps --format '{{.Names}}'")
        containers = containers_output.strip().split('\n') if containers_output else []
        
        # Discover and test API endpoints for each container
        for container in containers:
            if container:
                # Discover API endpoints
                endpoints = discover_api_endpoints(client, container)
                
                if endpoints:
                    save_to_file(endpoints, os.path.join(args.output_dir, f'{container}_discovered_endpoints.json'))
                    
                    # Test API endpoints
                    test_output = test_api_endpoints(client, container, endpoints)
                    save_to_file(test_output, os.path.join(args.output_dir, f'{container}_api_tests.txt'))
                else:
                    print(f"No API endpoints discovered for container {container}")
        
        client.close()
        print("SSH connection closed")
        print(f"All tests completed and results saved to {args.output_dir}")

if __name__ == "__main__":
    main()