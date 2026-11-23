"""Interface principal do Fluxo — Tkinter/ttk, sem dependências externas.

Importante: selecionar uma linha NÃO inicia edição. Edição só começa no botão
Editar ou com duplo clique; após salvar, o formulário volta ao modo cadastro.
"""

import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

from services import finance_manager as fm


C = {
    'bg': '#F5F7FB', 'panel': '#FFFFFF', 'text': '#17263C',
    'muted': '#66768B', 'border': '#E4EAF2', 'line': '#EDF1F6',
    'brand': '#2459DD', 'brand_hover': '#1948BD',
    'brand_soft': '#EAF0FF', 'green': '#17805A', 'green_soft': '#EAF7F0',
    'red': '#C24148', 'red_soft': '#FFF0F1', 'amber': '#A66616',
    'amber_soft': '#FFF5E8', 'soft': '#F8FAFD',
}


class AppContas:
    """Organiza a interface; toda regra de negócio fica em finance_manager."""

    def __init__(self, janela, caminho_arquivo='contas.txt'):
        self.janela = janela
        self.caminho = caminho_arquivo
        self.contas = []
        self.contas_exibidas = []
        self.id_edicao = None
        self.ids_linhas = {}
        self.meses_por_rotulo = {}
        self.ordem = ('vencimento', False)
        self._silenciar_filtros = False
        self._aviso_agendado = None

        janela.title('Fluxo — Contas a Pagar e Receber')
        janela.geometry('1250x800')
        janela.minsize(1000, 670)
        janela.configure(bg=C['bg'])
        self._configurar_fontes()
        self._configurar_estilos()
        self._criar_variaveis()
        self._montar_tela()
        self._registrar_atalhos()
        self._carregar()
        self.novo_lancamento(focar=False)
        self.atualizar_tela()

    def _configurar_fontes(self):
        familias = set(tkfont.families(self.janela))
        self.fonte = 'Segoe UI' if 'Segoe UI' in familias else 'Arial'
        self.fonte_titulo = (self.fonte, 25, 'bold')
        self.fonte_secao = (self.fonte, 13, 'bold')
        self.fonte_normal = (self.fonte, 10)
        self.fonte_pequena = (self.fonte, 9)
        self.fonte_forte = (self.fonte, 10, 'bold')

    def _configurar_estilos(self):
        estilo = ttk.Style(self.janela)
        estilo.theme_use('clam')
        estilo.configure('Principal.TButton', font=self.fonte_forte,
                         foreground='white', background=C['brand'],
                         bordercolor=C['brand'], padding=(15, 11), relief='flat')
        estilo.map('Principal.TButton', background=[('active', C['brand_hover']),
                                                     ('disabled', '#9DB5F1')])
        estilo.configure('Secundario.TButton', font=self.fonte_forte,
                         foreground=C['text'], background=C['panel'],
                         bordercolor=C['border'], padding=(12, 9), relief='flat')
        estilo.map('Secundario.TButton', background=[('active', C['brand_soft']),
                                                      ('disabled', C['soft'])])
        estilo.configure('Perigo.TButton', font=self.fonte_normal,
                         foreground=C['red'], background=C['panel'],
                         bordercolor=C['border'], padding=(9, 9), relief='flat')
        estilo.map('Perigo.TButton', background=[('active', C['red_soft'])])
        estilo.configure('Filtros.TCombobox', font=self.fonte_normal,
                         fieldbackground=C['panel'], background=C['panel'],
                         padding=8, arrowsize=13)
        estilo.map('Filtros.TCombobox', fieldbackground=[('readonly', C['panel'])],
                                              foreground=[('readonly', C['text'])])
        estilo.configure('Tabela.Treeview', font=self.fonte_normal,
                         background=C['panel'], fieldbackground=C['panel'],
                         foreground=C['text'], rowheight=39, borderwidth=0,
                         relief='flat')
        estilo.map('Tabela.Treeview', background=[('selected', C['brand_soft'])],
                                              foreground=[('selected', C['text'])])
        estilo.configure('Tabela.Treeview.Heading', font=self.fonte_forte,
                         background=C['soft'], foreground=C['muted'],
                         padding=(8, 13), relief='flat', borderwidth=0)
        estilo.map('Tabela.Treeview.Heading', background=[('active', C['brand_soft'])])
        estilo.configure('Barra.Vertical.TScrollbar', background=C['soft'])

    def _criar_variaveis(self):
        self.var_descricao = tk.StringVar()
        self.var_valor = tk.StringVar()
        self.var_vencimento = tk.StringVar()
        self.var_tipo = tk.StringVar(value='Despesa')
        self.var_status = tk.StringVar(value='Pendente')
        self.var_busca = tk.StringVar()
        self.var_filtro_tipo = tk.StringVar(value='Todos os tipos')
        self.var_filtro_status = tk.StringVar(value='Todos os status')
        self.var_filtro_mes = tk.StringVar(value='Todos os meses')

    def _texto(self, pai, texto, *, fonte=None, cor=None, bg=None, **kwargs):
        return tk.Label(pai, text=texto, font=fonte or self.fonte_normal,
                        fg=cor or C['text'], bg=bg or C['panel'], **kwargs)

    def _painel(self, pai, **kwargs):
        return tk.Frame(pai, bg=C['panel'], highlightbackground=C['border'],
                        highlightthickness=1, **kwargs)

    def _montar_tela(self):
        principal = tk.Frame(self.janela, bg=C['bg'], padx=27, pady=22)
        principal.pack(fill='both', expand=True)

        cabecalho = tk.Frame(principal, bg=C['bg'])
        cabecalho.pack(fill='x', pady=(0, 18))
        marca = tk.Frame(cabecalho, bg=C['bg'])
        marca.pack(side='left')
        self._texto(marca, 'fluxo.', fonte=(self.fonte, 26, 'bold'),
                    cor=C['brand'], bg=C['bg']).pack(anchor='w')
        self._texto(marca, 'CONTAS A PAGAR E RECEBER',
                    fonte=(self.fonte, 9, 'bold'), cor=C['muted'], bg=C['bg']).pack(anchor='w')
        ttk.Button(cabecalho, text='+  Novo lançamento',
                   style='Principal.TButton', command=self.novo_lancamento).pack(side='right', pady=7)

        resumo = tk.Frame(principal, bg=C['bg'])
        resumo.pack(fill='x', pady=(0, 18))
        for i in range(4):
            resumo.columnconfigure(i, weight=1, uniform='resumo')
        self.metricas = {}
        cards = (
            ('saldo', 'SALDO REALIZADO', C['brand']),
            ('receber', 'A RECEBER', C['green']),
            ('pagar', 'A PAGAR', C['red']),
            ('atrasadas', 'CONTAS ATRASADAS', C['amber']),
        )
        for indice, (chave, titulo, destaque) in enumerate(cards):
            card = self._painel(resumo, padx=17, pady=15)
            card.grid(row=0, column=indice, sticky='nsew',
                      padx=(0, 9) if indice < 3 else 0)
            self._texto(card, titulo, fonte=(self.fonte, 9, 'bold'),
                        cor=C['muted']).pack(anchor='w')
            valor = self._texto(card, '—', fonte=(self.fonte, 19, 'bold'), cor=destaque)
            valor.pack(anchor='w', pady=(8, 1))
            legenda = self._texto(card, ' ', fonte=self.fonte_pequena, cor=C['muted'])
            legenda.pack(anchor='w')
            self.metricas[chave] = (valor, legenda)

        faixas = tk.Frame(principal, bg=C['bg'])
        faixas.pack(fill='x', pady=(0, 11))
        self.btn_aba_contas = self._aba(faixas, 'Lançamentos', 0)
        self.btn_aba_grafico = self._aba(faixas, 'Gráfico mensal', 1)
        self.lbl_aviso = self._texto(faixas, 'Indicadores acompanham os filtros',
                                    fonte=self.fonte_pequena, cor=C['muted'], bg=C['bg'])
        self.lbl_aviso.pack(side='right', pady=9)

        self.area = tk.Frame(principal, bg=C['bg'])
        self.area.pack(fill='both', expand=True)
        self.area_lancamentos = tk.Frame(self.area, bg=C['bg'])
        self.area_lancamentos.grid(row=0, column=0, sticky='nsew')
        self.area_grafico = self._painel(self.area, padx=24, pady=20)
        self.area_grafico.grid(row=0, column=0, sticky='nsew')
        self.area.columnconfigure(0, weight=1)
        self.area.rowconfigure(0, weight=1)
        self._montar_lancamentos()
        self._montar_grafico()
        self.mostrar_aba(0)


    def _aba(self, pai, texto, indice):
        botao = tk.Button(pai, text=texto, font=self.fonte_forte, bd=0,
                          relief='flat', padx=15, pady=10, cursor='hand2',
                          command=lambda: self.mostrar_aba(indice))
        botao.pack(side='left', padx=(0, 6))
        return botao

    def mostrar_aba(self, indice):
        self.aba_atual = indice
        if indice == 0:
            self.area_lancamentos.tkraise()
        else:
            self.area_grafico.tkraise()
            self.janela.after_idle(self.desenhar_grafico)
        for i, botao in enumerate((self.btn_aba_contas, self.btn_aba_grafico)):
            ativo = i == indice
            botao.configure(bg=C['panel'] if ativo else C['bg'],
                            fg=C['brand'] if ativo else C['muted'],
                            activebackground=C['brand_soft'])

    def _montar_lancamentos(self):
        self.area_lancamentos.columnconfigure(0, weight=1)
        self.area_lancamentos.columnconfigure(1, minsize=325)
        self.area_lancamentos.rowconfigure(0, weight=1)
        lista = self._painel(self.area_lancamentos, padx=16, pady=15)
        lista.grid(row=0, column=0, sticky='nsew', padx=(0, 14))
        painel_form = self._painel(self.area_lancamentos, padx=18, pady=13)
        painel_form.grid(row=0, column=1, sticky='nsew')
        self._montar_tabela(lista)
        self._montar_formulario(painel_form)

    def _montar_tabela(self, pai):
        topo = tk.Frame(pai, bg=C['panel'])
        topo.pack(fill='x')
        self._texto(topo, 'Seus lançamentos', fonte=self.fonte_secao).pack(side='left')
        ttk.Button(topo, text='Exportar CSV', style='Secundario.TButton',
                   command=self.exportar).pack(side='right')

        busca_linha = tk.Frame(pai, bg=C['panel'])
        busca_linha.pack(fill='x', pady=(15, 9))
        self.entry_busca = tk.Entry(busca_linha, textvariable=self.var_busca,
                                    font=self.fonte_normal, bg=C['soft'], fg=C['text'],
                                    insertbackground=C['text'], relief='flat',
                                    highlightthickness=1, highlightbackground=C['border'],
                                    highlightcolor=C['brand'])
        self.entry_busca.pack(side='left', fill='x', expand=True, ipady=9)
        self._texto(busca_linha, '  Buscar descrição', fonte=self.fonte_pequena,
                    cor=C['muted']).pack(side='left')

        filtros = tk.Frame(pai, bg=C['panel'])
        filtros.pack(fill='x', pady=(0, 11))
        for var, valores, largura in (
            (self.var_filtro_tipo, ('Todos os tipos',) + fm.TIPOS, 14),
            (self.var_filtro_status, ('Todos os status', 'Pendente', 'Pago', 'Atrasada'), 16),
            (self.var_filtro_mes, ('Todos os meses',), 16),
        ):
            combo = ttk.Combobox(filtros, textvariable=var, values=valores,
                                 style='Filtros.TCombobox', width=largura, state='readonly')
            combo.pack(side='left', padx=(0, 6))
            combo.bind('<<ComboboxSelected>>', lambda e: self.atualizar_tela())
            if var is self.var_filtro_mes:
                self.combo_mes = combo
        btn_limpar = tk.Button(filtros, text='Limpar', font=self.fonte_pequena,
                               fg=C['brand'], bg=C['panel'], relief='flat', bd=0,
                               cursor='hand2', command=self.limpar_filtros)
        btn_limpar.pack(side='right', pady=5)

        tabela_area = tk.Frame(pai, bg=C['panel'], highlightthickness=1,
                               highlightbackground=C['border'])
        tabela_area.pack(fill='both', expand=True)
        tabela_area.rowconfigure(0, weight=1)
        tabela_area.columnconfigure(0, weight=1)
        self.tabela = ttk.Treeview(tabela_area, style='Tabela.Treeview',
                                   columns=('descricao', 'tipo', 'vencimento', 'status', 'valor'),
                                   show='headings', selectmode='browse', height=4)
        colunas = (
            ('descricao', 'Descrição', 185, 'w'),
            ('tipo', 'Tipo', 85, 'center'),
            ('vencimento', 'Vencimento', 100, 'center'),
            ('status', 'Status', 90, 'center'),
            ('valor', 'Valor', 122, 'e'),
        )
        self.colunas = colunas
        for key, titulo, largura, alinhar in colunas:
            self.tabela.heading(key, text=titulo,
                                command=lambda k=key: self.ordenar_por(k))
            self.tabela.column(key, width=largura, minwidth=65, stretch=(key == 'descricao'),
                               anchor=alinhar)
        barra = ttk.Scrollbar(tabela_area, orient='vertical', command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.grid(row=0, column=0, sticky='nsew')
        barra.grid(row=0, column=1, sticky='ns')
        self.tabela.tag_configure('par', background=C['panel'])
        self.tabela.tag_configure('impar', background=C['soft'])
        self.tabela.tag_configure('atrasada', foreground=C['red'], background=C['red_soft'])
        self.tabela.tag_configure('pago', foreground=C['muted'])
        self.tabela.bind('<<TreeviewSelect>>', self._atualizar_acoes)
        self.tabela.bind('<Double-1>', lambda e: self.editar_selecionada())
        self.tabela.bind('<Delete>', lambda e: self.excluir_selecionada())
        self.lbl_vazio = self._texto(tabela_area,
                                    'Nada por aqui ainda.\nCadastre um lançamento ou limpe os filtros.',
                                    fonte=self.fonte_normal, cor=C['muted'],
                                    justify='center')

        acoes = tk.Frame(pai, bg=C['panel'])
        acoes.pack(fill='x', pady=(12, 1))
        self.lbl_contagem = self._texto(acoes, '', fonte=self.fonte_pequena, cor=C['muted'])
        self.lbl_contagem.pack(side='left', padx=(2, 8), pady=8)
        self.btn_excluir = ttk.Button(acoes, text='Excluir', style='Perigo.TButton',
                                      command=self.excluir_selecionada)
        self.btn_excluir.pack(side='right', padx=(7, 0))
        self.btn_status = ttk.Button(acoes, text='Marcar como pago',
                                     style='Secundario.TButton',
                                     command=self.alternar_status_selecionada)
        self.btn_status.pack(side='right', padx=(7, 0))
        self.btn_editar = ttk.Button(acoes, text='Editar', style='Secundario.TButton',
                                     command=self.editar_selecionada)
        self.btn_editar.pack(side='right')
        self._atualizar_acoes()
        self.var_busca.trace_add('write', lambda *args: self.atualizar_tela())

    def _campo(self, pai, rotulo, variavel, *, largura=28):
        self._texto(pai, rotulo, fonte=self.fonte_forte).pack(anchor='w', pady=(8, 3))
        entrada = tk.Entry(pai, textvariable=variavel, font=(self.fonte, 11),
                           bg=C['soft'], fg=C['text'], insertbackground=C['text'],
                           relief='flat', highlightthickness=1,
                           highlightbackground=C['border'], highlightcolor=C['brand'])
        entrada.pack(fill='x', ipady=6)
        return entrada

    def _montar_formulario(self, pai):
        cabecalho = tk.Frame(pai, bg=C['panel'])
        cabecalho.pack(fill='x')
        self.lbl_modo = self._texto(cabecalho, 'Novo lançamento', fonte=self.fonte_secao)
        self.lbl_modo.pack(side='left')
        self.btn_cancelar = tk.Button(cabecalho, text='Cancelar', font=self.fonte_pequena,
                                      fg=C['brand'], bg=C['panel'], bd=0, relief='flat',
                                      cursor='hand2', command=self.novo_lancamento)
        self.btn_cancelar.pack(side='right')
        self.lbl_ajuda = self._texto(pai, 'Preencha os dados e salve.',
                                    fonte=self.fonte_pequena, cor=C['muted'])
        self.lbl_ajuda.pack(anchor='w', pady=(2, 2))
        self.entry_descricao = self._campo(pai, 'Descrição', self.var_descricao)
        self.entry_valor = self._campo(pai, 'Valor (R$)', self.var_valor)
        self.entry_vencimento = self._campo(pai, 'Vencimento (dd/mm/aaaa)', self.var_vencimento)
        self._texto(pai, 'Tipo', fonte=self.fonte_forte).pack(anchor='w', pady=(8, 3))
        self.combo_tipo = ttk.Combobox(pai, textvariable=self.var_tipo,
                                       values=fm.TIPOS, state='readonly',
                                       style='Filtros.TCombobox')
        self.combo_tipo.pack(fill='x')
        self._texto(pai, 'Situação', fonte=self.fonte_forte).pack(anchor='w', pady=(8, 3))
        self.combo_status = ttk.Combobox(pai, textvariable=self.var_status,
                                         values=fm.STATUS_OPCOES, state='readonly',
                                         style='Filtros.TCombobox')
        self.combo_status.pack(fill='x')
        self.btn_salvar = ttk.Button(pai, text='Adicionar lançamento',
                                     style='Principal.TButton', command=self.salvar_formulario)
        self.btn_salvar.pack(fill='x', pady=(15, 6))
        self.entry_valor.bind('<FocusOut>', self._formatar_valor)

    def _montar_grafico(self):
        self._texto(self.area_grafico, 'Panorama mensal', fonte=self.fonte_secao).pack(anchor='w')
        self._texto(self.area_grafico, 'Receitas e despesas previstas por vencimento, considerando os filtros.',
                    fonte=self.fonte_pequena, cor=C['muted']).pack(anchor='w', pady=(4, 14))
        self.grafico = tk.Canvas(self.area_grafico, bg=C['panel'], highlightthickness=0)
        self.grafico.pack(fill='both', expand=True)
        self.grafico.bind('<Configure>', lambda event: self.desenhar_grafico())
        legenda = tk.Frame(self.area_grafico, bg=C['panel'])
        legenda.pack(anchor='center', pady=(12, 0))
        for texto, cor in (('Receitas', C['green']), ('Despesas', C['red'])):
            tk.Frame(legenda, bg=cor, width=12, height=12).pack(side='left', padx=(16, 6))
            self._texto(legenda, texto, cor=C['muted']).pack(side='left')

    def _registrar_atalhos(self):
        for entrada in (self.entry_descricao, self.entry_valor, self.entry_vencimento):
            entrada.bind('<Return>', lambda evento: self.salvar_formulario())
            entrada.bind('<KP_Enter>', lambda evento: self.salvar_formulario())
        self.janela.bind('<Escape>', lambda evento: self.novo_lancamento())
        self.janela.bind('<Control-f>', lambda evento: self.focar_busca())

    def _carregar(self):
        try:
            self.contas = fm.carregar_contas(self.caminho)
        except OSError as erro:
            messagebox.showerror('Erro ao abrir os dados', str(erro), parent=self.janela)
            self.contas = []

    def _transacao(self, alterar):
        """Só troca a lista na tela depois de gravar com sucesso no disco."""
        copia = [dict(conta) for conta in self.contas]
        try:
            resultado = alterar(copia)
            fm.salvar_contas(copia, self.caminho)
        except (ValueError, OSError) as erro:
            messagebox.showerror('Não foi possível salvar', str(erro), parent=self.janela)
            return False, None
        self.contas = copia
        return True, resultado

    def _filtros_ativos(self):
        return (bool(self.var_busca.get().strip()) or
                self.var_filtro_tipo.get() != 'Todos os tipos' or
                self.var_filtro_status.get() != 'Todos os status' or
                self.var_filtro_mes.get() != 'Todos os meses')

    def atualizar_tela(self):
        if self._silenciar_filtros:
            return
        self._atualizar_meses()
        selecionada = self._id_tabela()
        tipo = self.var_filtro_tipo.get()
        status = self.var_filtro_status.get()
        mes = self.meses_por_rotulo.get(self.var_filtro_mes.get())
        filtradas = fm.filtrar_contas(self.contas,
                                     texto=self.var_busca.get(),
                                     tipo=None if tipo == 'Todos os tipos' else tipo,
                                     status=None if status == 'Todos os status' else status,
                                     mes=mes)
        self.contas_exibidas = fm.ordenar_contas(filtradas, *self.ordem)
        self.tabela.delete(*self.tabela.get_children())
        self.ids_linhas.clear()
        for i, conta in enumerate(self.contas_exibidas):
            atrasada = fm.esta_atrasada(conta)
            status_exibido = 'Atrasada' if atrasada else conta['status']
            linha = self.tabela.insert('', 'end', values=(
                conta['descricao'], conta['tipo'], conta['vencimento'],
                status_exibido, ('+' if conta['tipo'] == 'Receita' else '−') +
                ' ' + fm.formatar_moeda(conta['valor'])),
                tags=('atrasada' if atrasada else
                      'pago' if conta['status'] == 'Pago' else
                      ('par' if i % 2 == 0 else 'impar'),))
            self.ids_linhas[linha] = conta['id']
            if selecionada == conta['id']:
                self.tabela.selection_set(linha)
        if self.contas_exibidas:
            self.lbl_vazio.place_forget()
        else:
            self.lbl_vazio.place(relx=0.5, rely=0.5, anchor='center')
        self.lbl_contagem.configure(text=f'{len(self.contas_exibidas)} de {len(self.contas)} contas')
        for chave, titulo, largura, alinhar in self.colunas:
            seta = '  ↓' if self.ordem == (chave, True) else \
                   '  ↑' if self.ordem == (chave, False) else ''
            self.tabela.heading(chave, text=titulo + seta)
        self._atualizar_acoes()
        self._atualizar_metricas()
        if self.aba_atual == 1:
            self.desenhar_grafico()

    def _atualizar_meses(self):
        self.meses_por_rotulo = {fm.rotulo_mes(m): m for m in fm.listar_meses(self.contas)}
        self.combo_mes.configure(values=('Todos os meses',) + tuple(self.meses_por_rotulo))
        if self.var_filtro_mes.get() not in ('Todos os meses', *self.meses_por_rotulo):
            self.var_filtro_mes.set('Todos os meses')

    def _atualizar_metricas(self):
        contas = self.contas_exibidas
        recebidas = sum(c['valor'] for c in contas if c['tipo'] == 'Receita' and c['status'] == 'Pago')
        pagas = sum(c['valor'] for c in contas if c['tipo'] == 'Despesa' and c['status'] == 'Pago')
        a_receber, a_pagar = fm.calcular_pendencias(contas)
        vencidas = sum(fm.esta_atrasada(c) for c in contas)
        dados = {
            'saldo': (fm.formatar_moeda(recebidas - pagas), 'Entradas menos saídas pagas'),
            'receber': (fm.formatar_moeda(a_receber), 'Receitas ainda pendentes'),
            'pagar': (fm.formatar_moeda(a_pagar), 'Despesas ainda pendentes'),
            'atrasadas': (str(vencidas), 'Vencidas e não pagas'),
        }
        for chave, (valor, legenda) in dados.items():
            self.metricas[chave][0].configure(text=valor)
            self.metricas[chave][1].configure(text=legenda)

    def _id_tabela(self):
        linhas = self.tabela.selection()
        return self.ids_linhas.get(linhas[0]) if linhas else None

    def _atualizar_acoes(self, evento=None):
        selecionada = self._id_tabela()
        disponivel = ['!disabled'] if selecionada is not None else ['disabled']
        for botao in (self.btn_editar, self.btn_status, self.btn_excluir):
            botao.state(disponivel)
        if selecionada is not None:
            conta = fm.buscar_conta(self.contas, selecionada)
            if conta:
                self.btn_status.configure(text='Marcar como ' +
                                          ('pendente' if conta['status'] == 'Pago' else 'pago'))

    def novo_lancamento(self, focar=True):
        """Sempre volta ao cadastro — mesmo que uma conta estivesse sendo editada."""
        self.id_edicao = None
        self.var_descricao.set('')
        self.var_valor.set('')
        self.var_vencimento.set(date.today().strftime(fm.FORMATO_DATA))
        self.var_tipo.set('Despesa')
        self.var_status.set('Pendente')
        self.lbl_modo.configure(text='Novo lançamento')
        self.lbl_ajuda.configure(text='Preencha os dados e salve.')
        self.btn_salvar.configure(text='Adicionar lançamento')
        self.btn_cancelar.pack_forget()
        if self.tabela.selection():
            self.tabela.selection_remove(*self.tabela.selection())
        self.mostrar_aba(0)
        if focar:
            self.entry_descricao.focus_set()

    def _formulario(self):
        return (self.var_descricao.get(), self.var_valor.get(), self.var_tipo.get(),
                self.var_vencimento.get(), self.var_status.get())

    def salvar_formulario(self):
        dados = self._formulario()
        if self.id_edicao is None:
            ok, conta = self._transacao(lambda lista: fm.adicionar_conta(lista, *dados))
            aviso = 'Lançamento adicionado.'
        else:
            numero = self.id_edicao
            if fm.buscar_conta(self.contas, numero) is None:
                messagebox.showwarning('Conta não encontrada', 'Essa conta não existe mais.',
                                       parent=self.janela)
                self.novo_lancamento()
                return
            ok, conta = self._transacao(lambda lista: fm.editar_conta(lista, numero, *dados))
            aviso = 'Alterações salvas. Pronto para cadastrar outra conta.'
        if not ok:
            return
        self.novo_lancamento(focar=False)
        self.atualizar_tela()
        self._avisar(aviso)
        if self._filtros_ativos():
            self._avisar(aviso + ' Confira os filtros se não encontrar o registro.')

    def editar_selecionada(self):
        numero = self._id_tabela()
        if numero is None:
            return
        conta = fm.buscar_conta(self.contas, numero)
        if conta is None:
            return
        self.id_edicao = numero
        self.var_descricao.set(conta['descricao'])
        self.var_valor.set(fm.formatar_numero(conta['valor']))
        self.var_vencimento.set(conta['vencimento'])
        self.var_tipo.set(conta['tipo'])
        self.var_status.set(conta['status'])
        self.lbl_modo.configure(text='Editar lançamento')
        self.lbl_ajuda.configure(text=f'Conta #{numero} · altere os dados e salve.')
        self.btn_salvar.configure(text='Salvar alterações')
        self.btn_cancelar.pack(side='right')
        self.mostrar_aba(0)
        self.entry_descricao.focus_set()
        self.entry_descricao.select_range(0, 'end')

    def alternar_status_selecionada(self):
        numero = self._id_tabela()
        if numero is None:
            return
        ok, status = self._transacao(lambda lista: fm.alternar_status(lista, numero))
        if not ok:
            return
        if self.id_edicao == numero:
            self.novo_lancamento(focar=False)
        self.atualizar_tela()
        self._avisar('Conta marcada como ' + status.lower() + '.')

    def excluir_selecionada(self):
        numero = self._id_tabela()
        if numero is None:
            return
        conta = fm.buscar_conta(self.contas, numero)
        if not conta:
            return
        if not messagebox.askyesno('Excluir lançamento',
                                   f'Excluir "{conta["descricao"]}" ({fm.formatar_moeda(conta["valor"])})?\n\n'
                                   'Esta ação não pode ser desfeita.', parent=self.janela):
            return
        ok, _ = self._transacao(lambda lista: fm.excluir_conta(lista, numero))
        if not ok:
            return
        if self.id_edicao == numero:
            self.novo_lancamento(focar=False)
        self.atualizar_tela()
        self._avisar('Lançamento excluído.')

    def _formatar_valor(self, evento=None):
        try:
            self.var_valor.set(fm.formatar_numero(fm.converter_valor(self.var_valor.get())))
        except ValueError:
            pass

    def ordenar_por(self, coluna):
        atual, reverso = self.ordem
        self.ordem = (coluna, not reverso if atual == coluna else False)
        self.atualizar_tela()

    def limpar_filtros(self):
        self._silenciar_filtros = True
        self.var_busca.set('')
        self.var_filtro_tipo.set('Todos os tipos')
        self.var_filtro_status.set('Todos os status')
        self.var_filtro_mes.set('Todos os meses')
        self._silenciar_filtros = False
        self.atualizar_tela()

    def focar_busca(self):
        self.mostrar_aba(0)
        self.entry_busca.focus_set()
        self.entry_busca.select_range(0, 'end')

    def exportar(self):
        if not self.contas_exibidas:
            messagebox.showinfo('Nada para exportar', 'Não há contas nos filtros atuais.',
                                parent=self.janela)
            return
        pasta = os.path.dirname(os.path.abspath(self.caminho))
        nome = filedialog.asksaveasfilename(parent=self.janela, title='Salvar relatório CSV',
                                            initialdir=pasta, initialfile='relatorio_contas.csv',
                                            defaultextension='.csv',
                                            filetypes=[('Arquivo CSV', '*.csv')])
        if not nome:
            return
        try:
            fm.exportar_csv(self.contas_exibidas, nome)
        except OSError as erro:
            messagebox.showerror('Erro ao exportar', str(erro), parent=self.janela)
            return
        self._avisar(f'{len(self.contas_exibidas)} contas exportadas para CSV.')

    def _avisar(self, texto):
        self.lbl_aviso.configure(text=texto, fg=C['green'])
        if self._aviso_agendado is not None:
            self.janela.after_cancel(self._aviso_agendado)
        self._aviso_agendado = self.janela.after(6500, lambda: self.lbl_aviso.configure(
            text='Indicadores acompanham os filtros', fg=C['muted']))

    def desenhar_grafico(self):
        canvas = self.grafico
        canvas.delete('all')
        largura = canvas.winfo_width()
        altura = canvas.winfo_height()
        if largura < 100 or altura < 100:
            return
        grupos = fm.agrupar_por_mes(self.contas_exibidas)
        if not grupos:
            canvas.create_text(largura / 2, altura / 2, text='Ainda não há dados para o gráfico.',
                               fill=C['muted'], font=self.fonte_normal)
            return
        # Até seis meses mais recentes para manter o gráfico legível.
        meses = list(grupos)[-6:]
        maior = max([v for mes in meses for v in grupos[mes].values()] + [1])
        esquerda, direita, cima, base = 64, 25, 34, altura - 52
        altura_util = max(1, base - cima)
        largura_util = max(1, largura - esquerda - direita)
        for i in range(5):
            y = base - altura_util * i / 4
            canvas.create_line(esquerda, y, largura - direita, y, fill=C['line'])
            canvas.create_text(esquerda - 10, y, text=fm.formatar_compacto(maior * i / 4),
                               anchor='e', fill=C['muted'], font=(self.fonte, 8))
        grupo_largura = largura_util / len(meses)
        barra_largura = min(32, grupo_largura * 0.27)
        for indice, mes in enumerate(meses):
            centro = esquerda + grupo_largura * (indice + 0.5)
            for deslocamento, chave, cor in ((-1, 'Receita', C['green']),
                                             (0, 'Despesa', C['red'])):
                valor = grupos[mes][chave]
                alto = altura_util * valor / maior
                x = centro + (deslocamento + 0.13) * barra_largura
                canvas.create_rectangle(x, base - alto, x + barra_largura * 0.8,
                                        base, fill=cor, outline='')
            canvas.create_text(centro, base + 18, text=fm.rotulo_mes(mes),
                               fill=C['muted'], font=self.fonte_pequena)
