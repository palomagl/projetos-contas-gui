"""
main.py
Ponto de entrada do sistema de Contas a Pagar e Receber.

Para rodar, abra o terminal dentro da pasta do projeto e digite:
    python main.py
"""

import os
import tkinter as tk

from views.app_gui import AppContas

# O contas.txt fica sempre na mesma pasta deste arquivo,
# não importa de onde o programa foi aberto.
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_CONTAS = os.path.join(PASTA_PROJETO, 'contas.txt')


def main():
    janela = tk.Tk()
    AppContas(janela, CAMINHO_CONTAS)
    janela.mainloop()


if __name__ == '__main__':
    main()
