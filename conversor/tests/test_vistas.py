from django.test import SimpleTestCase
from django.urls import reverse


class VistaInicioTests(SimpleTestCase):
    url = reverse("conversor:inicio")

    def enviar_numero(self, numero, base):
        return self.client.post(
            self.url, {"accion": "numero", "num-numero": numero, "num-base": base}
        )

    def enviar_texto(self, texto):
        return self.client.post(self.url, {"accion": "texto", "txt-texto": texto})

    def test_get_muestra_ambos_formularios(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "conversor/inicio.html")
        self.assertContains(respuesta, 'name="num-numero"')
        self.assertContains(respuesta, 'name="txt-texto"')

    def test_conversion_valida_muestra_las_cuatro_bases(self):
        respuesta = self.enviar_numero("1A3F", 16)
        self.assertEqual(respuesta.status_code, 200)
        resultado = respuesta.context["resultado"]
        self.assertEqual(resultado.decimal, 6719)
        self.assertContains(respuesta, "00011010 00111111")
        self.assertContains(respuesta, "15077")
        self.assertContains(respuesta, "<strong>2</strong><span>bytes necesarios</span>")
        self.assertContains(respuesta, 'class="bit relleno"', count=3)

    def test_error_de_base_se_muestra_en_la_pagina(self):
        respuesta = self.enviar_numero("19", 8)
        self.assertNotIn("resultado", respuesta.context)
        self.assertContains(respuesta, "no es válido en base 8")

    def test_error_de_rango_y_vacio(self):
        self.assertContains(self.enviar_numero("70000", 10), "fuera del rango")
        self.assertContains(self.enviar_numero("", 10), "el campo está vacío")
        self.assertContains(self.enviar_numero("-1", 10), "valores negativos")

    def test_base_no_permitida_desde_el_formulario(self):
        self.assertContains(self.enviar_numero("12", 7), "La base seleccionada no es válida")

    def test_texto_con_enie_muestra_bytes_utf8(self):
        respuesta = self.enviar_texto("niño")
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "U+00F1")
        self.assertContains(respuesta, "C3 B1")
        self.assertEqual(respuesta.context["total_bytes"], 5)

    def test_texto_de_mas_de_20_caracteres(self):
        respuesta = self.enviar_texto("x" * 25)
        self.assertNotIn("analisis", respuesta.context)
        self.assertContains(respuesta, "máximo de 20 caracteres")
