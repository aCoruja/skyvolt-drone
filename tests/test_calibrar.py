import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "calibrar", Path(__file__).resolve().parents[1] / "firmware/medidor-bancada/calibrar.py"
)
calibrar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibrar)


class TestCalibracao(unittest.TestCase):
    def test_reta(self):
        ganho, offset, erro = calibrar.ajustar([(0, 1), (100, 3), (200, 5)])
        self.assertAlmostEqual(ganho, 0.02)
        self.assertAlmostEqual(offset, 1)
        self.assertAlmostEqual(erro, 0)

    def test_dados_invalidos(self):
        for pontos in ([], [(1, 1)] * 3, [(0, 0), (1, 1), (float("nan"), 2)]):
            with self.assertRaises(ValueError):
                calibrar.ajustar(pontos)


if __name__ == "__main__":
    unittest.main()
