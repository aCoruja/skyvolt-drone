#!/usr/bin/env python3
"""Ajuste linear de dados CSV com colunas adc_mv e referencia."""
import argparse
import csv
import math


def ajustar(pontos):
    if len(pontos) < 3 or any(not math.isfinite(x) or not math.isfinite(y) for x, y in pontos):
        raise ValueError("São necessários pelo menos três pontos finitos")
    mx = sum(x for x, _ in pontos) / len(pontos)
    my = sum(y for _, y in pontos) / len(pontos)
    denominador = sum((x - mx) ** 2 for x, _ in pontos)
    if denominador == 0:
        raise ValueError("As leituras ADC precisam variar")
    ganho = sum((x - mx) * (y - my) for x, y in pontos) / denominador
    offset = my - ganho * mx
    erro = max(abs(ganho * x + offset - y) for x, y in pontos)
    return ganho, offset, erro


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="arquivo CSV com colunas adc_mv e referencia")
    args = parser.parse_args()
    with open(args.csv, newline="", encoding="utf-8") as arquivo:
        pontos = [(float(row["adc_mv"]), float(row["referencia"]))
                  for row in csv.DictReader(arquivo)]
    ganho, offset, erro = ajustar(pontos)
    print(f"ganho={ganho:.9g} por mV; offset={offset:.9g}; erro máximo no ajuste={erro:.9g}")
    print("Valide com pontos independentes; o ajuste não demonstra a precisão final.")


if __name__ == "__main__":
    main()
