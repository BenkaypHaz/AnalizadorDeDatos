# Analizador de representación de datos

Aplicación web en **Python 3.12 + Django 5.2** que relaciona tres temas:

1. **Sistemas numéricos**: convierte un número de base 2, 8, 10 o 16 a las cuatro bases, completa el binario al siguiente límite de byte (8, 16, 24… bits) e indica los bits significativos y los bytes necesarios.
2. **Codificación de caracteres**: para un texto de hasta 20 caracteres muestra, por carácter, su código decimal, su punto de código `U+`, su valor hexadecimal y sus bytes en **UTF-8**.
3. **Ejecución en contenedores**: se empaqueta con Docker y se ejecuta con un límite de **256 MB de RAM y 1 CPU**.

---

## Estructura del proyecto

```
├── analizador/              # Proyecto Django (settings, urls, wsgi, asgi)
├── conversor/               # App Django
│   ├── servicios.py         # Lógica pura: conversión, validación y análisis UTF-8
│   ├── forms.py             # NumeroForm y TextoForm (validación + mensajes de error)
│   ├── views.py             # Vista única que procesa ambos formularios
│   ├── urls.py
│   ├── templates/conversor/ # base.html e inicio.html
│   └── tests/               # 24 pruebas automatizadas
├── Dockerfile               # Basado en python:3.12-slim, usuario no root, gunicorn
├── compose.yaml             # Puerto 8000, límites de 256 MB y 1 CPU
└── requirements.txt
```

La lógica está separada de Django (`servicios.py`), así se prueba de forma unitaria y los formularios solo traducen los errores (`ErrorConversion`) a mensajes en la página.

## Funcionalidad

### Conversión numérica

| Entrada | Base | Decimal | Binario (ajustado a bytes) | Octal | Hex | Bits sig. | Bytes |
|---|---|---|---|---|---|---|---|
| `101` | 2 | 5 | `00000101` | 5 | 5 | 3 | 1 |
| `255` | 10 | 255 | `11111111` | 377 | FF | 8 | 1 |
| `256` | 10 | 256 | `00000001 00000000` | 400 | 100 | 9 | 2 |
| `1A3F` | 16 | 6719 | `00011010 00111111` | 15077 | 1A3F | 13 | 2 |
| `FFFF` | 16 | 65535 | `11111111 11111111` | 177777 | FFFF | 16 | 2 |

- Bits significativos = `valor.bit_length()` (el 0 cuenta como 1 bit).
- Bytes = `ceil(bits / 8)`; el binario se rellena con ceros a la izquierda hasta `bytes × 8`.
- Se aceptan los prefijos opcionales `0b`, `0o`, `0x`, letras hexadecimales en minúscula y separadores `_`.

### Mensajes de error

| Caso | Ejemplo | Mensaje |
|---|---|---|
| Entrada vacía | ` ` | Debe ingresar un número; el campo está vacío. |
| Dígito inválido | `1021` en base 2 | El dígito '2' no es válido en base 2 (binario). Solo se permiten los dígitos 0 y 1. |
| Valor negativo | `-5` | No se permiten valores negativos (-5). Ingrese un valor entre 0 y 65 535. |
| Fuera de rango | `70000` | El valor 70 000 está fuera del rango permitido (0 a 65 535). |
| Texto vacío / largo | 25 caracteres | El texto supera el máximo de 20 caracteres (tiene 25). |

Los formularios usan `novalidate` para que sea el servidor (Django) quien valide y muestre estos mensajes.

### Análisis UTF-8 (ejemplo con `ñ`)

| Carácter | Decimal | Punto de código | Hex | Bytes UTF-8 | N.º bytes |
|---|---|---|---|---|---|
| A | 65 | U+0041 | 0x41 | 41 | 1 |
| ñ | 241 | U+00F1 | 0xF1 | C3 B1 | 2 |
| € | 8364 | U+20AC | 0x20AC | E2 82 AC | 3 |
| 😀 | 128512 | U+1F600 | 0x1F600 | F0 9F 98 80 | 4 |

La `ñ` tiene el punto de código 241 (cabe en un byte en Latin-1), pero UTF-8 la guarda en **2 bytes** (`110xxxxx 10xxxxxx` → `11000011 10110001`).

---

## Ejecución local (sin Docker)

```bash
python -m venv .venv
```
```bash
.venv\Scripts\activate
```
```bash
pip install -r requirements.txt
```
```bash
python manage.py runserver
```

Abrir <http://localhost:8000>. En Linux/macOS se activa el entorno con `source .venv/bin/activate`.

## Pruebas automatizadas

```bash
python manage.py test -v 2
```

24 pruebas en `conversor/tests/`:

- **Conversiones válidas**: 255 → 1 byte; 256 → 16 bits con 7 de relleno; `101₂` → `00000101`; `0xff`; octal `777`; límites 0 y 65 535.
- **Errores de base y rango**: vacío, dígitos inválidos en base 2, 8 y 10, negativos, fuera de rango, base no soportada.
- **UTF-8**: `ñ` → `U+00F1`, `C3 B1`, 2 bytes; `Año€`; emoji de 4 bytes; texto vacío y de más de 20 caracteres.
- **Vistas Django**: GET, conversión válida en la página, errores renderizados y análisis de `niño` (5 bytes).

Dentro del contenedor:

```bash
docker exec analizador-datos python manage.py test
```

---

## Docker

### Con Docker Compose (recomendado)

Construir y ejecutar en segundo plano (aplica los límites de `compose.yaml`):

```bash
docker compose up -d --build
```

Ver estado, logs y consumo de recursos:

```bash
docker compose ps
```
```bash
docker compose logs -f
```
```bash
docker stats analizador-datos
```

Detener y eliminar:

```bash
docker compose down
```

### Con `docker` directamente

```bash
docker build -t analizador-datos:1.0 .
```
```bash
docker run -d --name analizador-datos -p 8000:8000 --memory=256m --cpus=1 -e DJANGO_DEBUG=0 analizador-datos:1.0
```

### Límites de recursos

En `compose.yaml`:

```yaml
deploy:
  resources:
    limits:
      cpus: "1.0"
      memory: 256M
```

Comprobación de que Docker aplicó los límites (256 MiB = 268 435 456 bytes, 1 CPU = 10⁹ nanoCPUs):

```bash
docker inspect analizador-datos --format "Memory={{.HostConfig.Memory}} NanoCpus={{.HostConfig.NanoCpus}}"
```

### Evidencia de `docker stats`

Salida obtenida con el contenedor en ejecución:

```
$ docker inspect analizador-datos --format "Memory={{.HostConfig.Memory}} NanoCpus={{.HostConfig.NanoCpus}}"
Memory=268435456 NanoCpus=1000000000

$ docker stats --no-stream analizador-datos
CONTAINER ID   NAME               CPU %     MEM USAGE / LIMIT   MEM %     NET I/O          BLOCK I/O   PIDS
6e683af5d67e   analizador-datos   0.01%     74.82MiB / 256MiB   29.23%    26.6kB / 322kB   0B / 0B     3
```

La columna `MEM USAGE / LIMIT` muestra el tope de **256MiB**; la aplicación (gunicorn con 2 workers) usa unos 75 MiB.

---

## Explicación técnica

### Recursos de la arquitectura de Von Neumann que usa la aplicación

- **CPU (unidad de control + ALU)**: ejecuta las instrucciones del intérprete de Python. La ALU hace las operaciones de la conversión: divisiones y residuos sucesivos para cambiar de base, desplazamientos de bits para `bit_length()` y operaciones de máscara para armar los bytes UTF-8 (`110xxxxx 10xxxxxx`).
- **Memoria principal (RAM)**: siguiendo el principio de *programa almacenado*, en la misma memoria residen las **instrucciones** (el bytecode de Python/Django) y los **datos** (el número ingresado, sus cadenas binaria/octal/hex y los bytes del texto). Toda la aplicación trabaja en RAM; no usa base de datos.
- **Registros y bus**: los valores viajan por el bus entre RAM y CPU; el ancho de palabra y la organización en **bytes** de la memoria es justo lo que la app muestra al ajustar el binario a 8, 16, 24… bits.
- **Entrada/Salida**: la red (petición HTTP del formulario y respuesta HTML) es el dispositivo de E/S; el teclado y la pantalla del usuario llegan a la app a través de ella.

### ¿Por qué el contenedor comparte el kernel del host?

Un contenedor **no es una máquina virtual**: no incluye un kernel propio ni emula hardware. Es un **proceso normal del host** aislado con funciones del propio kernel de Linux:

- **Namespaces**: le dan su propia vista de procesos (PID), red, sistema de archivos (mount), usuarios y hostname.
- **cgroups**: limitan y contabilizan los recursos. Los `256 MB` y `1 CPU` se aplican como reglas de cgroups en el kernel del host, y `docker stats` lee esas mismas estadísticas.

La imagen `python:3.12-slim` solo aporta el *espacio de usuario* (bibliotecas de Debian, el intérprete de Python y la app); las llamadas al sistema (`read`, `write`, `socket`…) las atiende el kernel compartido. Por eso arranca en segundos y ocupa poca memoria. Se comprueba con `uname -r`, que devuelve el mismo kernel dentro y fuera del contenedor. En Windows/macOS, Docker Desktop ejecuta un kernel Linux ligero (WSL2), y todos los contenedores comparten **ese** kernel; en esta máquina `docker exec analizador-datos uname -r` devuelve `5.15.167.4-microsoft-standard-WSL2`.

---

## Entrega

- Repositorio: <https://github.com/BenkaypHaz/AnalizadorDeDatos>
- Video (máx. 2 min): _(agregar enlace)_. Guion sugerido:
  1. `docker compose up -d --build` y `docker compose ps` (contenedor *healthy*).
  2. Conversión válida: `1A3F` en base 16.
  3. Error de validación: `1021` en base 2, o `70000` en base 10.
  4. Texto con ñ: `Año ñandú €`.
  5. `docker exec analizador-datos python manage.py test` (24 pruebas OK).
  6. `docker stats analizador-datos` mostrando el límite de 256MiB.
