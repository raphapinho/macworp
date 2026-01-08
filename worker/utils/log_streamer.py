"""
Módulo para streaming de logs em tempo real
"""
import subprocess
import threading
import queue
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class LogStreamer:
    """Captura e transmite logs de processos em tempo real"""
    
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        """
        Args:
            callback: Função chamada para cada linha de log capturada
        """
        self.callback = callback or self._default_callback
        self.log_queue = queue.Queue()
        self.process = None
        self.threads = []
        
    def _default_callback(self, line: str):
        """Callback padrão que apenas imprime a linha"""
        print(line, end='')
        
    def _stream_output(self, pipe, prefix=''):
        """Thread que lê o pipe e envia para o callback"""
        try:
            for line in iter(pipe.readline, b''):
                if line:
                    decoded_line = line.decode('utf-8', errors='replace')
                    self.log_queue.put((prefix, decoded_line))
                    self.callback(f"{prefix}{decoded_line}")
        except Exception as e:
            logger.error(f"Erro ao capturar saída: {e}")
        finally:
            pipe.close()
    
    def run_process(self, cmd, cwd=None, env=None):
        """
        Executa processo e captura saída em tempo real
        
        Args:
            cmd: Lista com comando e argumentos
            cwd: Diretório de trabalho
            env: Variáveis de ambiente
            
        Returns:
            Código de retorno do processo
        """
        logger.info(f"Executando: {' '.join(cmd)}")
        
        # Iniciar processo
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            bufsize=1  # Line buffered
        )
        
        # Criar threads para capturar stdout e stderr
        stdout_thread = threading.Thread(
            target=self._stream_output,
            args=(self.process.stdout, '[OUT] ')
        )
        stderr_thread = threading.Thread(
            target=self._stream_output,
            args=(self.process.stderr, '[ERR] ')
        )
        
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        
        stdout_thread.start()
        stderr_thread.start()
        
        self.threads = [stdout_thread, stderr_thread]
        
        # Aguardar conclusão
        returncode = self.process.wait()
        
        # Aguardar threads terminarem
        for thread in self.threads:
            thread.join(timeout=5)
        
        return returncode


class NextflowLogStreamer(LogStreamer):
    """Streaming especializado para Nextflow"""
    
    def __init__(self, websocket_callback=None):
        """
        Args:
            websocket_callback: Função para enviar logs via WebSocket
        """
        super().__init__(callback=self._process_nextflow_line)
        self.websocket_callback = websocket_callback
        self.current_progress = {}
        
    def _process_nextflow_line(self, line: str):
        """Processa linha do Nextflow e extrai informações de progresso"""
        line = line.strip()
        
        # Enviar linha bruta
        if self.websocket_callback:
            self.websocket_callback({
                'type': 'log',
                'message': line
            })
        
        # Extrair informações de progresso
        if 'executor >' in line:
            # Exemplo: "executor >  local (4)"
            self._parse_executor_info(line)
        elif '] process >' in line:
            # Exemplo: "[a2/d4b5c6] process > prepareDatabase [100%] 4 of 4 ✔"
            self._parse_process_info(line)
        
        # Log padrão
        logger.info(line)
    
    def _parse_executor_info(self, line: str):
        """Extrai info do executor"""
        try:
            parts = line.split('executor >')[1].strip()
            if self.websocket_callback:
                self.websocket_callback({
                    'type': 'executor',
                    'info': parts
                })
        except Exception as e:
            logger.debug(f"Erro ao parsear executor: {e}")
    
    def _parse_process_info(self, line: str):
        """Extrai informações de progresso de processos"""
        try:
            # Extrair task ID [a2/d4b5c6]
            task_id = line.split(']')[0].split('[')[1]
            
            # Extrair nome do processo
            process_name = line.split('process >')[1].split('[')[0].strip()
            
            # Extrair percentual e contagem
            if '[' in line and '%]' in line:
                progress_part = line.split('[')[1].split(']')[0]
                percentage = progress_part.replace('%', '').strip()
                
                count_part = line.split(']')[-1].strip()
                
                progress_info = {
                    'type': 'progress',
                    'task_id': task_id,
                    'process': process_name,
                    'percentage': percentage,
                    'status': count_part
                }
                
                self.current_progress[process_name] = progress_info
                
                if self.websocket_callback:
                    self.websocket_callback(progress_info)
                    
        except Exception as e:
            logger.debug(f"Erro ao parsear progresso: {e}")