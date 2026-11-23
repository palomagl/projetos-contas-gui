"""
main.py
Ponto de entrada do sistema de Contas a Pagar e Receber.

Para rodar, abra o terminal dentro da pasta do projeto e digite:
    python main.py
"""

import os
from pathlib import Path
import tkinter as tk

from views.app_gui import AppContas

# O contas.txt fica sempre na mesma pasta deste arquivo,
# não importa de onde o programa foi aberto.
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_CONTAS = os.path.join(PASTA_PROJETO, 'contas.txt')


def inicializar_exemplo(caminho=CAMINHO_CONTAS):
    """Somente no primeiro uso, cria dados fictícios sem sobrescrever dados existentes.

    Um contas.txt existente, mesmo vazio, pertence ao usuário e é preservado.
    """
    if os.path.exists(caminho):
        return False
    exemplo = Path(PASTA_PROJETO) / 'docs' / 'exemplo_contas.txt'
    try:
        conteudo = exemplo.read_text(encoding='utf-8')
        with open(caminho, 'x', encoding='utf-8') as destino:
            destino.write(conteudo)
        return True
    except FileExistsError:
        return False


def main():
    inicializar_exemplo()
    janela = tk.Tk()
    AppContas(janela, CAMINHO_CONTAS)
    janela.mainloop()


if __name__ == '__main__':
    main()
