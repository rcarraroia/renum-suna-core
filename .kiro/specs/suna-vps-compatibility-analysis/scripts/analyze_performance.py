#!/usr/bin/env python3
"""
Script para realizar análise de performance dos serviços Renum e Suna.
Este script coleta métricas de uso de recursos, identifica gargalos de performance e sugere otimizações.
"""

import os
import sys
import json
import argparse
import paramiko
import getpass
import re
import time
from pathlib import Path
from datetime import datetime

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Analyze performance')
    parser.add_argument('--host', default='157.180.39.41', help='VPS hostname or IP address')
    parser.add_argument('--port', type=int, default=22, help='SSH port')
    parser.add_argument('--user', default='root', help='SSH username')
    parser.add_argument('--key-file', help='Path to SSH private key file')
    parser.add_argument('--output-dir', default='./output', help='Directory to save output files')
    parser.add_argument('--containers-file', help='Path to containers JSON file (optional)')
    parser.add_argument('--samples', type=int, default=3, help='Number of performance samples to collect')
    parser.add_argument('--interval', type=int, default=5, help='Interval between samples in seconds')
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

def get_system_resources(client):
    """Get system resources information."""
    # Get CPU info
    cpu_info = execute_command(client, "lscpu")
    
    # Get memory info
    memory_info = execute_command(client, "free -m")
    
    # Get disk usage
    disk_usage = execute_command(client, "df -h")
    
    # Get system load
    system_load = execute_command(client, "uptime")
    
    # Parse CPU count
    cpu_count = 1
    if cpu_info:
        cpu_count_match = re.search(r'CPU\(s\):\s+(\d+)', cpu_info)
        if cpu_count_match:
            cpu_count = int(cpu_count_match.group(1))
    
    # Parse memory total
    memory_total = 0
    if memory_info:
        memory_match = re.search(r'Mem:\s+(\d+)', memory_info)
        if memory_match:
            memory_total = int(memory_match.group(1))
    
    return {
        'cpu_info': cpu_info,
        'cpu_count': cpu_count,
        'memory_info': memory_info,
        'memory_total_mb': memory_total,
        'disk_usage': disk_usage,
        'system_load': system_load
    }

def get_container_stats(client, container_id):
    """Get container stats."""
    output = execute_command(client, f"docker stats {container_id} --no-stream --format '{{{{.CPUPerc}}}},{{{{.MemUsage}}}},{{{{.MemPerc}}}},{{{{.NetIO}}}},{{{{.BlockIO}}}},{{{{.PIDs}}}}'")
    
    if output:
        parts = output.strip().split(',')
        if len(parts) >= 6:
            cpu_perc = parts[0].replace('%', '')
            mem_usage = parts[1]
            mem_perc = parts[2].replace('%', '')
            net_io = parts[3]
            block_io = parts[4]
            pids = parts[5]
            
            # Parse memory usage
            mem_used = 0
            mem_limit = 0
            mem_match = re.search(r'([\d.]+)([A-Za-z]+) / ([\d.]+)([A-Za-z]+)', mem_usage)
            if mem_match:
                mem_used_val = float(mem_match.group(1))
                mem_used_unit = mem_match.group(2)
                mem_limit_val = float(mem_match.group(3))
                mem_limit_unit = mem_match.group(4)
                
                # Convert to MB for comparison
                if mem_used_unit == 'GiB':
                    mem_used = mem_used_val * 1024
                elif mem_used_unit == 'MiB':
                    mem_used = mem_used_val
                
                if mem_limit_unit == 'GiB':
                    mem_limit = mem_limit_val * 1024
                elif mem_limit_unit == 'MiB':
                    mem_limit = mem_limit_val
            
            return {
                'cpu_percent': float(cpu_perc) if cpu_perc else 0,
                'memory_usage': mem_usage,
                'memory_percent': float(mem_perc) if mem_perc else 0,
                'memory_used_mb': mem_used,
                'memory_limit_mb': mem_limit,
                'network_io': net_io,
                'block_io': block_io,
                'pids': int(pids) if pids.isdigit() else 0
            }
    
    return {
        'cpu_percent': 0,
        'memory_usage': '0B / 0B',
        'memory_percent': 0,
        'memory_used_mb': 0,
        'memory_limit_mb': 0,
        'network_io': '0B / 0B',
        'block_io': '0B / 0B',
        'pids': 0
    }

def get_container_top_processes(client, container_id):
    """Get top processes in a container."""
    output = execute_command(client, f"docker exec {container_id} ps aux --sort=-%cpu | head -6")
    
    if output:
        lines = output.strip().split('\n')
        if len(lines) > 1:  # Skip header
            processes = []
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 11:
                    processes.append({
                        'user': parts[0],
                        'pid': parts[1],
                        'cpu_percent': float(parts[2]),
                        'memory_percent': float(parts[3]),
                        'command': ' '.join(parts[10:])
                    })
            return processes
    
    return []

def get_api_response_times(client, container_id, container_name, category):
    """Get API response times for common endpoints."""
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
        return []
    
    container_ip = container_ip.strip()
    
    # Define endpoints to test based on category
    if category == 'renum':
        endpoints = [
            {'path': '/', 'method': 'GET'},
            {'path': '/health', 'method': 'GET'},
            {'path': '/docs', 'method': 'GET'},
            {'path': '/api/v1', 'method': 'GET'}
        ]
    elif category == 'suna':
        endpoints = [
            {'path': '/', 'method': 'GET'},
            {'path': '/health', 'method': 'GET'},
            {'path': '/docs', 'method': 'GET'},
            {'path': '/api/agent/status', 'method': 'GET'}
        ]
    else:
        endpoints = [
            {'path': '/', 'method': 'GET'},
            {'path': '/health', 'method': 'GET'}
        ]
    
    # Test response times
    results = []
    
    for endpoint in endpoints:
        path = endpoint['path']
        method = endpoint['method']
        url = f"http://{container_ip}:8000{path}"
        
        # Use curl to measure response time
        command = f"docker exec {container_id} curl -s -o /dev/null -w '%{{time_total}}' -X {method} {url}"
        response_time = execute_command(client, command)
        
        if response_time and response_time.strip():
            try:
                time_seconds = float(response_time.strip())
                results.append({
                    'endpoint': path,
                    'method': method,
                    'response_time_seconds': time_seconds
                })
            except:
                pass
    
    return results

def collect_performance_samples(client, containers, system_resources, num_samples=3, interval=5):
    """Collect multiple performance samples."""
    samples = []
    
    for i in range(num_samples):
        print(f"Coletando amostra de performance {i+1}/{num_samples}...")
        
        sample = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'load': execute_command(client, "uptime").strip(),
                'memory': execute_command(client, "free -m").strip(),
                'disk_io': execute_command(client, "iostat -x 1 1").strip()
            },
            'containers': {}
        }
        
        # Collect stats for each container
        for container in containers:
            if container['is_running']:
                container_id = container['id']
                container_name = container['name']
                
                stats = get_container_stats(client, container_id)
                sample['containers'][container_name] = stats
        
        samples.append(sample)
        
        # Wait for next sample
        if i < num_samples - 1:
            time.sleep(interval)
    
    return samples

def analyze_performance(system_resources, performance_samples, container_processes, api_response_times):
    """Analyze performance data."""
    analysis = {
        'system': {
            'cpu_count': system_resources['cpu_count'],
            'memory_total_mb': system_resources['memory_total_mb'],
            'high_load': False,
            'memory_pressure': False,
            'disk_pressure': False,
            'issues': []
        },
        'containers': {},
        'api_performance': {},
        'bottlenecks': [],
        'status': 'OK'
    }
    
    # Check system load
    if system_resources.get('system_load'):
        load_match = re.search(r'load average: ([\d.]+), ([\d.]+), ([\d.]+)', system_resources['system_load'])
        if load_match:
            load_1min = float(load_match.group(1))
            load_5min = float(load_match.group(2))
            load_15min = float(load_match.group(3))
            
            # High load is when load average is higher than number of CPUs
            if load_5min > system_resources['cpu_count']:
                analysis['system']['high_load'] = True
                analysis['system']['issues'].append(f"Carga do sistema alta: {load_5min} (limite: {system_resources['cpu_count']})")
    
    # Check memory pressure
    if system_resources.get('memory_info'):
        mem_available_match = re.search(r'available\s+(\d+)', system_resources['memory_info'])
        if mem_available_match:
            mem_available = int(mem_available_match.group(1))
            mem_total = system_resources['memory_total_mb']
            
            # Memory pressure when less than 20% available
            if mem_available < (mem_total * 0.2):
                analysis['system']['memory_pressure'] = True
                analysis['system']['issues'].append(f"Pressão de memória: {mem_available}MB disponível de {mem_total}MB")
    
    # Check disk usage
    if system_resources.get('disk_usage'):
        for line in system_resources['disk_usage'].split('\n'):
            if line.startswith('/dev/') and '%' in line:
                parts = line.split()
                if len(parts) >= 5:
                    usage_percent = int(parts[4].replace('%', ''))
                    if usage_percent > 85:
                        analysis['system']['disk_pressure'] = True
                        analysis['system']['issues'].append(f"Uso de disco alto: {usage_percent}% em {parts[5]}")
    
    # Analyze container performance
    for container_name in performance_samples[0]['containers'].keys():
        container_stats = [sample['containers'][container_name] for sample in performance_samples]
        
        # Calculate averages
        avg_cpu = sum(stat['cpu_percent'] for stat in container_stats) / len(container_stats)
        avg_mem = sum(stat['memory_percent'] for stat in container_stats) / len(container_stats)
        avg_pids = sum(stat['pids'] for stat in container_stats) / len(container_stats)
        
        container_analysis = {
            'avg_cpu_percent': avg_cpu,
            'avg_memory_percent': avg_mem,
            'avg_pids': avg_pids,
            'high_cpu': avg_cpu > 80,
            'high_memory': avg_mem > 80,
            'issues': []
        }
        
        # Check for issues
        if container_analysis['high_cpu']:
            container_analysis['issues'].append(f"Uso de CPU alto: {avg_cpu:.1f}%")
        
        if container_analysis['high_memory']:
            container_analysis['issues'].append(f"Uso de memória alto: {avg_mem:.1f}%")
        
        # Add top processes if available
        if container_name in container_processes:
            container_analysis['top_processes'] = container_processes[container_name]
        
        analysis['containers'][container_name] = container_analysis
    
    # Analyze API response times
    for container_name, response_times in api_response_times.items():
        if response_times:
            slow_endpoints = []
            for endpoint in response_times:
                if endpoint['response_time_seconds'] > 1.0:  # More than 1 second is slow
                    slow_endpoints.append({
                        'endpoint': endpoint['endpoint'],
                        'method': endpoint['method'],
                        'response_time': endpoint['response_time_seconds']
                    })
            
            analysis['api_performance'][container_name] = {
                'endpoints_tested': len(response_times),
                'slow_endpoints': slow_endpoints,
                'has_slow_endpoints': len(slow_endpoints) > 0
            }
    
    # Identify bottlenecks
    if analysis['system']['high_load']:
        analysis['bottlenecks'].append("CPU do sistema")
    
    if analysis['system']['memory_pressure']:
        analysis['bottlenecks'].append("Memória do sistema")
    
    if analysis['system']['disk_pressure']:
        analysis['bottlenecks'].append("Espaço em disco")
    
    for container_name, container_analysis in analysis['containers'].items():
        if container_analysis['high_cpu']:
            analysis['bottlenecks'].append(f"CPU do contêiner {container_name}")
        
        if container_analysis['high_memory']:
            analysis['bottlenecks'].append(f"Memória do contêiner {container_name}")
    
    for container_name, api_perf in analysis['api_performance'].items():
        if api_perf['has_slow_endpoints']:
            analysis['bottlenecks'].append(f"Performance da API do contêiner {container_name}")
    
    # Set overall status
    if analysis['bottlenecks']:
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
    
    # Get system resources
    print("Coletando informações de recursos do sistema...")
    system_resources = get_system_resources(client)
    save_to_file(system_resources, os.path.join(args.output_dir, 'system_resources.json'))
    
    # Collect performance samples
    print(f"Coletando {args.samples} amostras de performance com intervalo de {args.interval} segundos...")
    performance_samples = collect_performance_samples(client, running_containers, system_resources, args.samples, args.interval)
    save_to_file(performance_samples, os.path.join(args.output_dir, 'performance_samples.json'))
    
    # Collect container processes
    print("Coletando processos dos contêineres...")
    container_processes = {}
    for container in running_containers:
        container_id = container['id']
        container_name = container['name']
        
        processes = get_container_top_processes(client, container_id)
        container_processes[container_name] = processes
    
    save_to_file(container_processes, os.path.join(args.output_dir, 'container_processes.json'))
    
    # Collect API response times
    print("Medindo tempos de resposta das APIs...")
    api_response_times = {}
    for container in running_containers:
        if container['category'] in ['renum', 'suna']:
            container_id = container['id']
            container_name = container['name']
            category = container['category']
            
            response_times = get_api_response_times(client, container_id, container_name, category)
            if response_times:
                api_response_times[container_name] = response_times
    
    save_to_file(api_response_times, os.path.join(args.output_dir, 'api_response_times.json'))
    
    # Analyze performance
    print("Analisando dados de performance...")
    performance_analysis = analyze_performance(system_resources, performance_samples, container_processes, api_response_times)
    save_to_file(performance_analysis, os.path.join(args.output_dir, 'performance_analysis.json'))
    
    # Generate summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'system_resources': {
            'cpu_count': system_resources['cpu_count'],
            'memory_total_mb': system_resources['memory_total_mb']
        },
        'containers_analyzed': len(running_containers),
        'performance_samples': len(performance_samples),
        'bottlenecks': performance_analysis['bottlenecks'],
        'status': performance_analysis['status']
    }
    
    save_to_file(summary, os.path.join(args.output_dir, 'performance_summary.json'))
    
    # Generate text report
    report = f"""
=======================================================
RELATÓRIO DE PERFORMANCE - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

RECURSOS DO SISTEMA:
CPUs: {system_resources['cpu_count']}
Memória total: {system_resources['memory_total_mb']} MB

Contêineres analisados: {len(running_containers)}
Amostras de performance: {len(performance_samples)}

Status: {performance_analysis['status']}

"""
    
    # Add system issues
    if performance_analysis['system']['issues']:
        report += "PROBLEMAS DO SISTEMA:\n"
        for issue in performance_analysis['system']['issues']:
            report += f"- {issue}\n"
        report += "\n"
    
    # Add container performance details
    report += "PERFORMANCE DOS CONTÊINERES:\n"
    for container_name, container_analysis in performance_analysis['containers'].items():
        status_icon = "⚠️" if container_analysis['issues'] else "✅"
        report += f"\n{status_icon} {container_name}:\n"
        report += f"  CPU média: {container_analysis['avg_cpu_percent']:.1f}%\n"
        report += f"  Memória média: {container_analysis['avg_memory_percent']:.1f}%\n"
        report += f"  Processos médios: {container_analysis['avg_pids']:.1f}\n"
        
        if container_analysis['issues']:
            report += "  Problemas:\n"
            for issue in container_analysis['issues']:
                report += f"  - {issue}\n"
        
        if 'top_processes' in container_analysis and container_analysis['top_processes']:
            report += "  Processos principais:\n"
            for process in container_analysis['top_processes'][:3]:  # Show top 3
                report += f"  - {process['command']} (CPU: {process['cpu_percent']}%, Mem: {process['memory_percent']}%)\n"
    
    # Add API performance details
    if api_response_times:
        report += "\nPERFORMANCE DAS APIs:\n"
        for container_name, api_perf in performance_analysis['api_performance'].items():
            status_icon = "⚠️" if api_perf['has_slow_endpoints'] else "✅"
            report += f"\n{status_icon} {container_name}:\n"
            report += f"  Endpoints testados: {api_perf['endpoints_tested']}\n"
            
            if api_perf['slow_endpoints']:
                report += "  Endpoints lentos:\n"
                for endpoint in api_perf['slow_endpoints']:
                    report += f"  - {endpoint['method']} {endpoint['endpoint']}: {endpoint['response_time']:.2f}s\n"
    
    # Add bottlenecks
    if performance_analysis['bottlenecks']:
        report += "\nGARGALOS IDENTIFICADOS:\n"
        for bottleneck in performance_analysis['bottlenecks']:
            report += f"- {bottleneck}\n"
    else:
        report += "\nNenhum gargalo significativo identificado.\n"
    
    # Add recommendations
    report += "\nRECOMENDAÇÕES:\n"
    
    if performance_analysis['system']['high_load']:
        report += "- Considerar aumentar o número de CPUs disponíveis para o servidor\n"
        report += "- Verificar processos que estão consumindo muita CPU e otimizá-los\n"
    
    if performance_analysis['system']['memory_pressure']:
        report += "- Aumentar a memória disponível para o servidor\n"
        report += "- Verificar vazamentos de memória em aplicações\n"
    
    if performance_analysis['system']['disk_pressure']:
        report += "- Limpar arquivos desnecessários ou aumentar o espaço em disco\n"
        report += "- Configurar rotação de logs para evitar crescimento excessivo\n"
    
    for container_name, container_analysis in performance_analysis['containers'].items():
        if container_analysis['high_cpu']:
            report += f"- Otimizar o uso de CPU no contêiner {container_name}\n"
            report += f"- Considerar aumentar os limites de CPU para {container_name}\n"
        
        if container_analysis['high_memory']:
            report += f"- Verificar vazamentos de memória no contêiner {container_name}\n"
            report += f"- Aumentar os limites de memória para {container_name}\n"
    
    for container_name, api_perf in performance_analysis['api_performance'].items():
        if api_perf['has_slow_endpoints']:
            report += f"- Otimizar endpoints lentos no contêiner {container_name}\n"
            report += f"- Considerar implementar cache para melhorar tempos de resposta\n"
    
    save_to_file(report, os.path.join(args.output_dir, 'performance_report.txt'))
    print(report)
    
    client.close()
    print("Conexão SSH encerrada")
    print(f"Análise de performance concluída. Resultados salvos em {args.output_dir}")

if __name__ == "__main__":
    main()