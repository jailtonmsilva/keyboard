# Love S2 Nic

Aplicativo desktop para Windows que ativa/desativa o teclado interno via interface grafica, na versao v1.0.0.

Pagina publica de download do EXE:

- https://jailtonmsilva.github.io/keyboard/

## Objetivo deste guia

Este README documenta o passo a passo para montar o ambiente de desenvolvimento local, executar o projeto e gerar o executavel.

## 1) Pre-requisitos

1. Sistema operacional: Windows 10/11
2. PowerShell 5.1+
3. Python 3.14+
4. Git instalado e configurado

Verifique versoes:

```powershell
python --version
git --version
$PSVersionTable.PSVersion
```

## 2) Clonar e entrar no projeto

```powershell
git clone <URL_DO_REPOSITORIO>
cd keyboard
```

Se o repositorio ja estiver local, apenas navegue ate a pasta raiz do projeto.

## 3) Criar ambiente virtual

```powershell
python -m venv .venv
```

## 4) Ativar ambiente virtual

```powershell
. .\.venv\Scripts\Activate.ps1
```

Se houver erro de politica de execucao no PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
. .\.venv\Scripts\Activate.ps1
```

## 5) Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 6) Executar em modo desenvolvimento

Opcao A (launcher da raiz):

```powershell
python love_nic.py
```

Opcao B (execucao por modulo, layout src):

```powershell
$env:PYTHONPATH = "src"
python -m love_nic
```

Observacao importante:

1. O app interage com dispositivo de teclado no Windows e pode solicitar elevacao (admin).
2. Para testes reais de ativar/desativar dispositivo, execute em contexto com permissao administrativa.

## 7) Build do executavel (PyInstaller)

Metodo recomendado (usa configuracao central em spec):

```powershell
python -m PyInstaller --noconfirm --clean love_nic.spec
```

Saida esperada:

1. Executavel em dist/love_nic.exe
2. Artefatos temporarios em build/

## 8) Validacao rapida apos setup

Cheque sintaxe dos modulos:

```powershell
python -m compileall love_nic.py src/love_nic
```

Cheque import principal:

```powershell
python -c "import sys; sys.path.insert(0, 'src'); import love_nic.app"
```

## 9) Estrutura do projeto (resumo)

1. love_nic.py: launcher fino
2. src/love_nic/__main__.py: entrada por modulo
3. src/love_nic/app.py: interface principal
4. src/love_nic/system/keyboard_device.py: integracao com API nativa do Windows
5. src/love_nic/audio/mci_player.py: reproducao de audio via MCI
6. src/love_nic/utils/paths.py: resolucao de caminhos (dev/PyInstaller)
7. projeto/src/img e projeto/src/mp3: assets da aplicacao

## 10) Troubleshooting rapido

1. Erro ao ativar .venv no PowerShell
Use Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned e ative novamente.

2. Modulo nao encontrado ao rodar python -m love_nic
Garanta $env:PYTHONPATH = "src" na mesma sessao do terminal.

3. Build falha por arquivo exe em uso
Feche qualquer instancia de dist/love_nic.exe antes de rodar o build.

4. Assinatura digital para distribuicao externa
O build local funciona sem assinatura publica, mas para distribuicao sem alertas de confianca e necessario certificado OV/EV de CA confiavel.

## 11) Contribuicao

Fluxo recomendado para contribuir com o projeto:

1. Atualize a branch principal local

```powershell
git checkout main
git pull
```

2. Crie uma branch de trabalho

```powershell
git checkout -b feat/nome-da-mudanca
```

3. Faça as alteracoes e valide localmente

```powershell
python -m compileall love_nic.py src/love_nic
```

4. Commit com mensagem clara e objetiva

```powershell
git add .
git commit -m "feat: descreve a mudanca"
```

5. Envie a branch para o remoto

```powershell
git push -u origin feat/nome-da-mudanca
```

6. Abra Pull Request para main

Template de PR:

1. Utilize o modelo em .github/pull_request_template.md

Templates de Issue:

1. Bug report em .github/ISSUE_TEMPLATE/bug_report.md
2. Feature request em .github/ISSUE_TEMPLATE/feature_request.md

Checklist do PR:

1. Descreve objetivo e impacto da mudanca
2. Inclui passos de validacao executados
3. Atualiza README/arquivos de suporte quando necessario
4. Nao inclui arquivos temporarios de build ou cache

Padrao sugerido para prefixo de commit:

1. feat: nova funcionalidade
2. fix: correcao de bug
3. docs: ajuste de documentacao
4. refactor: reorganizacao sem alterar comportamento
5. chore: manutencao geral
