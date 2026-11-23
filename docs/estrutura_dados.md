# Estrutura de Dados

Este documento descreve como os dados do sistema de Contas a Pagar e Receber são organizados na memória (enquanto o programa está aberto) e no arquivo `contas.txt` (quando o programa é fechado).

## 1. Tuplas: opções fixas

Tuplas são **imutáveis**: depois de criadas, não podem ser alteradas. Por isso são usadas para as opções que o usuário pode escolher e que nunca mudam.

```python
TIPOS = ('Receita', 'Despesa')
STATUS_OPCOES = ('Pendente', 'Pago')
CAMPOS = ('id', 'descricao', 'valor', 'tipo', 'vencimento', 'status')
MESES = ('jan', 'fev', 'mar', ..., 'dez')
```

| Tupla           | Para que serve                                                          |
|-----------------|-------------------------------------------------------------------------|
| `TIPOS`         | Diz se a conta é dinheiro que entra (Receita) ou que sai (Despesa)      |
| `STATUS_OPCOES` | Diz se a conta já foi paga/recebida ou se ainda está pendente           |
| `CAMPOS`        | Ordem dos campos em cada linha do `contas.txt`                          |
| `MESES`, `MESES_EXTENSO`, `DIAS_SEMANA` | Nomes usados para mostrar datas em português     |

`TIPOS` e `STATUS_OPCOES` criam os botões de opção do formulário e servem para validar os dados: só são aceitos valores que estão dentro delas. A interface também junta tuplas para montar os filtros:

```python
OPCOES_FILTRO_STATUS = ('Todos os status',) + STATUS_OPCOES + ('Atrasada',)
# ('Todos os status', 'Pendente', 'Pago', 'Atrasada')
```

Funções que devolvem mais de um valor também devolvem tuplas, como `calcular_resumo`, que devolve `(receitas, despesas, saldo)`.

## 2. Dicionário: uma conta

Cada conta é um **dicionário**, em que cada informação tem um nome (chave).

```python
conta = {
    'id': 1,
    'descricao': 'Aluguel',
    'valor': 1200.00,
    'tipo': 'Despesa',
    'vencimento': '10/11/2026',
    'status': 'Pendente'
}
```

| Chave        | Tipo em Python | Descrição                      | Regra                                          |
|--------------|----------------|--------------------------------|------------------------------------------------|
| `id`         | `int`          | Número que identifica a conta  | Único, gerado automaticamente (maior id + 1)   |
| `descricao`  | `str`          | Nome da conta                  | Obrigatório, não pode conter `;`               |
| `valor`      | `float`        | Valor em reais                 | Obrigatório, maior que zero                    |
| `tipo`       | `str`          | Receita ou Despesa             | Deve estar em `TIPOS`                          |
| `vencimento` | `str`          | Data de vencimento             | Formato `dd/mm/aaaa`                           |
| `status`     | `str`          | Situação da conta              | Deve estar em `STATUS_OPCOES`                  |

## 3. Lista: todas as contas

Todas as contas ficam em uma **lista** de dicionários. A lista é usada porque é **mutável**: dá para adicionar, alterar e remover contas.

```python
contas = [
    {'id': 1, 'descricao': 'Salário', 'valor': 3500.0, 'tipo': 'Receita', 'vencimento': '05/11/2026', 'status': 'Pago'},
    {'id': 2, 'descricao': 'Aluguel', 'valor': 1200.0, 'tipo': 'Despesa', 'vencimento': '10/11/2026', 'status': 'Pendente'},
]
```

| Operação  | Como é feita na lista                                         |
|-----------|---------------------------------------------------------------|
| Adicionar | `contas.append(nova_conta)`                                   |
| Listar    | laço `for conta in contas:`                                   |
| Editar    | encontrar a conta pelo `id` e alterar as chaves               |
| Excluir   | encontrar a conta pelo `id` e removê-la (`contas.remove(conta)`) |
| Buscar e filtrar | `filtrar_contas` monta uma **nova lista** só com as contas que passam nos filtros |
| Ordenar   | `ordenar_contas` devolve uma **nova lista** com `sorted(...)`; a original não muda |

A tabela da tela mostra a lista filtrada e ordenada, mas o arquivo sempre recebe a lista completa.

### Dicionário de dicionários: totais por mês

Para o gráfico, `agrupar_por_mes` soma as contas de cada mês em um dicionário cujas chaves são os meses e cujos valores são outros dicionários:

```python
{
    '2026-10': {'Receita': 3950.0, 'Despesa': 2392.8},
    '2026-11': {'Receita': 4300.0, 'Despesa': 1930.65},
}
```

A chave `'aaaa-mm'` (ano antes do mês) faz a ordem alfabética ser também a ordem das datas.

## 4. Arquivo `contas.txt`

Cada linha do arquivo é **uma conta**. Os campos ficam separados por ponto e vírgula (`;`), sempre nesta ordem:

```
id;descricao;valor;tipo;vencimento;status
```

Exemplo:

```
1;Salário;3500.00;Receita;05/11/2026;Pago
2;Aluguel;1200.00;Despesa;10/11/2026;Pendente
```

Regras do arquivo:

- Codificação `utf-8` (para aceitar acentos)
- O valor usa **ponto** como separador decimal (`1200.50`, não `1200,50`)
- O arquivo **não tem linha de cabeçalho**: toda linha é uma conta
- Linhas que não tiverem exatamente 6 campos são ignoradas na leitura
- Se o arquivo não existir, o programa começa com a lista vazia

## 5. Fluxo dos dados

```
contas.txt  --(carregar_contas)-->  lista de dicionários (memória)
                                              |
                                 adicionar / editar / excluir
                                              |
contas.txt  <--(salvar_contas)----  lista de dicionários (memória)
```

1. Ao abrir o programa, o arquivo é lido **linha por linha** com um laço `for`, e cada linha vira um dicionário dentro da lista.
2. Enquanto o programa está aberto, todas as alterações são feitas na lista.
3. Depois de cada alteração, a lista inteira é gravada de volta no arquivo.

## 6. Funções (`services/finance_manager.py`)

**Arquivo**

| Função                            | O que faz                                               | Retorna |
|-----------------------------------|---------------------------------------------------------|---------|
| `carregar_contas(caminho)`        | Lê o TXT linha por linha e monta a lista de dicionários | `list`  |
| `salvar_contas(contas, caminho)`  | Grava a lista no TXT, uma conta por linha               | nada    |

**Validação**

| Função                  | O que faz                                                        | Retorna |
|-------------------------|------------------------------------------------------------------|---------|
| `converter_valor(texto)`| Converte `'1.200,50'`, `'1.200'` ou `'1200.50'` em número e exige valor > 0 | `float` |
| `validar_data(texto)`   | Confere se a data existe e está em `dd/mm/aaaa`                  | `str`   |
| `validar_conta(...)`    | Confere todos os campos do formulário                            | `dict`  |

Se algum dado estiver errado, essas funções levantam `ValueError` com uma mensagem. A interface pega esse erro (`try/except`) e mostra a mensagem num `messagebox`.

**CRUD**

| Função                          | O que faz                                          | Retorna          |
|---------------------------------|----------------------------------------------------|------------------|
| `gerar_novo_id(contas)`         | Calcula o próximo id (maior id + 1, ou 1 se vazia) | `int`            |
| `adicionar_conta(contas, ...)`  | Valida, cria o dicionário e adiciona na lista      | `dict`           |
| `buscar_conta(contas, id)`      | Procura a conta pelo id                            | `dict` ou `None` |
| `editar_conta(contas, id, ...)` | Altera os dados da conta com aquele id             | `bool`           |
| `excluir_conta(contas, id)`     | Remove a conta com aquele id                       | `bool`           |
| `alternar_status(contas, id)`   | Troca Pendente ↔ Pago                              | `str`            |

**Cálculos**

| Função                        | O que faz                                    | Retorna |
|-------------------------------|----------------------------------------------|---------|
| `calcular_resumo(contas)`     | Soma receitas e despesas e calcula o saldo   | `tuple` |
| `calcular_pendencias(contas)` | Soma o que ainda falta receber e pagar       | `tuple` |
| `esta_atrasada(conta)`        | Diz se a conta está pendente e já venceu     | `bool`  |

`calcular_resumo` retorna `(total_receitas, total_despesas, saldo)`. Com o arquivo `exemplo_contas.txt`: `(4300.0, 1930.65, 2369.35)`.
`calcular_pendencias` retorna `(a_receber, a_pagar)`. Com o arquivo `exemplo_contas.txt`: `(800.0, 1380.45)`.

**Busca, filtros e ordenação**

| Função                                  | O que faz                                                         | Retorna |
|-----------------------------------------|-------------------------------------------------------------------|---------|
| `remover_acentos(texto)`                | `'Salário'` vira `'salario'`, para a busca achar com ou sem acento | `str`   |
| `filtrar_contas(contas, texto, tipo, status, mes)` | Nova lista só com as contas que passam em todos os filtros | `list`  |
| `ordenar_contas(contas, coluna, decrescente)` | Nova lista ordenada pela coluna escolhida                   | `list`  |

**Meses e gráfico**

| Função                    | O que faz                                              | Retorna |
|---------------------------|--------------------------------------------------------|---------|
| `chave_mes(conta)`        | `'05/11/2026'` vira `'2026-11'`                        | `str`   |
| `rotulo_mes(chave)`       | `'2026-11'` vira `'nov/2026'`                          | `str`   |
| `listar_meses(contas)`    | Meses que têm contas, em ordem                         | `list`  |
| `agrupar_por_mes(contas)` | Soma receitas e despesas de cada mês                   | `dict` de `dict` |

**Relatório e formatação**

| Função                          | O que faz                                                    | Retorna |
|---------------------------------|--------------------------------------------------------------|---------|
| `exportar_csv(contas, caminho)` | Gera um `.csv` que abre no Excel, com os totais no final     | nada    |
| `formatar_numero(valor)`        | `1234.5` vira `'1.234,50'`                                   | `str`   |
| `formatar_moeda(valor)`         | `1234.5` vira `'R$ 1.234,50'`                                | `str`   |
| `formatar_compacto(valor)`      | `3500` vira `'R$ 3,5 mil'` (eixo do gráfico)                 | `str`   |
| `data_por_extenso(dia)`         | `'Quinta-feira, 19 de novembro de 2026'`                     | `str`   |

## 7. Onde os laços são usados

| Laço    | Onde                          | Para quê                                              |
|---------|-------------------------------|-------------------------------------------------------|
| `for`   | `carregar_contas`             | Ler o arquivo linha por linha                         |
| `for`   | `salvar_contas`               | Gravar cada conta em uma linha                        |
| `for`   | `calcular_resumo`             | Somar receitas e despesas (dentro do `sum(...)`)      |
| `for`   | `calcular_pendencias`         | Somar os valores pendentes                            |
| `for`   | `gerar_novo_id`               | Achar o maior id da lista                             |
| `while` | `buscar_conta`                | Percorrer a lista até achar a conta com o id buscado  |
| `for`   | `filtrar_contas`              | Testar cada conta nos filtros                         |
| `for`   | `agrupar_por_mes`             | Somar os valores de cada mês                          |
| `for`   | `exportar_csv`                | Gravar cada conta no relatório                        |
| `for`   | `app_gui.atualizar_tabela`    | Colocar cada conta como uma linha na tabela           |
| `for`   | `app_gui.desenhar_grafico`    | Desenhar as barras de cada mês                        |

## 8. Estruturas usadas na interface (`views/app_gui.py`)

| Estrutura  | Nome                    | Para quê                                                          |
|------------|-------------------------|-------------------------------------------------------------------|
| Dicionário | `CORES`                 | Paleta de cores da tela (`'receita': '#1e7a4c'`, ...)             |
| Tupla      | `COLUNAS`               | Colunas da tabela: (chave, título, largura, alinhamento)          |
| Tupla      | `OPCOES_FILTRO_TIPO`, `OPCOES_FILTRO_STATUS` | Opções dos filtros                           |
| Lista      | `self.contas`           | Lista global com todas as contas carregadas do TXT                |
| Lista      | `self.contas_exibidas`  | Contas que passam nos filtros, na ordem da tabela                 |
| Dicionário | `self.id_por_linha`     | Liga cada linha da tabela ao id da conta                          |
| Dicionário | `self.meses_por_rotulo` | Liga o texto do filtro (`'nov/2026'`) à chave do mês (`'2026-11'`) |
| Dicionário | `self.resumo`           | Guarda os textos da faixa de resumo, um por chave                 |
| Dicionário | `self.fontes`           | Fontes usadas na tela (normal, negrito, título...)                |
| Tupla      | `self.ordem`            | Coluna que ordena a tabela e se a ordem é decrescente             |
