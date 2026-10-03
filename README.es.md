# Puesta en marcha de BrainChip AKD1000

Manual y herramientas en Python para preparar una tarjeta AKD1000 conectada por PCIe, comprobar
su funcionamiento y ejecutar modelos FBZ. El procedimiento parte del despliegue realizado en
mi TFG. Los resultados de estimación del ángulo de llegada se recogen en un apéndice del manual.

- [Manual en PDF, versión 1.2.2](manual/AKD1000_Bringup_Guide.pdf)
- [Fuente del manual](manual/main.tex)
- [English](README.md)

## Instalación y primera prueba

Extrae `akd1000-bringup.zip` y abre una terminal en la carpeta que contiene
`pyproject.toml`. Conserva esa carpeta: los ejemplos, el modelo y los manifiestos no se instalan
con el wheel de Python. Los comandos siguientes parten de la raíz del repositorio.

En Linux, con Python 3.11 instalado:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

En Windows, PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Si PowerShell bloquea la activación, usa `.\.venv\Scripts\python.exe` en lugar de `python`
y `python -m akd1000_bringup` en lugar de `akd1000-bringup`.

Elige **una** instalación del SDK, sin volver a crear el entorno. Para repetir la prueba incluida:

```text
python -m pip install -r requirements/reproducible.txt
```

Esta ruta fija Akida 2.19.1 y NumPy 2.4.6 en Python 3.11. No reproduce el experimento AoA completo.
Si necesitas el entorno de conversión, la [instalación oficial de MetaTF](https://doc.brainchipinc.com/installation.html)
consultada el 29 de septiembre de 2026 usa, como alternativa:

```text
python -m pip install "metatf==2.19.3"
```

En ambas rutas, instala después la herramienta y comprueba el modelo:

```text
python -m pip install -e . --no-deps
python -m pip check
akd1000-bringup --help
akd1000-bringup verify --id smoke --model models/akida_v1_smoke_test.fbz
python examples/00_simulator_smoke.py
```

La salida esperada es `[5, 5]`. El ejemplo ejecuta el simulador, guarda y carga el modelo y
comprueba el mapeo sobre un AKD1000 virtual. El archivo generado se guarda en `outputs/`;
el modelo original no se sobrescribe. Esta prueba no ejecuta la tarjeta física.

## Con la tarjeta conectada

Sigue primero el montaje y la instalación del controlador Linux del manual. Después ejecuta:

```text
akd1000-bringup doctor
akida devices
python examples/01_hardware_smoke.py
```

`doctor` devuelve 0 si el SDK se importa y detecta un dispositivo; 2 si falta el SDK o la tarjeta.
Solo compara versiones si se añade `--expected-akida VERSION`; una diferencia con hardware
detectado devuelve 1. En Raspberry Pi muestra las líneas de configuración PCIe con su sección,
pero no deduce la configuración efectiva. Confirma la enumeración con `lspci`.

No continúes con un modelo propio hasta que la prueba básica funcione.

## Ejecutar y medir un modelo

Este ejemplo en Linux usa archivos de una aplicación propia; sustituye las rutas:

```bash
akd1000-bringup run \
  --model models/model.fbz --input data/input.npy \
  --method forward --clock Performance --map AllNps \
  --output outputs/raw-output.npy

akd1000-bringup benchmark \
  --model models/model.fbz --input data/input.npy \
  --method forward --clock Performance --map AllNps \
  --warmup 8 --repetitions 1 --output outputs/trial-01
```

La herramienta acepta un tensor numérico de forma `(batch, *model.input_shape)` y una salida
NumPy. Solicita `hw_only=True`. La forma, tipo, rango, orden de canales y preprocesado deben
proceder del modelo. `--input-key NOMBRE` selecciona una matriz de un archivo NPZ. La salida
se guarda sin interpretar clases o ángulos; se añade `.npy` si falta esa extensión y se informa
de la ruta real. Los modelos con varias entradas o salidas requieren integración específica.

El benchmark ejecuta las muestras de una en una. Guarda `summary.json`, `latencies.csv` y
`host.json`: tiempos, configuración, hashes de modelo y datos, versiones, fecha UTC y diagnóstico
previo del host. El tiempo incluye las validaciones de entrada y salida de `run_raw`, la llamada
al SDK y la inferencia. Excluye carga de archivos, diagnóstico, mapeo, calentamiento y escritura.
No es latencia aislada del chip. Este comando no mide potencia; el manual explica las estadísticas
del SDK y los límites de la estimación de energía. Añade el commit del driver y el preprocesado
al registro del ensayo. Usa una carpeta de salida nueva para cada campaña.

## Comprobaciones y límites

La ejecución física del procedimiento revisado y la sesión con una
persona principiante siguen pendientes. Los modelos AoA, sus datos y sus checkpoints no se incluyen.

## Desarrollo y manual

```text
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m ruff check .
python manual/build.py
```

La compilación del PDF requiere XeLaTeX, BibTeX y los paquetes LaTeX indicados en `manual/main.tex`
(por ejemplo, una instalación de TeX Live o MiKTeX). `build.py` funciona en Windows y Linux y
guarda el PDF en `manual/AKD1000_Bringup_Guide.pdf`. Los archivos temporales quedan fuera del repositorio. En Linux también
puedes usar `make -C manual release`.

El contenido original se distribuye con licencia MIT. El SDK y el controlador de BrainChip no
se redistribuyen; consulta [los avisos de terceros](THIRD_PARTY_NOTICES.md).
