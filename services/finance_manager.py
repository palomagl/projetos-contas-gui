"""
services/finance_manager.py
Camada de dados do sistema de Contas a Pagar e Receber.

Este módulo cuida de tudo que é "dado":
- as opções fixas (tuplas);
- a leitura e a escrita do arquivo contas.txt;
- as funções que alteram a lista de contas em memória (CRUD);
- filtros, ordenação e agrupamento por mês;
- os cálculos financeiros (receitas, despesas e saldo);
- a exportação de relatório para o Excel (.csv).

Aqui não tem nada de interface gráfica: quem mostra as coisas na tela
é o arquivo views/app_gui.py.
"""

import csv
import math
import os
import re
import tempfile
import unicodedata
from datetime import date, datetime

# ===========================================================================
# Tuplas: opções fixas (imutáveis)
# ===========================================================================
TIPOS = ('Receita', 'Despesa')
STATUS_OPCOES = ('Pendente', 'Pago')

# Ordem dos campos em cada linha do contas.txt
CAMPOS = ('id', 'descricao', 'valor', 'tipo', 'vencimento', 'status')

SEPARADOR = ';'
FORMATO_DATA = '%d/%m/%Y'  # dd/mm/aaaa

MESES = ('jan', 'fev', 'mar', 'abr', 'mai', 'jun',
         'jul', 'ago', 'set', 'out', 'nov', 'dez')
MESES_EXTENSO = ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
                 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro')
DIAS_SEMANA = ('segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira',
               'sexta-feira', 'sábado', 'domingo')


# ===========================================================================
# 1. Leitura e escrita do arquivo TXT
# ===========================================================================
def carregar_contas(caminho='contas.txt'):
    """Lê o arquivo linha por linha e devolve uma lista de dicionários.

    - Se o arquivo não existir, devolve uma lista vazia.
    - Linhas com formato errado são ignoradas.
    """
    contas = []
    try:
        # 'utf-8-sig' lê UTF-8 normal e também arquivos salvos pelo Bloco de Notas com BOM
        with open(caminho, 'r', encoding='utf-8-sig') as arq:
            for linha in arq:
                dados = linha.strip().split(SEPARADOR)
                if len(dados) == len(CAMPOS):
                    try:
                        contas.append({
                            'id': int(dados[0]),
                            'descricao': dados[1],
                            'valor': float(dados[2]),
                            'tipo': dados[3],
                            'vencimento': dados[4],
                            'status': dados[5],
                        })
                    except ValueError:
                        # id ou valor não são números: pula a linha
                        continue
    except FileNotFoundError:
        # Primeira vez que o programa roda: o arquivo ainda não existe
        pass
    return contas


def salvar_contas(contas, caminho='contas.txt'):
    """Salva de forma atômica: falhas não corrompem o arquivo anterior.

    O arquivo temporário é criado na mesma pasta para permitir os.replace.
    """
    pasta = os.path.dirname(os.path.abspath(caminho))
    os.makedirs(pasta, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=pasta,
                                         prefix='.contas-', suffix='.tmp',
                                         delete=False) as arq:
            temporario = arq.name
            for conta in contas:
                linha = SEPARADOR.join((
                    str(conta['id']), conta['descricao'], f"{conta['valor']:.2f}",
                    conta['tipo'], conta['vencimento'], conta['status'],
                ))
                arq.write(linha + '\n')
            arq.flush()
            os.fsync(arq.fileno())
        os.replace(temporario, caminho)
    finally:
        if temporario is not None and os.path.exists(temporario):
            os.unlink(temporario)


# ===========================================================================
# 2. Validação dos dados digitados no formulário
# ===========================================================================
def converter_valor(texto):
    """Transforma o texto digitado em float.

    Aceita '1200.50', '1200,50', '1.200,50' e '1.200'. Levanta ValueError se for inválido.
    """
    texto = str(texto).strip().replace('R$', '').replace(' ', '')
    if ',' in texto:
        # Formato brasileiro: o ponto separa milhar e a vírgula separa centavos
        texto = texto.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'\d{1,3}(\.\d{3})+', texto):
        # '1.350' ou '1.200.000': o ponto aqui é de milhar, não de centavos
        texto = texto.replace('.', '')
    try:
        valor = float(texto)
    except ValueError:
        raise ValueError('Valor inválido. Digite só números, por exemplo: 150,90')
    if not math.isfinite(valor):
        raise ValueError('Digite um valor numérico válido.')
    if valor <= 0:
        raise ValueError('O valor precisa ser maior que zero.')
    return round(valor, 2)


def validar_data(texto):
    """Confere se a data está no formato dd/mm/aaaa e se ela existe (ex.: 31/02 não existe)."""
    try:
        data = datetime.strptime(texto.strip(), FORMATO_DATA)
    except ValueError:
        raise ValueError('Data inválida. Use o formato dd/mm/aaaa, por exemplo: 25/12/2026')
    return data.strftime(FORMATO_DATA)  # devolve sempre com 2 dígitos: 05/01/2026


def validar_conta(descricao, valor, tipo, vencimento, status):
    """Confere todos os campos do formulário.

    Devolve um dicionário com os dados já convertidos (sem o id)
    ou levanta ValueError com uma mensagem para o usuário.
    """
    descricao = descricao.strip()
    if not descricao:
        raise ValueError('Preencha a descrição da conta.')
    if SEPARADOR in descricao or '\n' in descricao or '\r' in descricao:
        raise ValueError('A descrição não pode ter ponto e vírgula ou quebra de linha.')
    if len(descricao) > 120:
        raise ValueError('A descrição deve ter até 120 caracteres.')

    valor = converter_valor(valor)

    if tipo not in TIPOS:
        raise ValueError('Escolha o tipo: Receita ou Despesa.')

    vencimento = validar_data(vencimento)

    if status not in STATUS_OPCOES:
        raise ValueError('Escolha o status: Pendente ou Pago.')

    return {
        'descricao': descricao,
        'valor': valor,
        'tipo': tipo,
        'vencimento': vencimento,
        'status': status,
    }


# ===========================================================================
# 3. CRUD na lista de contas (em memória)
# ===========================================================================
def gerar_novo_id(contas):
    """Próximo id = maior id da lista + 1 (ou 1 se a lista estiver vazia)."""
    maior = 0
    for conta in contas:
        if conta['id'] > maior:
            maior = conta['id']
    return maior + 1


def adicionar_conta(contas, descricao, valor, tipo, vencimento, status='Pendente'):
    """Valida os dados, cria o dicionário da conta e coloca na lista."""
    dados = validar_conta(descricao, valor, tipo, vencimento, status)
    conta = {'id': gerar_novo_id(contas)}
    conta.update(dados)
    contas.append(conta)
    return conta


def buscar_conta(contas, id_conta):
    """Procura a conta pelo id (usando while). Devolve o dicionário ou None."""
    i = 0
    while i < len(contas):
        if contas[i]['id'] == id_conta:
            return contas[i]
        i += 1
    return None


def editar_conta(contas, id_conta, descricao, valor, tipo, vencimento, status):
    """Altera os dados da conta com aquele id. Devolve True se encontrou a conta."""
    conta = buscar_conta(contas, id_conta)
    if conta is None:
        return False
    dados = validar_conta(descricao, valor, tipo, vencimento, status)
    conta.update(dados)
    return True


def excluir_conta(contas, id_conta):
    """Remove da lista a conta com aquele id. Devolve True se encontrou a conta."""
    conta = buscar_conta(contas, id_conta)
    if conta is None:
        return False
    contas.remove(conta)
    return True


def alternar_status(contas, id_conta):
    """Troca o status da conta: Pendente vira Pago e Pago vira Pendente.

    Devolve o novo status, ou None se a conta não existir.
    """
    conta = buscar_conta(contas, id_conta)
    if conta is None:
        return None
    if conta['status'] == 'Pendente':
        conta['status'] = 'Pago'
    else:
        conta['status'] = 'Pendente'
    return conta['status']


# ===========================================================================
# 4. Cálculos financeiros
# ===========================================================================
def calcular_resumo(contas):
    """Devolve uma tupla (total_receitas, total_despesas, saldo)."""
    rec = sum(c['valor'] for c in contas if c['tipo'] == 'Receita')
    desp = sum(c['valor'] for c in contas if c['tipo'] == 'Despesa')
    return rec, desp, rec - desp


def calcular_pendencias(contas):
    """Soma o que ainda falta receber e pagar. Devolve uma tupla (a_receber, a_pagar)."""
    a_receber = 0.0
    a_pagar = 0.0
    for conta in contas:
        if conta['status'] == 'Pendente':
            if conta['tipo'] == 'Receita':
                a_receber += conta['valor']
            elif conta['tipo'] == 'Despesa':
                a_pagar += conta['valor']
    return a_receber, a_pagar


def esta_atrasada(conta, hoje=None):
    """True se a conta ainda está Pendente e a data de vencimento já passou."""
    if conta['status'] != 'Pendente':
        return False
    if hoje is None:
        hoje = date.today()
    try:
        vencimento = datetime.strptime(conta['vencimento'], FORMATO_DATA).date()
    except ValueError:
        return False
    return vencimento < hoje


# ===========================================================================
# 5. Busca, filtros e ordenação
# ===========================================================================
def remover_acentos(texto):
    """'Salário' -> 'salario'. Assim a busca acha a conta com ou sem acento."""
    decomposto = unicodedata.normalize('NFD', texto.lower())
    return ''.join(letra for letra in decomposto if unicodedata.category(letra) != 'Mn')


def filtrar_contas(contas, texto='', tipo=None, status=None, mes=None):
    """Devolve uma nova lista só com as contas que passam em todos os filtros.

    - texto: parte da descrição (não diferencia maiúscula nem acento)
    - tipo: 'Receita' ou 'Despesa' (None = todos)
    - status: 'Pendente', 'Pago' ou 'Atrasada' (None = todos)
    - mes: 'aaaa-mm', por exemplo '2026-11' (None = todos)
    """
    busca = remover_acentos(texto.strip())
    resultado = []
    for conta in contas:
        if busca and busca not in remover_acentos(conta['descricao']):
            continue
        if tipo and conta['tipo'] != tipo:
            continue
        if status == 'Atrasada':
            if not esta_atrasada(conta):
                continue
        elif status and conta['status'] != status:
            continue
        if mes and chave_mes(conta) != mes:
            continue
        resultado.append(conta)
    return resultado


def ordenar_contas(contas, coluna='vencimento', decrescente=False):
    """Devolve uma NOVA lista ordenada pela coluna escolhida (a lista original não muda)."""
    def valor_para_ordenar(conta):
        if coluna == 'vencimento':
            try:
                return datetime.strptime(conta['vencimento'], FORMATO_DATA)
            except ValueError:
                return datetime.max  # datas inválidas vão para o final
        if coluna == 'descricao':
            return remover_acentos(conta['descricao'])
        return conta[coluna]
    return sorted(contas, key=valor_para_ordenar, reverse=decrescente)


# ===========================================================================
# 6. Agrupamento por mês (usado no gráfico e no filtro de mês)
# ===========================================================================
def chave_mes(conta):
    """'05/11/2026' -> '2026-11'. Devolve None se a data for inválida."""
    try:
        data = datetime.strptime(conta['vencimento'], FORMATO_DATA)
    except ValueError:
        return None
    return f'{data.year}-{data.month:02d}'


def rotulo_mes(chave):
    """'2026-11' -> 'nov/2026'."""
    ano, mes = chave.split('-')
    return f'{MESES[int(mes) - 1]}/{ano}'


def listar_meses(contas):
    """Lista os meses (aaaa-mm) que têm contas, do mais antigo para o mais novo."""
    meses = []
    for conta in contas:
        chave = chave_mes(conta)
        if chave is not None and chave not in meses:
            meses.append(chave)
    return sorted(meses)


def agrupar_por_mes(contas):
    """Soma receitas e despesas de cada mês.

    Devolve um dicionário de dicionários, em ordem de data. Exemplo:
    {'2026-11': {'Receita': 4300.0, 'Despesa': 1930.65}}
    """
    grupos = {}
    for conta in contas:
        chave = chave_mes(conta)
        if chave is None or conta['tipo'] not in TIPOS:
            continue
        if chave not in grupos:
            grupos[chave] = {'Receita': 0.0, 'Despesa': 0.0}
        grupos[chave][conta['tipo']] += conta['valor']
    return {chave: grupos[chave] for chave in sorted(grupos)}


# ===========================================================================
# 7. Relatório para o Excel
# ===========================================================================
def exportar_csv(contas, caminho):
    """Exporta CSV compatível com Excel brasileiro, escapando conteúdo textual."""
    receitas, despesas, saldo = calcular_resumo(contas)

    def seguro_para_excel(texto):
        texto = str(texto)
        # Evita executar fórmulas em programas de planilhas ao abrir o CSV.
        if texto.lstrip().startswith(('=', '+', '-', '@')):
            return "'" + texto
        return texto

    with open(caminho, 'w', encoding='utf-8-sig', newline='') as arq:
        escritor = csv.writer(arq, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        escritor.writerow(['ID', 'Descrição', 'Tipo', 'Vencimento', 'Status', 'Valor (R$)'])
        for conta in contas:
            escritor.writerow([
                conta['id'], seguro_para_excel(conta['descricao']), conta['tipo'],
                conta['vencimento'], conta['status'], formatar_numero(conta['valor']),
            ])
        escritor.writerow([])
        escritor.writerow(['', '', '', '', 'Total de receitas', formatar_numero(receitas)])
        escritor.writerow(['', '', '', '', 'Total de despesas', formatar_numero(despesas)])
        escritor.writerow(['', '', '', '', 'Saldo previsto', formatar_numero(saldo)])


# ===========================================================================
# 8. Formatação de números e datas (padrão brasileiro)
# ===========================================================================
def formatar_numero(valor):
    """1234.5 -> '1.234,50'."""
    valor = round(valor, 2)
    sinal = '-' if valor < 0 else ''
    texto = f'{abs(valor):,.2f}'                  # '1,234.50' (padrão americano)
    texto = texto.replace(',', '_').replace('.', ',').replace('_', '.')
    return sinal + texto


def formatar_moeda(valor):
    """1234.5 -> 'R$ 1.234,50'  e  -50 -> '-R$ 50,00'."""
    texto = formatar_numero(valor)
    if texto.startswith('-'):
        return '-R$ ' + texto[1:]
    return 'R$ ' + texto


def formatar_compacto(valor):
    """Valor curto para o eixo do gráfico: 850 -> 'R$ 850', 3500 -> 'R$ 3,5 mil'."""
    if valor >= 1_000_000:
        texto = f'{valor / 1_000_000:.1f} mi'
    elif valor >= 1000:
        texto = f'{valor / 1000:.1f} mil'
    else:
        texto = f'{valor:.0f}'
    texto = texto.replace('.', ',').replace(',0 ', ' ')  # '3,0 mil' -> '3 mil'
    return 'R$ ' + texto


def data_por_extenso(dia):
    """date(2026, 11, 19) -> 'Quinta-feira, 19 de novembro de 2026'."""
    texto = f'{DIAS_SEMANA[dia.weekday()]}, {dia.day} de {MESES_EXTENSO[dia.month - 1]} de {dia.year}'
    return texto[0].upper() + texto[1:]
