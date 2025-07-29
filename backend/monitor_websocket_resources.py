#!/usr/bin/env python3
"""
Monitor em tempo real de recursos do sistema para WebSocket
Monitora conexões, uso de recursos e performance
"""

import asyncio
import time
import psutil
import socket
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class WebSocketResourceMonitor:
    """Monitor de recursos para WebSocket"""
    
    def __init__(self, interval: int = 5):
        self.interval = interval
        self.running = False
        self.metrics_history = []
        self.max_history = 100  # Mantém últimas 100 medições
        
    async def start_monitoring(self):
        """Inicia monitoramento contínuo"""
        self.running = True
        print("🔍 MONITOR DE RECURSOS WEBSOCKET INICIADO")
        print("=" * 60)
        print("Pressione Ctrl+C para parar")
        print()
        
        try:
            while self.running:
                metrics = await self.collect_metrics()
                self.display_metrics(metrics)
                self.store_metrics(metrics)
                
                await asyncio.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitor interrompido pelo usuário")
            await self.save_metrics_report()
        except Exception as e:
            print(f"\n❌ Erro no monitor: {e}")
        finally:
            self.running = False
    
    async def collect_metrics(self) -> Dict:
        """Coleta métricas do sistema"""
        timestamp = datetime.now()
        
        # CPU e Memória
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # File descriptors
        try:
            import resource
            fd_soft, fd_hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            fd_used = len(psutil.Process().open_files()) + len(psutil.Process().connections())
        except:
            fd_soft = fd_hard = fd_used = 0
        
        # Conexões de rede
        try:
            connections = psutil.net_connections()
            tcp_connections = len([c for c in connections if c.type == socket.SOCK_STREAM])
            websocket_connections = len([c for c in connections 
                                       if c.laddr and c.laddr.port in [8000, 3000, 8080]])
            listening_sockets = len([c for c in connections if c.status == 'LISTEN'])
        except:
            tcp_connections = websocket_connections = listening_sockets = 0
        
        # Load average (apenas Linux)
        try:
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
        except:
            load_avg = (0, 0, 0)
        
        # Processos
        process_count = len(psutil.pids())
        
        # Rede
        net_io = psutil.net_io_counters()
        
        return {
            'timestamp': timestamp,
            'cpu': {
                'percent': cpu_percent,
                'load_avg': load_avg
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            },
            'file_descriptors': {
                'soft_limit': fd_soft,
                'hard_limit': fd_hard,
                'used': fd_used,
                'usage_percent': (fd_used / fd_soft * 100) if fd_soft > 0 else 0
            },
            'connections': {
                'tcp_total': tcp_connections,
                'websocket': websocket_connections,
                'listening': listening_sockets
            },
            'system': {
                'processes': process_count
            },
            'network': {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        }
    
    def display_metrics(self, metrics: Dict):
        """Exibe métricas na tela"""
        timestamp = metrics['timestamp'].strftime('%H:%M:%S')
        
        # Limpa tela (funciona na maioria dos terminais)
        print('\033[2J\033[H', end='')
        
        print(f"🔍 MONITOR WEBSOCKET - {timestamp}")
        print("=" * 60)
        
        # CPU e Load
        cpu = metrics['cpu']
        print(f"💻 CPU: {cpu['percent']:5.1f}% | Load: {cpu['load_avg'][0]:.2f} {cpu['load_avg'][1]:.2f} {cpu['load_avg'][2]:.2f}")
        
        # Memória
        mem = metrics['memory']
        mem_gb = mem['used'] / (1024**3)
        mem_total_gb = mem['total'] / (1024**3)
        print(f"🧠 RAM: {mem['percent']:5.1f}% | {mem_gb:.1f}GB / {mem_total_gb:.1f}GB")
        
        # File Descriptors
        fd = metrics['file_descriptors']
        fd_status = self.get_status_indicator(fd['usage_percent'], 70, 90)
        print(f"📁 FDs: {fd_status} {fd['used']:4d} / {fd['soft_limit']:5d} ({fd['usage_percent']:5.1f}%)")
        
        # Conexões
        conn = metrics['connections']
        print(f"🌐 Conexões: TCP={conn['tcp_total']:3d} | WebSocket={conn['websocket']:3d} | Listen={conn['listening']:2d}")
        
        # Sistema
        sys_info = metrics['system']
        print(f"⚙️  Processos: {sys_info['processes']:4d}")
        
        # Rede
        net = metrics['network']
        net_mb_sent = net['bytes_sent'] / (1024**2)
        net_mb_recv = net['bytes_recv'] / (1024**2)
        print(f"📡 Rede: ↑{net_mb_sent:.1f}MB ↓{net_mb_recv:.1f}MB | Pacotes: ↑{net['packets_sent']} ↓{net['packets_recv']}")
        
        # Alertas
        alerts = self.check_alerts(metrics)
        if alerts:
            print("\n⚠️  ALERTAS:")
            for alert in alerts:
                print(f"   • {alert}")
        
        print(f"\n🔄 Atualizando a cada {self.interval}s... (Ctrl+C para parar)")
    
    def get_status_indicator(self, value: float, warning_threshold: float, critical_threshold: float) -> str:
        """Retorna indicador de status baseado no valor"""
        if value >= critical_threshold:
            return "🔴"
        elif value >= warning_threshold:
            return "🟡"
        else:
            return "🟢"
    
    def check_alerts(self, metrics: Dict) -> List[str]:
        """Verifica condições de alerta"""
        alerts = []
        
        # CPU alto
        if metrics['cpu']['percent'] > 80:
            alerts.append(f"CPU alta: {metrics['cpu']['percent']:.1f}%")
        
        # Memória alta
        if metrics['memory']['percent'] > 85:
            alerts.append(f"Memória alta: {metrics['memory']['percent']:.1f}%")
        
        # File descriptors
        fd_usage = metrics['file_descriptors']['usage_percent']
        if fd_usage > 90:
            alerts.append(f"File descriptors crítico: {fd_usage:.1f}%")
        elif fd_usage > 70:
            alerts.append(f"File descriptors alto: {fd_usage:.1f}%")
        
        # Muitas conexões WebSocket
        ws_conn = metrics['connections']['websocket']
        if ws_conn > 500:
            alerts.append(f"Muitas conexões WebSocket: {ws_conn}")
        
        # Load average alto (apenas se disponível)
        if metrics['cpu']['load_avg'][0] > 4:
            alerts.append(f"Load average alto: {metrics['cpu']['load_avg'][0]:.2f}")
        
        return alerts
    
    def store_metrics(self, metrics: Dict):
        """Armazena métricas no histórico"""
        # Converte datetime para string para serialização JSON
        metrics_copy = metrics.copy()
        metrics_copy['timestamp'] = metrics['timestamp'].isoformat()
        
        self.metrics_history.append(metrics_copy)
        
        # Mantém apenas as últimas medições
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
    
    async def save_metrics_report(self):
        """Salva relatório de métricas"""
        if not self.metrics_history:
            return
        
        # Calcula estatísticas
        cpu_values = [m['cpu']['percent'] for m in self.metrics_history]
        mem_values = [m['memory']['percent'] for m in self.metrics_history]
        fd_values = [m['file_descriptors']['usage_percent'] for m in self.metrics_history]
        ws_conn_values = [m['connections']['websocket'] for m in self.metrics_history]
        
        stats = {
            'monitoring_duration': len(self.metrics_history) * self.interval,
            'samples_collected': len(self.metrics_history),
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'avg': sum(mem_values) / len(mem_values),
                'max': max(mem_values),
                'min': min(mem_values)
            },
            'file_descriptors': {
                'avg': sum(fd_values) / len(fd_values),
                'max': max(fd_values),
                'min': min(fd_values)
            },
            'websocket_connections': {
                'avg': sum(ws_conn_values) / len(ws_conn_values),
                'max': max(ws_conn_values),
                'min': min(ws_conn_values)
            }
        }
        
        # Salva dados completos
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'raw_data': self.metrics_history
        }
        
        # Salva em JSON
        json_path = f"backend/websocket_monitoring_{int(time.time())}.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Salva relatório legível
        report_path = f"backend/websocket_monitoring_report_{int(time.time())}.txt"
        with open(report_path, 'w') as f:
            f.write("RELATÓRIO DE MONITORAMENTO WEBSOCKET\n")
            f.write("=" * 50 + "\n")
            f.write(f"Duração: {stats['monitoring_duration']} segundos\n")
            f.write(f"Amostras: {stats['samples_collected']}\n")
            f.write(f"Intervalo: {self.interval} segundos\n\n")
            
            f.write("ESTATÍSTICAS:\n")
            f.write("-" * 30 + "\n")
            f.write(f"CPU - Média: {stats['cpu']['avg']:.1f}% | Máx: {stats['cpu']['max']:.1f}% | Mín: {stats['cpu']['min']:.1f}%\n")
            f.write(f"RAM - Média: {stats['memory']['avg']:.1f}% | Máx: {stats['memory']['max']:.1f}% | Mín: {stats['memory']['min']:.1f}%\n")
            f.write(f"FDs - Média: {stats['file_descriptors']['avg']:.1f}% | Máx: {stats['file_descriptors']['max']:.1f}% | Mín: {stats['file_descriptors']['min']:.1f}%\n")
            f.write(f"WebSocket - Média: {stats['websocket_connections']['avg']:.0f} | Máx: {stats['websocket_connections']['max']} | Mín: {stats['websocket_connections']['min']}\n")
        
        print(f"\n📊 Relatório salvo em {report_path}")
        print(f"📊 Dados JSON salvos em {json_path}")
    
    async def run_single_check(self):
        """Executa uma única verificação (não contínua)"""
        print("🔍 VERIFICAÇÃO ÚNICA DE RECURSOS WEBSOCKET")
        print("=" * 50)
        
        metrics = await self.collect_metrics()
        self.display_metrics(metrics)
        
        return metrics


async def main():
    """Função principal"""
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Execução única
        monitor = WebSocketResourceMonitor()
        await monitor.run_single_check()
    else:
        # Monitoramento contínuo
        interval = 5
        if len(sys.argv) > 1:
            try:
                interval = int(sys.argv[1])
            except ValueError:
                print("Uso: python3 monitor_websocket_resources.py [intervalo_segundos] [--once]")
                sys.exit(1)
        
        monitor = WebSocketResourceMonitor(interval)
        await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())