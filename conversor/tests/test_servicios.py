from django.test import SimpleTestCase

from conversor.servicios import ErrorConversion, analizar_texto, convertir_numero


class ConversionesValidasTests(SimpleTestCase):
    def test_decimal_255_cabe_en_un_byte(self):
        r = convertir_numero("255", 10)
        self.assertEqual(r.decimal, 255)
        self.assertEqual(r.binario, "11111111")
        self.assertEqual(r.octal, "377")
        self.assertEqual(r.hexadecimal, "FF")
        self.assertEqual(r.bits_significativos, 8)
        self.assertEqual(r.bytes_necesarios, 1)

    def test_256_necesita_dos_bytes_y_se_rellena_a_16_bits(self):
        r = convertir_numero("256", 10)
        self.assertEqual(r.binario, "0000000100000000")
        self.assertEqual(r.binario_agrupado, "00000001 00000000")
        self.assertEqual(r.bits_significativos, 9)
        self.assertEqual(r.bytes_necesarios, 2)
        self.assertEqual(r.bits_relleno, 7)

    def test_binario_corto_se_completa_a_8_bits(self):
        r = convertir_numero("101", 2)
        self.assertEqual(r.decimal, 5)
        self.assertEqual(r.binario, "00000101")
        self.assertEqual(r.bits_significativos, 3)

    def test_hexadecimal_minusculas_y_prefijo(self):
        r = convertir_numero("0xff", 16)
        self.assertEqual(r.decimal, 255)
        self.assertEqual(r.hexadecimal, "FF")

    def test_octal_a_las_demas_bases(self):
        r = convertir_numero("777", 8)
        self.assertEqual(r.decimal, 511)
        self.assertEqual(r.hexadecimal, "1FF")
        self.assertEqual(r.binario, "0000000111111111")

    def test_limites_del_rango(self):
        cero = convertir_numero("0", 10)
        self.assertEqual(cero.binario, "00000000")
        self.assertEqual(cero.bits_significativos, 1)
        self.assertEqual(cero.bytes_necesarios, 1)

        maximo = convertir_numero("FFFF", 16)
        self.assertEqual(maximo.decimal, 65535)
        self.assertEqual(maximo.binario, "1" * 16)
        self.assertEqual(maximo.bytes_necesarios, 2)


class ErroresDeValidacionTests(SimpleTestCase):
    def test_entrada_vacia(self):
        with self.assertRaisesMessage(ErrorConversion, "vacío"):
            convertir_numero("   ", 10)

    def test_digito_invalido_para_binario(self):
        with self.assertRaisesMessage(ErrorConversion, "'2' no es válido en base 2"):
            convertir_numero("1021", 2)

    def test_digitos_invalidos_para_octal(self):
        with self.assertRaisesMessage(ErrorConversion, "'8', '9' no son válidos en base 8"):
            convertir_numero("1289", 8)

    def test_letra_invalida_en_decimal(self):
        with self.assertRaisesMessage(ErrorConversion, "'A' no es válido en base 10"):
            convertir_numero("12A", 10)

    def test_valor_negativo(self):
        with self.assertRaisesMessage(ErrorConversion, "No se permiten valores negativos"):
            convertir_numero("-5", 10)

    def test_fuera_de_rango(self):
        with self.assertRaisesMessage(ErrorConversion, "65 536 está fuera del rango"):
            convertir_numero("65536", 10)
        with self.assertRaisesMessage(ErrorConversion, "fuera del rango"):
            convertir_numero("10000", 16)

    def test_base_no_soportada(self):
        with self.assertRaisesMessage(ErrorConversion, "base 3 no es válida"):
            convertir_numero("12", 3)


class AnalisisUtf8Tests(SimpleTestCase):
    def test_enie_ocupa_dos_bytes_en_utf8(self):
        (n,) = analizar_texto("ñ")
        self.assertEqual(n.decimal, 241)
        self.assertEqual(n.punto_codigo, "U+00F1")
        self.assertEqual(n.hexadecimal, "0xF1")
        self.assertEqual(n.bytes_utf8, "C3 B1")
        self.assertEqual(n.bytes_utf8_binario, "11000011 10110001")
        self.assertEqual(n.cantidad_bytes, 2)

    def test_palabra_con_enie_ascii_y_euro(self):
        analisis = analizar_texto("Año€")
        self.assertEqual([c.cantidad_bytes for c in analisis], [1, 2, 1, 3])
        self.assertEqual(analisis[0].bytes_utf8, "41")
        self.assertEqual(analisis[3].punto_codigo, "U+20AC")
        self.assertEqual(analisis[3].bytes_utf8, "E2 82 AC")

    def test_emoji_ocupa_cuatro_bytes(self):
        (emoji,) = analizar_texto("😀")
        self.assertEqual(emoji.punto_codigo, "U+1F600")
        self.assertEqual(emoji.cantidad_bytes, 4)

    def test_texto_vacio_y_demasiado_largo(self):
        with self.assertRaisesMessage(ErrorConversion, "vacío"):
            analizar_texto("")
        with self.assertRaisesMessage(ErrorConversion, "máximo permitido es 20"):
            analizar_texto("a" * 21)
