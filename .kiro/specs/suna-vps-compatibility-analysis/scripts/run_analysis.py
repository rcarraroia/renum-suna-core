#!/usr/bin/env python3
"""
Script principal para orquestrar a análise técnica completa do ambiente Suna na VPS.
Este script executa todos os outros scripts de análise em sequência e compila os resultados.
"""

import os
import sys
import json
import argparse
import subprocess
import datetime
from pathlib import Path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run complete technical analysis')
    parser.add_argument('--host', default='157.180.39.41', help='VPS hostname or IP address')
    parser.add_argument('--port', type=int, default=22, help='SSH port')
    parser.add_argument('--user', default='root', help='SSH username')
    parser.add_argument('--key-file', help='Path to SSH private key file')
    parser.add_argument('--output-dir', default='./analysis_results', help='Directory to save output files')
    return parser.parse_args()

def run_script(script_path, args):
    """Run a Python script with arguments."""
    cmd = [sys.executable, script_path]
    
    for key, value in args.items():
        if value is not None:
            cmd.extend([f'--{key}', str(value)])
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing {script_path}: {e}")
        return False

def compile_results(output_dir):
    """Compile results from all analyses into a single report."""
    report = {
        'timestamp': datetime.datetime.now().isoformat(),
        'summary': {},
        'details': {},
        'recommendations': []
    }
    
    # Load recommendations if they exist
    recommendations_file = os.path.join(output_dir, 'recommendations.txt')
    if os.path.exists(recommendations_file):
        with open(recommendations_file, 'r') as f:
            report['recommendations'] = [line.strip() for line in f if line.strip()]
    
    # Check for container information
    containers_file = os.path.join(output_dir, 'containers.json')
    if os.path.exists(containers_file):
        with open(containers_file, 'r') as f:
            containers = json.load(f)
            report['summary']['containers'] = len(containers)
            report['details']['containers'] = containers
    
    # Check for network information
    networks_file = os.path.join(output_dir, 'network_details.json')
    if os.path.exists(networks_file):
        with open(networks_file, 'r') as f:
            networks = json.load(f)
            report['summary']['networks'] = len(networks)
            report['details']['networks'] = networks
    
    # Check for API endpoints
    api_files = [f for f in os.listdir(output_dir) if f.endswith('_discovered_endpoints.json')]
    api_endpoints = {}
    
    for api_file in api_files:
        container_name = api_file.split('_discovered_endpoints.json')[0]
        with open(os.path.join(output_dir, api_file), 'r') as f:
            try:
                endpoints = json.load(f)
                api_endpoints[container_name] = endpoints
            except json.JSONDecodeError:
                api_endpoints[container_name] = "Error parsing JSON"
    
    if api_endpoints:
        report['summary']['api_endpoints'] = sum(len(endpoints) if isinstance(endpoints, dict) else 0 for endpoints in api_endpoints.values())
        report['details']['api_endpoints'] = api_endpoints
    
    # Check for system resources
    system_file = os.path.join(output_dir, 'system_resources.json')
    if os.path.exists(system_file):
        with open(system_file, 'r') as f:
            try:
                system = json.load(f)
                report['details']['system_resources'] = system
            except json.JSONDecodeError:
                report['details']['system_resources'] = "Error parsing JSON"
    
    # Generate summary status
    status_checks = {
        'environment': os.path.exists(containers_file),
        'network': os.path.exists(networks_file),
        'api': bool(api_endpoints),
        'supabase': any(f.endswith('_supabase_connection.txt') for f in os.listdir(output_dir)),
        'system': os.path.exists(system_file)
    }
    
    report['summary']['status'] = {
        check: 'OK' if status else 'Missing' for check, status in status_checks.items()
    }
    
    # Save compiled report
    report_file = os.path.join(output_dir, 'analysis_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate HTML report
    html_report = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Análise Técnica do Ambiente Suna VPS</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .status-ok {{ color: green; }}
            .status-missing {{ color: red; }}
            .section {{ margin-bottom: 20px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }}
            .recommendation {{ background-color: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; }}
        </style>
    </head>
    <body>
        <h1>Relatório de Análise Técnica - Ambiente Suna VPS</h1>
        <p>Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        
        <div class="section">
            <h2>Resumo do Status</h2>
            <ul>
    """
    
    for check, status in report['summary']['status'].items():
        status_class = 'status-ok' if status == 'OK' else 'status-missing'
        html_report += f'<li><strong>{check}:</strong> <span class="{status_class}">{status}</span></li>\n'
    
    html_report += f"""
            </ul>
            <p><strong>Contêineres:</strong> {report['summary'].get('containers', 'N/A')}</p>
            <p><strong>Redes:</strong> {report['summary'].get('networks', 'N/A')}</p>
            <p><strong>Endpoints API:</strong> {report['summary'].get('api_endpoints', 'N/A')}</p>
        </div>
        
        <div class="section">
            <h2>Recomendações</h2>
    """
    
    if report['recommendations']:
        for rec in report['recommendations']:
            html_report += f'<div class="recommendation">{rec}</div>\n'
    else:
        html_report += '<p>Nenhuma recomendação específica.</p>\n'
    
    html_report += """
        </div>
        
        <div class="section">
            <h2>Próximos Passos</h2>
            <ol>
                <li>Revisar as recomendações e implementar as correções necessárias</li>
                <li>Verificar a integração entre Renum e Suna</li>
                <li>Testar a execução de agentes em ambiente de produção</li>
                <li>Monitorar o desempenho do sistema após as correções</li>
            </ol>
        </div>
    </body>
    </html>
    """
    
    html_file = os.path.join(output_dir, 'analysis_report.html')
    with open(html_file, 'w') as f:
        f.write(html_report)
    
    return report_file, html_file

def main():
    """Main function."""
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define scripts to run in order
    scripts = [
        'connect_vps.py',
        'check_docker_containers.py',
        'analyze_environment_variables.py',
        'check_directory_structure.py',
        'check_docker_network.py',
        'test_service_communication.py',
        'validate_ports_endpoints.py',
        'check_supabase_connection.py',
        'validate_ssl_configuration.py',
        'check_vector_functions.py',
        'map_available_endpoints.py',
        'test_endpoint_responses.py',
        'verify_auth_mechanisms.py',
        'analyze_logs_monitoring.py',
        'check_backup_recovery.py',
        'analyze_performance.py',
        'check_security_config.py',
        'analyze_production_config.py',
        'compile_final_report.py'
    ]
    
    # Run each script
    for script in scripts:
        script_path = os.path.join(script_dir, script)
        if os.path.exists(script_path):
            print(f"\n{'='*80}\nExecuting {script}\n{'='*80}")
            
            # Prepare arguments
            script_args = {
                'host': args.host,
                'port': args.port,
                'user': args.user,
                'key_file': args.key_file,
                'output_dir': args.output_dir
            }
            
            # Special case for test_supabase_connection.py which needs a container
            if script == 'test_supabase_connection.py':
                # Try to find a suitable container from previous results
                containers_file = os.path.join(args.output_dir, 'containers.json')
                if os.path.exists(containers_file):
                    try:
                        with open(containers_file, 'r') as f:
                            containers = json.load(f)
                            # Look for Renum or Suna containers
                            for container in containers:
                                if 'renum' in container.get('name', '').lower() or 'suna' in container.get('name', '').lower():
                                    script_args['container'] = container['name']
                                    break
                    except:
                        pass
            
            success = run_script(script_path, script_args)
            if not success:
                print(f"Warning: {script} failed to execute properly")
        else:
            print(f"Warning: Script {script} not found at {script_path}")
    
    # Compile results
    print("\n\nCompiling analysis results...")
    report_file, html_file = compile_results(args.output_dir)
    
    print(f"\nAnalysis complete!")
    print(f"JSON report saved to: {report_file}")
    print(f"HTML report saved to: {html_file}")
    print("\nReview the reports for detailed findings and recommendations.")

if __name__ == "__main__":
    main()