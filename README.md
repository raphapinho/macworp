# Integração ViralFlow-Macworp para Vigilância Genômica Viral

![Status](https://img.shields.io/badge/status-active-success.svg)
![Ubuntu](https://img.shields.io/badge/ubuntu-20.04%20%7C%2022.04-orange.svg)

> Plataforma web integrada para análise automatizada de genomas virais, combinando o poder do ViralFlow com a acessibilidade do Macworp.

## Índice

- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [1. ViralFlow](#1-instalação-do-viralflow)
- [2. Macworp](#2-instalação-do-macworp)
- [Configuração](#configuração)
- [Executando a Aplicação](#executando-a-aplicação)
- [Testando a Plataforma](#testando-a-plataforma)
- [Troubleshooting](#troubleshooting)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

---

## Visão Geral

Esta plataforma integra dois sistemas poderosos:

- **[ViralFlow](https://viralflow.github.io/)**: Pipeline bioinformático especializado para análise de genomas virais
- **[Macworp](https://cubimedrub.github.io/macworp/)**: Plataforma web para gerenciamento e execução de workflows

A integração permite a execução de análises genômicas virais complexas através de uma interface web acessível, sem necessidade de conhecimento avançado em linha de comando.

### Características

- Análise automatizada de sequências virais (SARS-CoV-2, Dengue, Zika, etc.)
- Interface web intuitiva
- Workflows pré-configurados e customizáveis
- Visualização de resultados em tempo real
- Controle de acesso e gerenciamento de projetos
- Execução distribuída de análises

---

## Pré-requisitos

### Sistema Operacional

**IMPORTANTE**: Este projeto foi testado e é recomendado para:

- **Ubuntu 20.04 LTS** 
- **Ubuntu 22.04 LTS** 

Outras distribuições Linux podem funcionar, mas não são oficialmente suportadas.

### Hardware Mínimo

- **CPU**: 4 cores (8 cores recomendado)
- **RAM**: 16GB (32GB recomendado para múltiplas análises simultâneas)
- **Disco**: 100GB de espaço livre
- **Conexão**: Internet estável para download de dependências

### Software Base

Antes de começar, certifique-se de ter instalado:

```bash
# Atualizar sistema
sudo apt update
sudo apt upgrade -y

# Instalar dependências básicas
sudo apt install -y \
    git \
    curl \
    wget \
    build-essential \
    python3 \
    python3-pip \
    python3-venv
```

---

## Instalação

A instalação deve ser feita **na ordem especificada abaixo**. Primeiro instale o ViralFlow, depois o Macworp.

### 1. Instalação do ViralFlow

O ViralFlow é o pipeline de análise que será integrado ao Macworp.

#### 1.1. Clonar o Repositório

```bash
# Ir para o diretório home
cd ~

# Clonar o repositório do ViralFlow
git clone https://github.com/raphapinho/ViralFlow.git

# Entrar no diretório
cd ViralFlow

# Fazer checkout da branch apropriada (se necessário)
git checkout main
```

#### 1.2. Instalar Dependências do ViralFlow

Siga as instruções oficiais da documentação do ViralFlow:

**Documentação oficial**: https://viralflow.github.io/

```bash
# Instalar Micromamba (gerenciador de ambientes conda)
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)

# Reiniciar o terminal ou executar
source ~/.bashrc

# Criar ambiente do ViralFlow
micromamba create -n viralflow -c conda-forge -c bioconda \
    python=3.10 \
    nextflow \
    fastp \
    bwa \
    samtools \
    bcftools \
    bedtools \
    ivar \
    snpeff \
    mafft \
    iqtree

# Ativar ambiente
micromamba activate viralflow

# Verificar instalação do Nextflow
nextflow -version
```

#### 1.3. Testar ViralFlow

```bash
# Ativar ambiente
micromamba activate viralflow

# Testar com dados de exemplo (se disponível)
cd ~/ViralFlow
nextflow run vfnext/main.nf --help
```

Se o comando acima mostrar a ajuda do ViralFlow, a instalação foi bem-sucedida! ✅

---

### 2. Instalação do Macworp

Agora vamos instalar o Macworp, que fornecerá a interface web para o ViralFlow.

#### 2.1. Clonar o Repositório do Macworp

```bash
# Voltar para o diretório home
cd ~

# Clonar o repositório do Macworp
git clone https://github.com/raphapinho/macworp.git

# Entrar no diretório
cd macworp

# Fazer checkout da branch apropriada
git checkout main
```

#### 2.2. Instalar Dependências do Macworp

Siga as instruções oficiais de desenvolvimento do Macworp:

**Documentação oficial**: https://cubimedrub.github.io/macworp/latest/development/

```bash
# Instalar Docker (se ainda não tiver)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Aplicar mudanças (ou fazer logout/login)
newgrp docker

# Verificar Docker
docker --version
docker compose version

# Instalar dependências Python
pip3 install -r requirements.txt

# Instalar Honcho (gerenciador de processos)
pip3 install honcho
```

#### 2.3. Configurar Ambiente de Desenvolvimento

```bash
cd ~/macworp

# Copiar arquivo de configuração de exemplo
cp dev.env.example dev.env

# Editar configurações se necessário
nano dev.env
```

#### 2.4. Verificar Estrutura de Diretórios

```bash
# Criar diretório de uploads (se não existir)
mkdir -p ~/macworp/uploads

# Criar link simbólico para o ViralFlow
ln -s ~/ViralFlow ~/macworp/workflows/viralflow
```

---

## Configuração

### Configurar Integração ViralFlow-Macworp

#### 1. Criar Script de Ativação do ViralFlow

```bash
# Criar script helper
cat > ~/macworp/activate_viralflow.sh <<'EOF'
#!/bin/bash
# Script para ativar ambiente ViralFlow
eval "$(micromamba shell hook --shell bash)"
micromamba activate viralflow
exec "$@"
EOF

# Dar permissão de execução
chmod +x ~/macworp/activate_viralflow.sh
```

#### 2. Verificar Nextflow

```bash
# Localizar Nextflow
which nextflow

# Se não encontrar, criar link simbólico
# (substitua o caminho pelo resultado do comando acima)
ln -s $(which nextflow) ~/macworp/nextflow
```

#### 3. Verificar Snakemake (opcional)

```bash
# Verificar Snakemake
which snakemake

# Se não instalado
pip3 install snakemake
```

---

## 🎮 Executando a Aplicação

Para executar o Macworp com ViralFlow integrado, você precisa abrir **3 terminais separados** e executar comandos específicos em cada um.

### Terminal 1: Serviços Docker

Este terminal inicia os serviços de infraestrutura (PostgreSQL, Redis, RabbitMQ).

```bash
# Abrir Terminal 1
cd ~/macworp

# Iniciar serviços Docker
docker-compose up
```

**Saída esperada:**
```
Creating network "macworp_default" with the default driver
Creating macworp_postgres_1 ... done
Creating macworp_redis_1    ... done
Creating macworp_rabbitmq_1 ... done
```

**Mantenha este terminal aberto!** Não feche nem use Ctrl+C.

---

### Terminal 2: Backend e Frontend

Este terminal prepara o banco de dados e inicia o backend/frontend.

```bash
# Abrir Terminal 2 (Nova janela/aba)
cd ~/macworp

# 1. Executar migrações do banco de dados
python -m macworp_backend database migrate

# 2. Preparar RabbitMQ
python -m macworp_backend utility rabbitmq prepare

# 3. Iniciar backend e frontend com Honcho
honcho -e dev.env start
```

**Saída esperada:**
```
Starting macworp database migration...
✓ Migration completed successfully

Preparing RabbitMQ...
✓ RabbitMQ queues created

13:45:01 system   | backend.1 started (pid=12345)
13:45:01 system   | frontend.1 started (pid=12346)
13:45:02 backend  | * Running on http://localhost:3001
13:45:03 frontend | * Running on http://localhost:5001
```

**Mantenha este terminal aberto!**

---

### Terminal 3: Worker (Executor de Workflows)

Este terminal inicia o worker que executará os workflows do ViralFlow.

```bash
# Abrir Terminal 3 (Nova janela/aba)
cd ~/macworp

# Ativar ambiente ViralFlow e iniciar worker
env PYTHONUNBUFFERED=1 python -m macworp_worker \
    -n ./nextflow \
    -s $(which snakemake) \
    -c http://localhost:3001 \
    -r amqp://admin:developer@127.0.0.1:5674/%2f \
    -q project_workflow \
    -d ./uploads \
    -u worker \
    -p developer \
    -vvvvvvvv
```

**Parâmetros explicados:**
- `-n ./nextflow`: Caminho para o executável do Nextflow
- `-s $(which snakemake)`: Caminho para o Snakemake (opcional)
- `-c http://localhost:3001`: URL do backend
- `-r amqp://admin:developer@127.0.0.1:5674/%2f`: URL do RabbitMQ
- `-q project_workflow`: Nome da fila
- `-d ./uploads`: Diretório de trabalho
- `-u worker`: Usuário do worker
- `-p developer`: Senha do worker
- `-vvvvvvvv`: Modo verbose (para debug)

**Saída esperada:**
```
Worker started successfully
Connected to RabbitMQ: amqp://admin:***@127.0.0.1:5674/%2f
Listening on queue: project_workflow
Nextflow version: 23.10.0
Ready to process workflows...
```

**Mantenha este terminal aberto!**

---

##  Testando a Plataforma

### 1. Acessar a Interface Web

Abra seu navegador e acesse:

```
http://localhost:5001
```

Você deverá ver a página de login do Macworp.

### 2. Fazer Login

**Credenciais padrão de desenvolvimento:**
- **Usuário**: `developer`
- **Senha**: `developer`

### 3. Criar Primeiro Projeto

1. Após o login, clique em **"Novo Projeto"**
2. Digite um nome: `Teste ViralFlow`
3. Adicione uma descrição (opcional)
4. Clique em **"Criar"**

### 4. Adicionar Workflow ViralFlow

1. No menu lateral, clique em **"Workflows"**
2. Clique em **"Adicionar Workflow"**
3. Preencha:
   - **Nome**: `ViralFlow - SARS-CoV-2`
   - **Descrição**: `Pipeline para análise de genomas SARS-CoV-2`
   - **Engine**: Selecione `Nextflow`
   - **Caminho do Workflow**: `~/ViralFlow/vfnext/main.nf`

4. Configure parâmetros padrão (exemplo para SARS-CoV-2):
```json
{
  "virus": "sars-cov2",
  "runSnpEff": true,
  "writeMappedReads": true,
  "minLen": 75,
  "depth": 25,
  "minDpIntrahost": 100
}
```

5. Clique em **"Salvar"**

### 5. Upload de Dados de Teste

1. Entre no projeto `Teste ViralFlow`
2. Clique em **"Upload"**
3. Faça upload de arquivos FASTQ de teste
4. Ou use os dados de exemplo do ViralFlow:

```bash
# Copiar dados de exemplo para o projeto
cp ~/ViralFlow/test_files/sars-cov-2/input/*.fastq.gz ~/macworp/uploads/
```

### 6. Executar Análise de Teste

1. No projeto, clique em **"Executar Workflow"**
2. Selecione o workflow `ViralFlow - SARS-CoV-2`
3. Configure os parâmetros:
   - **inDir**: Selecione a pasta com os arquivos FASTQ
   - **outDir**: Selecione pasta para resultados
4. Clique em **"Executar"**

### 7. Monitorar Execução

No **Terminal 3** (worker), você verá:
```
[INFO] Received job: workflow_123
[INFO] Starting Nextflow execution
[INFO] N E X T F L O W  ~  version 23.10.0
[INFO] Launching workflow...
```

Na interface web, você verá o status da execução em tempo real.

### 8. Visualizar Resultados

Após a conclusão (pode levar 20-40 minutos dependendo dos dados):
1. Navegue até a pasta de resultados
2. Visualize os arquivos gerados:
   - Consensos FASTA
   - VCF de variantes
   - Relatórios HTML
   - Gráficos de cobertura

---

## Verificação Rápida

Use esta checklist para verificar se tudo está funcionando:

### Checklist de Instalação

- [ ] Ubuntu 20.04 ou 22.04 instalado
- [ ] ViralFlow clonado de `https://github.com/raphapinho/ViralFlow.git`
- [ ] Ambiente conda/micromamba do ViralFlow criado
- [ ] Nextflow executável (`nextflow -version` funciona)
- [ ] Macworp clonado de `https://github.com/raphapinho/macworp.git`
- [ ] Docker instalado e funcionando
- [ ] Dependências Python instaladas
- [ ] `docker-compose up` funciona sem erros
- [ ] Migrações do banco executadas com sucesso
- [ ] Backend rodando em `http://localhost:3001`
- [ ] Frontend rodando em `http://localhost:5001`
- [ ] Worker conectado e aguardando jobs
- [ ] Login na interface web funciona
- [ ] Workflow pode ser adicionado
- [ ] Análise de teste executa com sucesso

---

## Troubleshooting

### Problema: "docker: permission denied"

```bash
# Solução: Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Ou reiniciar a sessão
logout
# Fazer login novamente
```

### Problema: "Port 5001 already in use"

```bash
# Verificar o que está usando a porta
sudo netstat -tulpn | grep :5001

# Matar o processo
sudo kill -9 [PID]

# Ou mudar a porta no dev.env
nano dev.env
# Alterar: FRONTEND_PORT=5002
```

### Problema: "Nextflow command not found"

```bash
# Verificar se o ambiente está ativado
micromamba activate viralflow

# Verificar instalação
which nextflow

# Se não encontrado, reinstalar
micromamba install -c bioconda nextflow

# Criar link simbólico
ln -s $(which nextflow) ~/macworp/nextflow
```

### Problema: "Connection refused to RabbitMQ"

```bash
# Verificar se RabbitMQ está rodando
docker ps | grep rabbitmq

# Se não estiver, reiniciar docker-compose
cd ~/macworp
docker-compose down
docker-compose up -d

# Aguardar 30 segundos
sleep 30
```

### Problema: "Database migration failed"

```bash
# Limpar banco e recomeçar
cd ~/macworp
docker-compose down -v
docker-compose up -d

# Aguardar serviços iniciarem
sleep 30

# Executar migração novamente
python -m macworp database migrate
```

### Problema: Worker não processa jobs

```bash
# Verificar logs do worker (Terminal 3)
# Deve mostrar: "Ready to process workflows..."

# Se não mostrar, verificar:
# 1. Nextflow está no PATH?
which nextflow

# 2. Backend está acessível?
curl http://localhost:3001/api/health

# 3. RabbitMQ está acessível?
docker logs macworp_rabbitmq_1
```

### Problema: "ModuleNotFoundError"

```bash
# Reinstalar dependências Python
cd ~/macworp
pip3 install -r requirements.txt

# Ou instalar módulo específico
pip3 install [nome-do-modulo]
```

### Logs Detalhados

```bash
# Ver logs do Docker Compose
cd ~/macworp
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f postgres
docker-compose logs -f rabbitmq

# Ver logs do backend
tail -f backend.log

# Ver logs do worker
# (já exibidos no Terminal 3 com -vvvvvvvv)
```

---

## Documentação Adicional

### ViralFlow
- **Documentação**: https://viralflow.github.io/
- **GitHub**: https://github.com/raphapinho/ViralFlow
- **Issues**: https://github.com/raphapinho/ViralFlow/issues

### Macworp
- **Documentação**: https://cubimedrub.github.io/macworp/
- **GitHub**: https://github.com/raphapinho/macworp
- **Development Guide**: https://cubimedrub.github.io/macworp/latest/development/

### Ferramentas Utilizadas
- **Nextflow**: https://www.nextflow.io/docs/
- **Docker**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **Micromamba**: https://mamba.readthedocs.io/

---

##  Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes de Contribuição

- Siga o estilo de código existente
- Adicione testes para novas funcionalidades
- Atualize a documentação conforme necessário
- Descreva claramente suas mudanças no PR

---

##  Changelog

### Versão 1.0.0 (2025-01-16)
- Integração inicial ViralFlow-Macworp
- Suporte para Ubuntu 20.04 e 22.04
- Containerização com Docker
- Interface web completa
- Análise de SARS-CoV-2, Dengue, Zika

---

##  Autores

- **Raphael Pinho** - *Desenvolvimento e Integração* - [GitHub](https://github.com/raphapinho)

---

##  Licença

Perguntar sobre licenciamento

---

##  Agradecimentos

- Equipe do [ViralFlow](https://github.com/dezordi/ViralFlow)
- Equipe do [Macworp](https://github.com/cubimedrub/macworp)
- Comunidade de bioinformática open-source
- Universidade Federal do Pará (UFPA)

---

## Suporte

Se encontrar problemas ou tiver dúvidas:

1. Verifique a seção [Troubleshooting](#troubleshooting)
2. Consulte as documentações oficiais
3. Abra uma [Issue](https://github.com/seu-usuario/seu-repo/issues)
4. Entre em contato: seu-email@exemplo.com

---

## Próximos Passos

Após ter a plataforma funcionando em ambiente de desenvolvimento, você pode:

1. **Adicionar mais workflows** - Configure workflows para outros vírus
2. **Customizar parâmetros** - Ajuste parâmetros conforme suas necessidades
3. **Deploy em produção** - Siga o guia de [deploy em produção](DEPLOY.md)
4. **Integrar com LIMS** - Conecte com sistemas de laboratório existentes
5. **Automatizar análises** - Configure análises automáticas via API

---

** Desenvolvido com amor para vigilância genômica viral**