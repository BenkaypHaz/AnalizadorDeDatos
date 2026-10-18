from dataclasses import dataclass

VALOR_MINIMO = 0
VALOR_MAXIMO = 65_535
MAX_CARACTERES = 20

BASES = {
    2: {"nombre": "Binario", "digitos": "01", "prefijo": "0b"},
    8: {"nombre": "Octal", "digitos": "01234567", "prefijo": "0o"},
    10: {"nombre": "Decimal", "digitos": "0123456789", "prefijo": ""},
    16: {"nombre": "Hexadecimal", "digitos": "0123456789ABCDEF", "prefijo": "0x"},
}

RANGO_DIGITOS = {2: "0 y 1", 8: "0 al 7", 10: "0 al 9", 16: "0 al 9 y A a F"}


class ErrorConversion(ValueError):
    pass


@dataclass(frozen=True)
class ResultadoNumero:
    entrada: str
    base_origen: int
    decimal: int
    binario: str
    binario_agrupado: str
    octal: str
    hexadecimal: str
    bits_significativos: int
    bytes_necesarios: int
    bits_relleno: int

    @property
    def bits_totales(self) -> int:
        return self.bytes_necesarios * 8

    @property
    def bytes_detalle(self) -> list[list[tuple[str, bool]]]:
        return [
            [(self.binario[i + j], i + j < self.bits_relleno) for j in range(8)]
            for i in range(0, len(self.binario), 8)
        ]


@dataclass(frozen=True)
class AnalisisCaracter:
    caracter: str
    representacion: str
    decimal: int
    punto_codigo: str
    hexadecimal: str
    bytes_utf8: str
    bytes_utf8_binario: str
    cantidad_bytes: int


def _formatear_es(numero: int) -> str:
    return f"{numero:,}".replace(",", " ")


def _limpiar_entrada(texto: str, base: int) -> str:
    limpio = texto.strip().replace("_", "").replace(" ", "")
    prefijo = BASES[base]["prefijo"]
    if prefijo and limpio.lower().startswith(prefijo):
        limpio = limpio[len(prefijo):]
    return limpio.upper()


def convertir_numero(texto: str, base: int) -> ResultadoNumero:
    if base not in BASES:
        raise ErrorConversion(
            f"La base {base} no es válida. Seleccione 2, 8, 10 o 16."
        )

    texto = (texto or "").strip()
    if not texto:
        raise ErrorConversion("Debe ingresar un número; el campo está vacío.")

    if texto.startswith("-"):
        raise ErrorConversion(
            f"No se permiten valores negativos ({texto}). "
            f"Ingrese un valor entre {VALOR_MINIMO} y {_formatear_es(VALOR_MAXIMO)}."
        )
    if texto.startswith("+"):
        texto = texto[1:]

    digitos = _limpiar_entrada(texto, base)
    if not digitos:
        raise ErrorConversion("Debe ingresar al menos un dígito después del prefijo.")

    permitidos = BASES[base]["digitos"]
    invalidos = sorted({c for c in digitos if c not in permitidos})
    if invalidos:
        lista = ", ".join(f"'{c}'" for c in invalidos)
        palabra = "El dígito" if len(invalidos) == 1 else "Los dígitos"
        verbo = "no es válido" if len(invalidos) == 1 else "no son válidos"
        raise ErrorConversion(
            f"{palabra} {lista} {verbo} en base {base} "
            f"({BASES[base]['nombre'].lower()}). "
            f"Solo se permiten los dígitos {RANGO_DIGITOS[base]}."
        )

    valor = int(digitos, base)
    if valor > VALOR_MAXIMO:
        raise ErrorConversion(
            f"El valor {_formatear_es(valor)} está fuera del rango permitido "
            f"({VALOR_MINIMO} a {_formatear_es(VALOR_MAXIMO)})."
        )

    bits = max(1, valor.bit_length())
    bytes_necesarios = (bits + 7) // 8
    binario = format(valor, f"0{bytes_necesarios * 8}b")
    binario_agrupado = " ".join(
        binario[i:i + 8] for i in range(0, len(binario), 8)
    )

    return ResultadoNumero(
        entrada=texto,
        base_origen=base,
        decimal=valor,
        binario=binario,
        binario_agrupado=binario_agrupado,
        octal=format(valor, "o"),
        hexadecimal=format(valor, "X"),
        bits_significativos=bits,
        bytes_necesarios=bytes_necesarios,
        bits_relleno=bytes_necesarios * 8 - bits,
    )


def _representar(caracter: str) -> str:
    if caracter == " ":
        return "␠ (espacio)"
    if caracter == "\t":
        return "⇥ (tabulación)"
    if not caracter.isprintable():
        return f"(control U+{ord(caracter):04X})"
    return caracter


def analizar_texto(texto: str) -> list[AnalisisCaracter]:
    if texto is None or texto == "":
        raise ErrorConversion("Debe ingresar un texto; el campo está vacío.")
    if len(texto) > MAX_CARACTERES:
        raise ErrorConversion(
            f"El texto tiene {len(texto)} caracteres; "
            f"el máximo permitido es {MAX_CARACTERES}."
        )

    resultado = []
    for caracter in texto:
        codigo = ord(caracter)
        codificado = caracter.encode("utf-8")
        resultado.append(
            AnalisisCaracter(
                caracter=caracter,
                representacion=_representar(caracter),
                decimal=codigo,
                punto_codigo=f"U+{codigo:04X}",
                hexadecimal=f"0x{codigo:X}",
                bytes_utf8=" ".join(f"{b:02X}" for b in codificado),
                bytes_utf8_binario=" ".join(f"{b:08b}" for b in codificado),
                cantidad_bytes=len(codificado),
            )
        )
    return resultado
