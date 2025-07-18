"""
Script para verificar o status de implementação do projeto Renum.

Este script analisa os arquivos do projeto e gera um relatório de status
de implementação, comparando com o plano de desenvolvimento e as tarefas definidas.
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Configuração
TASKS_FILE = ".kiro/specs/supabase-rag-integration/tasks.md"
PLAN_FILE = "plano-desenvolvimento-renum-atualizado.md"
REPORT_FILE = "painel-acompanhamento-renum.md"

# Estrutura para armazenar o status de implementação
class ImplementationStatus:
    def __init__(self):
        self.components = {}
        self.tasks = {}
        self.files = {}
        self.total_tasks = 0
        self.completed_tasks = 0
    
    def add_component(self, name: str, status: str, progress: float, next_steps: str):
        self.components[name] = {
            "status": status,
            "progress": progress,
            "next_steps": next_steps
        }
    
    def add_task(self, id: str, name: str, status: str, evidence: str = ""):
        self.tasks[id] = {
            "name": name,
            "status": status,
            "evidence": evidence
        }
        self.total_tasks += 1
        if status == "completed":
            self.completed_tasks += 1
    
    def add_file(self, path: str, component: str, status: str):
        self.files[path] = {
            "component": component,
            "status": status
        }
    
    def get_overall_progress(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100.0

def parse_tasks_file(file_path: str) -> Dict[str, Any]:
    """Parse the tasks file and extract task status."""
    tasks = {}
    current_section = None
    current_task = None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
            for line in lines:
                # Match section headers
                section_match = re.match(r"^- \[([ x])\] (\d+)\. (.+)$", line)
                if section_match:
                    status = "completed" if section_match.group(1) == "x" else "in_progress"
                    section_id = section_match.group(2)
                    section_name = section_match.group(3)
                    current_section = section_id
                    tasks[section_id] = {
                        "name": section_name,
                        "status": status,
                        "tasks": {}
                    }
                    continue
                
                # Match tasks
                task_match = re.match(r"^  - \[([ x])\] (\d+\.\d+) (.+)$", line)
                if task_match and current_section:
                    status = "completed" if task_match.group(1) == "x" else "in_progress"
                    task_id = task_match.group(2)
                    task_name = task_match.group(3)
                    current_task = task_id
                    tasks[current_section]["tasks"][task_id] = {
                        "name": task_name,
                        "status": status,
                        "requirements": []
                    }
                    continue
                
                # Match requirements
                req_match = re.match(r"^    - _Requisitos: (.+)_$", line)
                if req_match and current_section and current_task:
                    requirements = req_match.group(1).split(", ")
                    tasks[current_section]["tasks"][current_task]["requirements"] = requirements
    
    except Exception as e:
        print(f"Error parsing tasks file: {str(e)}")
    
    return tasks

def parse_plan_file(file_path: str) -> Dict[str, Any]:
    """Parse the plan file and extract component status."""
    components = {}
    current_component = None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
            for line in lines:
                # Match component headers
                component_match = re.match(r"^(\d+)\. \*\*(.+)\*\* (✅|🔄|❌)", line)
                if component_match:
                    component_id = component_match.group(1)
                    component_name = component_match.group(2)
                    status = component_match.group(3)
                    current_component = component_id
                    components[component_id] = {
                        "name": component_name,
                        "status": status,
                        "items": {}
                    }
                    continue
                
                # Match component items
                item_match = re.match(r"^   - (.+) (✅|🔄|❌)$", line)
                if item_match and current_component:
                    item_name = item_match.group(1)
                    status = item_match.group(2)
                    components[current_component]["items"][item_name] = status
    
    except Exception as e:
        print(f"Error parsing plan file: {str(e)}")
    
    return components

def scan_project_files() -> Dict[str, Any]:
    """Scan project files to determine implementation status."""
    files = {}
    
    # Define directories to scan
    dirs_to_scan = [
        "renum-backend/app/models",
        "renum-backend/app/repositories",
        "renum-backend/app/services",
        "renum-backend/app/api",
        "renum-backend/scripts"
    ]
    
    # Scan directories
    for dir_path in dirs_to_scan:
        if os.path.exists(dir_path):
            for root, _, filenames in os.walk(dir_path):
                for filename in filenames:
                    if filename.endswith(".py") or filename.endswith(".sql"):
                        file_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(file_path)
                        files[rel_path] = {
                            "component": determine_component(rel_path),
                            "status": "implemented"
                        }
    
    return files

def determine_component(file_path: str) -> str:
    """Determine which component a file belongs to."""
    if "models" in file_path:
        return "Data Models"
    elif "repositories" in file_path:
        return "Data Access Layer"
    elif "services" in file_path:
        return "Business Logic"
    elif "api" in file_path:
        return "API Layer"
    elif "scripts" in file_path:
        return "Scripts"
    else:
        return "Other"

def generate_report(status: ImplementationStatus, output_file: str):
    """Generate a report of the implementation status."""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Relatório de Status de Implementação do Projeto Renum\n\n")
            f.write(f"Data: {os.popen('date /t').read().strip()}\n\n")
            
            # Overall progress
            overall_progress = status.get_overall_progress()
            f.write(f"## Progresso Geral: {overall_progress:.1f}%\n\n")
            
            # Components status
            f.write("## Status por Componente\n\n")
            f.write("| Componente | Status | Progresso | Próximos Passos |\n")
            f.write("|------------|--------|-----------|----------------|\n")
            
            for name, component in status.components.items():
                f.write(f"| {name} | {component['status']} | {component['progress']:.1f}% | {component['next_steps']} |\n")
            
            # Tasks status
            f.write("\n## Status por Tarefa\n\n")
            f.write("| ID | Tarefa | Status | Evidência |\n")
            f.write("|-------|--------|--------|----------|\n")
            
            for id, task in status.tasks.items():
                f.write(f"| {id} | {task['name']} | {task['status']} | {task['evidence']} |\n")
            
            # Files status
            f.write("\n## Arquivos Implementados\n\n")
            f.write("| Arquivo | Componente | Status |\n")
            f.write("|---------|------------|--------|\n")
            
            for path, file in status.files.items():
                f.write(f"| {path} | {file['component']} | {file['status']} |\n")
            
            f.write("\n## Recomendações\n\n")
            f.write("1. Atualizar o arquivo de tarefas para refletir o status real das implementações\n")
            f.write("2. Priorizar a implementação das tarefas estruturantes ainda faltantes\n")
            f.write("3. Implementar testes unitários e de integração para garantir a qualidade do código\n")
            f.write("4. Manter a documentação atualizada à medida que o código evolui\n")
    
    except Exception as e:
        print(f"Error generating report: {str(e)}")

def main():
    """Main function."""
    print("Verificando status de implementação do projeto Renum...")
    
    # Parse tasks file
    print("Analisando arquivo de tarefas...")
    tasks = parse_tasks_file(TASKS_FILE)
    
    # Parse plan file
    print("Analisando plano de desenvolvimento...")
    components = parse_plan_file(PLAN_FILE)
    
    # Scan project files
    print("Escaneando arquivos do projeto...")
    files = scan_project_files()
    
    # Create implementation status
    status = ImplementationStatus()
    
    # Add components
    for id, component in components.items():
        status.add_component(
            name=component["name"],
            status=component["status"],
            progress=calculate_component_progress(component),
            next_steps=determine_next_steps(component)
        )
    
    # Add tasks
    for section_id, section in tasks.items():
        status.add_task(
            id=section_id,
            name=section["name"],
            status=section["status"],
            evidence=find_evidence(section["name"], files)
        )
        
        for task_id, task in section["tasks"].items():
            status.add_task(
                id=task_id,
                name=task["name"],
                status=task["status"],
                evidence=find_evidence(task["name"], files)
            )
    
    # Add files
    for path, file in files.items():
        status.add_file(
            path=path,
            component=file["component"],
            status=file["status"]
        )
    
    # Generate report
    print("Gerando relatório...")
    generate_report(status, REPORT_FILE)
    
    print(f"Relatório gerado em {REPORT_FILE}")
    print(f"Progresso geral: {status.get_overall_progress():.1f}%")

def calculate_component_progress(component: Dict[str, Any]) -> float:
    """Calculate the progress of a component."""
    if not component["items"]:
        return 100.0 if component["status"] == "✅" else 0.0
    
    total = len(component["items"])
    completed = sum(1 for status in component["items"].values() if status == "✅")
    
    return (completed / total) * 100.0

def determine_next_steps(component: Dict[str, Any]) -> str:
    """Determine the next steps for a component."""
    if component["status"] == "✅":
        return "Concluído"
    
    incomplete_items = [name for name, status in component["items"].items() if status != "✅"]
    
    if incomplete_items:
        return f"Implementar {incomplete_items[0]}"
    else:
        return "Continuar implementação"

def find_evidence(task_name: str, files: Dict[str, Any]) -> str:
    """Find evidence for a task in the project files."""
    keywords = task_name.lower().split()
    
    for path, file in files.items():
        if any(keyword in path.lower() for keyword in keywords):
            return path
    
    return ""

if __name__ == "__main__":
    main()