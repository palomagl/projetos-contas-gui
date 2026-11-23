"""Testes das funções de negócio, sem dependência de interface gráfica."""

import csv
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from services import finance_manager as fm
from main import inicializar_exemplo


class TestFinanceManager(unittest.TestCase):
    def setUp(self):
        self.contas = []
        self.diretorio = tempfile.TemporaryDirectory()
        self.arquivo = str(Path(self.diretorio.name) / 'contas.txt')

    def tearDown(self):
        self.diretorio.cleanup()

    def test_primeira_execucao_cria_exemplos_sem_sobrescrever(self):
        self.assertTrue(inicializar_exemplo(self.arquivo))
        contas = fm.carregar_contas(self.arquivo)
        self.assertEqual(len(contas), 18)
        self.assertEqual(set(fm.listar_meses(contas)), {'2026-11', '2026-12'})
        Path(self.arquivo).write_text('meus dados', encoding='utf-8')
        self.assertFalse(inicializar_exemplo(self.arquivo))
        self.assertEqual(Path(self.arquivo).read_text(encoding='utf-8'), 'meus dados')

    def test_valores_brasileiros(self):
        self.assertEqual(fm.converter_valor('1.200,50'), 1200.5)
        self.assertEqual(fm.converter_valor('1200.50'), 1200.5)
        self.assertEqual(fm.converter_valor('1.200'), 1200)

    def test_valores_invalidos(self):
        for texto in ('', 'abc', '0', '-10', 'NaN', 'inf'):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                fm.converter_valor(texto)

    def test_crud_status_e_saldo(self):
        c = fm.adicionar_conta(self.contas, 'Salário', '3500,00', 'Receita', '05/11/2026')
        self.assertEqual(c['id'], 1)
        fm.adicionar_conta(self.contas, 'Aluguel', '1200', 'Despesa', '10/11/2026')
        self.assertEqual(fm.calcular_pendencias(self.contas), (3500.0, 1200.0))
        self.assertEqual(fm.alternar_status(self.contas, 1), 'Pago')
        self.assertTrue(fm.editar_conta(self.contas, 2, 'Moradia', '1300',
                                        'Despesa', '10/11/2026', 'Pendente'))
        self.assertEqual(fm.calcular_resumo(self.contas), (3500.0, 1300.0, 2200.0))
        self.assertTrue(fm.excluir_conta(self.contas, 1))
        self.assertEqual(len(self.contas), 1)

    def test_salvar_e_carregar(self):
        fm.adicionar_conta(self.contas, 'Internet', '99,90', 'Despesa', '20/12/2026')
        fm.salvar_contas(self.contas, self.arquivo)
        self.assertEqual(fm.carregar_contas(self.arquivo), self.contas)

    def test_salvamento_atomico_preserva_arquivo_se_falhar(self):
        Path(self.arquivo).write_text('conteúdo anterior', encoding='utf-8')
        fm.adicionar_conta(self.contas, 'Internet', '99,90', 'Despesa', '20/12/2026')
        with patch.object(fm.os, 'replace', side_effect=OSError('simulado')):
            with self.assertRaises(OSError):
                fm.salvar_contas(self.contas, self.arquivo)
        self.assertEqual(Path(self.arquivo).read_text(encoding='utf-8'), 'conteúdo anterior')
        self.assertFalse(list(Path(self.diretorio.name).glob('*.tmp')))

    def test_filtro_acentos(self):
        fm.adicionar_conta(self.contas, 'Salário mensal', '3500', 'Receita', '05/11/2026')
        self.assertEqual(len(fm.filtrar_contas(self.contas, texto='salario')), 1)
        self.assertEqual(len(fm.filtrar_contas(self.contas, texto='aluguel')), 0)

    def test_atraso(self):
        c = fm.adicionar_conta(self.contas, 'Conta antiga', '200', 'Despesa', '01/01/2020')
        self.assertTrue(fm.esta_atrasada(c, date(2026, 11, 23)))
        c['status'] = 'Pago'
        self.assertFalse(fm.esta_atrasada(c, date(2026, 11, 23)))

    def test_exportacao_csv_com_descricao_segura(self):
        fm.adicionar_conta(self.contas, '=HYPERLINK("a")', '20', 'Despesa', '20/12/2026')
        destino = str(Path(self.diretorio.name) / 'saida.csv')
        fm.exportar_csv(self.contas, destino)
        with open(destino, encoding='utf-8-sig', newline='') as arq:
            linhas = list(csv.reader(arq, delimiter=';'))
        self.assertTrue(linhas[1][1].startswith("'="))

    def test_validar_descricao_nao_permite_quebra_de_linha(self):
        with self.assertRaises(ValueError):
            fm.validar_conta('Teste\nOutro', '10', 'Despesa', '10/12/2026', 'Pendente')


if __name__ == '__main__':
    unittest.main()
