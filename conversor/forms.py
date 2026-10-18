from django import forms

from .servicios import (
    BASES,
    MAX_CARACTERES,
    ErrorConversion,
    analizar_texto,
    convertir_numero,
)


class NumeroForm(forms.Form):
    numero = forms.CharField(
        label="Número",
        max_length=64,
        error_messages={
            "required": "Debe ingresar un número; el campo está vacío.",
            "max_length": "El número es demasiado largo (máximo 64 caracteres).",
        },
        widget=forms.TextInput(
            attrs={"placeholder": "Ej.: 255, 1010, FF", "autocomplete": "off"}
        ),
    )
    base = forms.TypedChoiceField(
        label="Base de origen",
        choices=[(b, f"Base {b} — {d['nombre']}") for b, d in BASES.items()],
        coerce=int,
        initial=10,
        error_messages={
            "required": "Seleccione la base de origen.",
            "invalid_choice": "La base seleccionada no es válida. Use 2, 8, 10 o 16.",
        },
    )

    def clean(self):
        datos = super().clean()
        numero, base = datos.get("numero"), datos.get("base")
        if numero is not None and base is not None:
            try:
                datos["resultado"] = convertir_numero(numero, base)
            except ErrorConversion as error:
                self.add_error("numero", str(error))
        return datos


class TextoForm(forms.Form):
    texto = forms.CharField(
        label="Texto",
        max_length=MAX_CARACTERES,
        strip=False,
        error_messages={
            "required": "Debe ingresar un texto; el campo está vacío.",
            "max_length": (
                f"El texto supera el máximo de {MAX_CARACTERES} caracteres "
                "(tiene %(show_value)d)."
            ),
        },
        widget=forms.TextInput(
            attrs={"placeholder": "Ej.: Año ñandú €", "autocomplete": "off"}
        ),
    )

    def clean_texto(self):
        texto = self.cleaned_data["texto"]
        try:
            self.cleaned_data["analisis"] = analizar_texto(texto)
        except ErrorConversion as error:
            raise forms.ValidationError(str(error))
        return texto
