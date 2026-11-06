# Finanças em Dia

Um organizador financeiro pessoal feito com Python, Flask e SQLite. Cadastre receitas e despesas e acompanhe seus hábitos em um painel simples e responsivo.

## Funcionalidades

- Adicionar, editar e excluir receitas e despesas.
- Filtrar movimentações por mês e categoria.
- Consultar receitas, despesas e saldo de cada mês.
- Visualizar a distribuição das despesas por categoria.
- Armazenar os dados localmente em SQLite, sem criar conta.

Os cartões e o gráfico mostram sempre o mês inteiro; o filtro de categoria afeta apenas a lista de movimentações. Os valores são armazenados em centavos para evitar erros de arredondamento.

## Como executar no Windows

Instale o [Python 3.10 ou superior](https://www.python.org/downloads/) e, durante a instalação, marque a opção **Add Python to PATH**. Abra o terminal na pasta do projeto e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Abra **http://127.0.0.1:5000** no navegador. Para encerrar o programa, volte ao terminal e pressione `Ctrl + C`.

No macOS ou Linux, use `python3 -m venv .venv` e `.venv/bin/python` nos demais comandos.

## Dados e privacidade

O banco é criado automaticamente em `instance/financas.db`, no computador onde o programa é executado. Ele não é enviado ao GitHub. Faça cópias desse arquivo se quiser guardar seus registros. Este projeto foi feito para uso local e aprendizado: não possui autenticação e não deve ser publicado na internet ou exposto a outras pessoas sem adicionar proteção adequada.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Estrutura

- `app.py`: rotas, validações e banco de dados.
- `templates/`: páginas HTML.
- `static/style.css`: aparência e adaptação para celular.
- `tests/`: testes das principais operações.
