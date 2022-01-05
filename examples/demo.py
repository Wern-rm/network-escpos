# -*- coding: utf-8 -*-
"""
    Demo
    ~~~~~
    Python network esc/pos printer API demo.
    :copyright: (c) 2021 by WeRn <wern@lightning-digital.org>.
    :license: MIT, see LICENSE for more details.
"""

from network_escpos import NetworkPrinter


printer = NetworkPrinter(host="192.168.0.100", port=9100, timeout=5, autoclose=True)


def demo_print():
    printer.set(align='left', height=2, width=2, custom_size=True)
    printer.text_ln('Demo network-escpos')
    printer.ln(count=2)

    printer.set(align='center', width=5, height=5, bold=True, custom_size=True)
    printer.text_ln('Hello Workd')
    printer.ln()

    printer.set(align='right', width=1, height=1, custom_size=True)
    printer.text_ln('Test success!')

    printer.cut(mode='FULL')


if __name__ == '__main__':
    demo_print()