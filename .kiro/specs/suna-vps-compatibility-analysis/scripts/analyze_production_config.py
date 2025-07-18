#!/usr/bin/env python3
"""
Script para analisar a configuração de produção e identificar possíveis ajustes.
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
    parser = argparse.ArgumentParser(description='Analyze production configuration')
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

def analyze_system_resources(client):
    """Analyze system resources."""
    print("Analyzing system resources...")
    
    # Get CPU info
    cpu_info = execute_command(client, "lscpu")
    
    # Get memory info
    memory_info = execute_command(client, "free -h")
    
    # Get disk usage
    disk_usage = execute_command(client, "df -h")
    
    # Get system load
    system_load = execute_command(client, "uptime")
    
    # Get running processes
    processes = execute_command(client, "ps aux --sort=-%cpu | head -11")
    
    return {
        'cpu_info': cpu_info,
        'memory_info': memory_info,
        'disk_usage': disk_usage,
        'system_load': system_load,
        'top_processes': processes
    }

def analyze_docker_resources(client):
    """Analyze Docker resources."""
    print("Analyzing Docker resources...")
    
    # Get Docker info
    docker_info = execute_command(client, "docker info")
    
    # Get Docker stats
    docker_stats = execute_command(client, "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}'")
    
    # Get Docker disk usage
    docker_disk = execute_command(client, "docker system df")
    
    return {
        'docker_info': docker_info,
        'docker_stats': docker_stats,
        'docker_disk': docker_disk
    }

def analyze_logs_configuration(client):
    """Analyze logs configuration."""
    print("Analyzing logs configuration...")
    
    # Get Docker logging configuration
    docker_log_config = execute_command(client, "docker info | grep 'Logging Driver'")
    
    # Check log sizes for containers
    log_sizes = execute_command(client, "sudo find /var/lib/docker/containers -name '*-json.log' -exec ls -lh {} \\;")
    
    # Check if log rotation is configured
    log_rotation = execute_command(client, "cat /etc/docker/daemon.json 2>/dev/null || echo 'No daemon.json found'")
    
    return {
        'docker_log_config': docker_log_config,
        'log_sizes': log_sizes,
        'log_rotation': log_rotation
    }

def analyze_backup_configuration(client):
    """Analyze backup configuration."""
    print("Analyzing backup configuration...")
    
    # Check for backup scripts
    backup_scripts = execute_command(client, "find / -name '*backup*' -type f -not -path '*/proc/*' -not -path '*/sys/*' -not -path '*/dev/*' 2>/dev/null | grep -v 'Permission denied' || echo 'No backup scripts found'")
    
    # Check for cron jobs
    cron_jobs = execute_command(client, "crontab -l 2>/dev/null || echo 'No crontab for root'")
    
    # Check for backup directories
    backup_dirs = execute_command(client, "find / -name '*backup*' -type d -not -path '*/proc/*' -not -path '*/sys/*' -not -path '*/dev/*' 2>/dev/null | grep -v 'Permission denied' || echo 'No backup directories found'")
    
    return {
        'backup_scripts': backup_scripts,
        'cron_jobs': cron_jobs,
        'backup_dirs': backup_dirs
    }

def analyze_security_configuration(client):
    """Analyze security configuration."""
    print("Analyzing security configuration...")
    
    # Check for firewall
    firewall = execute_command(client, "ufw status 2>/dev/null || iptables -L -n 2>/dev/null || echo 'No firewall found'")
    
    # Check for open ports
    open_ports = execute_command(client, "netstat -tuln")
    
    # Check for SSH configuration
    ssh_config = execute_command(client, "cat /etc/ssh/sshd_config | grep -v '^#' | grep -v '^$'")
    
    # Check for failed login attempts
    failed_logins = execute_command(client, "grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -10 || echo 'No auth.log found'")
    
    return {
        'firewall': firewall,
        'open_ports': open_ports,
        'ssh_config': ssh_config,
        'failed_logins': failed_logins
    }

def generate_recommendations(analysis):
    """Generate recommendations based on analysis."""
    recommendations = []
    
    # System resources recommendations
    if 'system_resources' in analysis:
        if 'memory_info' in analysis['system_resources'] and 'available' in analysis['system_resources']['memory_info'].lower():
            # Simple check for low memory
            if 'available mem' in analysis['system_resources']['memory_info'].lower():
                memory_lines = analysis['system_resources']['memory_info'].split('\n')
                for line in memory_lines:
                    if 'mem:' in line.lower():
                        parts = line.split()
                        if len(parts) >= 7:
                            total = parts[1]
                            available = parts[6]
                            if 'g' in total.lower() and 'g' in available.lower():
                                try:
                                    total_val = float(total.lower().replace('g', '').replace('i', ''))
                                    avail_val = float(available.lower().replace('g', '').replace('i', ''))
                                    if avail_val / total_val < 0.2:  # Less than 20% available
                                        recommendations.append("Sistema com pouca memória disponível. Considere aumentar a memória ou otimizar o uso de recursos.")
                                except:
                                    pass
        
        if 'disk_usage' in analysis['system_resources']:
            # Check for high disk usage
            disk_lines = analysis['system_resources']['disk_usage'].split('\n')
            for line in disk_lines:
                if '/' in line and '%' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        usage = parts[4].replace('%', '')
                        try:
                            usage_val = int(usage)
                            if usage_val > 80:
                                recommendations.append(f"Alto uso de disco ({usage}%) em {parts[5]}. Considere limpar arquivos desnecessários ou aumentar o espaço em disco.")
                        except:
                            pass
    
    # Docker resources recommendations
    if 'docker_resources' in analysis:
        if 'docker_stats' in analysis['docker_resources']:
            # Check for high CPU usage
            stats_lines = analysis['docker_resources']['docker_stats'].split('\n')
            for line in stats_lines:
                if '%' in line and 'cpu' not in line.lower():  # Skip header
                    parts = line.split()
                    if len(parts) >= 2:
                        cpu_usage = parts[1].replace('%', '')
                        try:
                            cpu_val = float(cpu_usage)
                            if cpu_val > 80:
                                recommendations.append(f"Alto uso de CPU ({cpu_usage}%) no contêiner {parts[0]}. Considere otimizar o código ou aumentar os recursos.")
                        except:
                            pass
        
        if 'docker_disk' in analysis['docker_resources'] and 'space usage' in analysis['docker_resources']['docker_disk'].lower():
            # Check for high Docker disk usage
            if '80%' in analysis['docker_resources']['docker_disk'] or '90%' in analysis['docker_resources']['docker_disk'] or '100%' in analysis['docker_resources']['docker_disk']:
                recommendations.append("Alto uso de disco pelo Docker. Execute 'docker system prune' para limpar recursos não utilizados.")
    
    # Logs recommendations
    if 'logs_configuration' in analysis:
        if 'log_sizes' in analysis['logs_configuration'] and analysis['logs_configuration']['log_sizes']:
            # Check for large log files
            log_lines = analysis['logs_configuration']['log_sizes'].split('\n')
            large_logs = False
            for line in log_lines:
                if 'G' in line:  # Log file larger than 1GB
                    large_logs = True
                    break
            
            if large_logs:
                recommendations.append("Arquivos de log muito grandes detectados. Configure a rotação de logs no Docker para evitar o consumo excessivo de disco.")
        
        if 'log_rotation' in analysis['logs_configuration'] and 'no daemon.json found' in analysis['logs_configuration']['log_rotation'].lower():
            recommendations.append("Rotação de logs do Docker não configurada. Crie o arquivo /etc/docker/daemon.json com configurações de log-driver e log-opts.")
    
    # Backup recommendations
    if 'backup_configuration' in analysis:
        if 'backup_scripts' in analysis['backup_configuration'] and 'no backup scripts found' in analysis['backup_configuration']['backup_scripts'].lower():
            recommendations.append("Nenhum script de backup encontrado. Implemente uma estratégia de backup para dados críticos.")
        
        if 'cron_jobs' in analysis['backup_configuration'] and 'backup' not in analysis['backup_configuration']['cron_jobs'].lower():
            recommendations.append("Nenhum job de cron para backup encontrado. Configure backups automáticos regulares.")
    
    # Security recommendations
    if 'security_configuration' in analysis:
        if 'firewall' in analysis['security_configuration'] and 'no firewall found' in analysis['security_configuration']['firewall'].lower():
            recommendations.append("Nenhum firewall detectado. Instale e configure ufw ou iptables para proteger o servidor.")
        
        if 'open_ports' in analysis['security_configuration']:
            # Check for unnecessary open ports
            open_ports_lines = analysis['security_configuration']['open_ports'].split('\n')
            open_ports_count = 0
            for line in open_ports_lines:
                if '0.0.0.0' in line and 'LISTEN' in line:
                    open_ports_count += 1
            
            if open_ports_count > 5:  # Arbitrary threshold
                recommendations.append(f"Muitas portas abertas ({open_ports_count}). Revise e feche portas desnecessárias.")
        
        if 'ssh_config' in analysis['security_configuration'] and 'permitrootlogin yes' in analysis['security_configuration']['ssh_config'].lower():
            recommendations.append("Login SSH como root está permitido. Considere desabilitar o login root e usar um usuário normal com sudo.")
        
        if 'failed_logins' in analysis['security_configuration'] and analysis['security_configuration']['failed_logins'] and 'no auth.log found' not in analysis['security_configuration']['failed_logins'].lower():
            failed_count = len(analysis['security_configuration']['failed_logins'].split('\n'))
            if failed_count > 5:
                recommendations.append(f"Detectadas {failed_count} tentativas de login SSH com falha. Considere instalar fail2ban para proteção contra força bruta.")
    
    return recommendations

def save_to_file(data, filename):
    """Save data to a file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if isinstance(data, dict):
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
        
        # Analyze system resources
        system_resources = analyze_system_resources(client)
        save_to_file(system_resources, os.path.join(args.output_dir, 'system_resources.json'))
        
        # Analyze Docker resources
        docker_resources = analyze_docker_resources(client)
        save_to_file(docker_resources, os.path.join(args.output_dir, 'docker_resources.json'))
        
        # Analyze logs configuration
        logs_configuration = analyze_logs_configuration(client)
        save_to_file(logs_configuration, os.path.join(args.output_dir, 'logs_configuration.json'))
        
        # Analyze backup configuration
        backup_configuration = analyze_backup_configuration(client)
        save_to_file(backup_configuration, os.path.join(args.output_dir, 'backup_configuration.json'))
        
        # Analyze security configuration
        security_configuration = analyze_security_configuration(client)
        save_to_file(security_configuration, os.path.join(args.output_dir, 'security_configuration.json'))
        
        # Combine all analyses
        analysis = {
            'system_resources': system_resources,
            'docker_resources': docker_resources,
            'logs_configuration': logs_configuration,
            'backup_configuration': backup_configuration,
            'security_configuration': security_configuration,
            'timestamp': datetime.now().isoformat()
        }
        
        # Generate recommendations
        recommendations = generate_recommendations(analysis)
        analysis['recommendations'] = recommendations
        
        # Save full analysis
        save_to_file(analysis, os.path.join(args.output_dir, 'full_analysis.json'))
        
        # Save recommendations separately
        save_to_file('\n'.join([f"- {r}" for r in recommendations]), os.path.join(args.output_dir, 'recommendations.txt'))
        
        client.close()
        print("SSH connection closed")
        print(f"Analysis completed and results saved to {args.output_dir}")
        
        if recommendations:
            print("\nRecommendations:")
            for i, recommendation in enumerate(recommendations, 1):
                print(f"{i}. {recommendation}")

if __name__ == "__main__":
    main()