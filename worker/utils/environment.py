"""
Utilitários para gerenciamento de ambientes conda/micromamba
"""
import subprocess
import logging
import os

logger = logging.getLogger(__name__)


def activate_micromamba_env(env_name: str = "viralflow") -> dict:
    """
    Retorna variáveis de ambiente com micromamba ativado.
    
    Args:
        env_name: Nome do ambiente micromamba a ativar
        
    Returns:
        dict: Dicionário com variáveis de ambiente atualizadas
    """
    env = os.environ.copy()
    
    try:
        # Obter o caminho do ambiente
        result = subprocess.run(
            ["micromamba", "env", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Procurar o ambiente na saída
        for line in result.stdout.split('\n'):
            if env_name in line and not line.strip().startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    env_path = parts[-1]
                    logger.info(f"Ambiente {env_name} encontrado em: {env_path}")
                    
                    # Atualizar PATH
                    env['PATH'] = f"{env_path}/bin:{env.get('PATH', '')}"
                    
                    # Adicionar variáveis conda
                    env['CONDA_DEFAULT_ENV'] = env_name
                    env['CONDA_PREFIX'] = env_path
                    
                    logger.info(f"Ambiente {env_name} ativado com sucesso")
                    return env
        
        logger.warning(f"Ambiente {env_name} não encontrado")
        return env
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao ativar ambiente micromamba: {e}")
        return env
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return env


def get_nextflow_command_with_env(env_name: str = "viralflow") -> list:
    """
    Retorna o comando para executar nextflow com ambiente ativado.
    
    Args:
        env_name: Nome do ambiente micromamba
        
    Returns:
        list: Lista com o comando [bash, -c, "comando completo"]
    """
    return [
        "bash",
        "-c",
        f'eval "$(micromamba shell hook --shell bash)" && '
        f'micromamba activate {env_name} && '
        f'exec nextflow "$@"',
        "bash"  # argv[0]
    ]
