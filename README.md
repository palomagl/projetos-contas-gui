# Fluxo — Contas a Pagar e Receber

Aplicativo desktop feito em **Python + Tkinter** para organizar receitas, despesas, vencimentos e pagamentos. Interface renovada, sem instalar bibliotecas externas e sem banco de dados.

## O que mudou

- **Cadastro e edição separados**: clicar numa linha só a seleciona. Para editar, clique em **Editar** (ou dê duplo clique). Depois de salvar, o formulário volta automaticamente a **Novo lançamento**.
- **Novo lançamento sempre disponível** no canto superior direito; **Esc** cancela a edição.
- **Resumo mais claro**: saldo realizado considera apenas valores pagos/recebidos. A receber, a pagar e vencidas são mostrados separadamente. Os indicadores acompanham os filtros da tabela.
- Interface mais limpa, com pesquisa, filtros, tabela, formulário e gráfico por mês.
- Mudança de status, edição, exclusão confirmada e exportação CSV.
- Salvamento automático no `contas.txt`, com substituição atômica: se a gravação falhar, o arquivo antigo continua intacto.
- Dados financeiros locais não são enviados para GitHub (`contas.txt` está no `.gitignore`).

## Rodar no PyCharm

1. Abra a pasta que contém `main.py` no PyCharm.
2. Configure um interpretador **Python 3.8 ou superior**.
3. Clique com o botão direito em `main.py` e escolha **Run 'main'**.

Ou abra o terminal na pasta do projeto:

```bash
python main.py
```

No Windows, se `python` não funcionar, use `py main.py`. O Tkinter normalmente já acompanha a instalação do Python para Windows.

## Primeiro uso / dados de demonstração

O programa começa vazio se não existir `contas.txt`. Para testar com lançamentos fictícios, copie `docs/exemplo_contas.txt` para `contas.txt`, na mesma pasta de `main.py`, **antes** de abrir o aplicativo.

Se você já usava a versão antiga, mantenha uma cópia do seu `contas.txt` e coloque-a ao lado do `main.py` novo. O formato de dados continua compatível.

## Como usar

- **Cadastrar:** preencha o formulário e clique em **Adicionar lançamento**.
- **Editar:** selecione uma linha e clique em **Editar**; salve as alterações. O formulário será liberado para um novo cadastro.
- **Cancelar edição / cadastrar outra:** clique em **Cancelar**, **+ Novo lançamento** ou **Esc**.
- **Pagar / reabrir:** selecione a linha e clique em **Marcar como pago/pendente**.
- **Excluir:** selecione a conta e clique em **Excluir**. Há confirmação antes da exclusão.
- **Buscar:** digite parte da descrição. A busca ignora acentos.
- **Filtrar:** selecione tipo, situação ou mês. Clique em **Limpar** para remover os filtros.
- **Ordenar:** clique em qualquer coluna da tabela, uma segunda vez inverte a ordem.
- **Gráfico mensal:** consulte receitas e despesas previstas por vencimento (até seis meses mais recentes dos lançamentos filtrados).
- **Exportar:** salva um CSV separado por `;` que abre no Excel.

Atalhos: **Enter** nos campos salva, **Esc** volta para novo lançamento, **Ctrl+F** foca a busca, **Delete** na tabela exclui a conta selecionada.

## Estrutura

```text
projeto_contas_gui/
├── main.py                  # Entrada da aplicação
├── services/
│   └── finance_manager.py   # CRUD, TXT, filtros, cálculos, exportação
├── views/
│   └── app_gui.py           # Interface Tkinter
├── docs/
│   ├── estrutura_dados.md   # Fundamentos de listas, tuplas e dicionários
│   └── exemplo_contas.txt   # Dados fictícios de exemplo
├── tests/
│   └── test_finance_manager.py
└── README.md
```

## Testes

```bash
python -m unittest discover -s tests -v
```

Todas as regras usam a biblioteca padrão do Python. A GUI utiliza `tkinter`/`ttk`, e o gráfico utiliza `tk.Canvas`.

## Observação sobre saldo

**Saldo realizado** = soma das receitas **pagas/recebidas** − soma das despesas **pagas**. Receitas e despesas **pendentes** não afetam o saldo realizado; aparecem nos indicadores a receber e a pagar. Os números exibidos refletem os filtros atuais.
