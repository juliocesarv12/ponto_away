import unittest

from src.config import only_digits, parse_ids, redact
from src.texto import eh_placeholder, linhas_relevantes, opcoes_de_matricula, resumo_consulta, resumo_registro


class ConfigTest(unittest.TestCase):
    def test_only_digits(self):
        self.assertEqual(only_digits("123.456.789-00"), "12345678900")
        self.assertEqual(only_digits(""), "")

    def test_parse_ids(self):
        self.assertEqual(parse_ids("10, 20\n30"), {10, 20, 30})
        self.assertEqual(parse_ids("  "), set())
        self.assertEqual(parse_ids(None), set())

    def test_redact(self):
        self.assertEqual(redact("senha=abc123 falhou", "abc123"), "senha=*** falhou")
        self.assertEqual(redact("ok", ""), "ok")


class ResumoTest(unittest.TestCase):
    def test_extrai_horario(self):
        texto = "Portal\n\nRegistro do dia\n08:01 entrada\n12:02 saída\nmenu"
        linhas = linhas_relevantes(texto)
        self.assertEqual(linhas, ["08:01 entrada", "12:02 saída"])

    def test_resumo_registro_sem_texto(self):
        self.assertIn("Confere o horário", resumo_registro("   "))

    def test_resumo_consulta(self):
        self.assertIn("08:12", resumo_consulta("batida 08:12"))

    def test_placeholder_de_matricula(self):
        self.assertTrue(eh_placeholder("Selecione a matrícula"))
        self.assertFalse(eh_placeholder("Matrícula 12345"))
        self.assertFalse(eh_placeholder("12345"))

    def test_ignora_select_de_ano(self):
        self.assertEqual(opcoes_de_matricula(["Selecione", "2024", "2025"]), [])
        self.assertEqual(opcoes_de_matricula(["2024", "2025"]), [])
        self.assertEqual(opcoes_de_matricula(["Selecione a matrícula", "12345"]), ["12345"])
        self.assertEqual(opcoes_de_matricula(["2026", "12345"]), ["2026", "12345"])


if __name__ == "__main__":
    unittest.main()
