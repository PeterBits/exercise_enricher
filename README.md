# Exercise Enricher

Script interactivo para enriquecer ejercicios de gimnasio utilizando **modelos locales de LLM** de Hugging Face. No requiere API keys ni conexión a internet después de la primera descarga del modelo.

## Características

- ✅ **Modelos 100% locales**: Sin necesidad de API keys ni costos por uso
- ✅ **Optimizado para CPU**: Funciona sin GPU NVIDIA
- ✅ **Eficiente con poca RAM**: Modelos diseñados para sistemas con 8GB o menos
- ✅ Enriquece ejercicios con información estructurada según el esquema Prisma
- ✅ Identifica el músculo principal trabajado
- ✅ Genera títulos, descripciones, aliases y notas en inglés y español
- ✅ Sistema de progreso incremental (resume desde donde se quedó)
- ✅ Manejo de errores robusto
- ✅ Privacidad total: tus datos nunca salen de tu ordenador

## Estructura del Proyecto

```
exercise-enricher/
├── enrich_exercises.py      # Script principal
├── requirements.txt          # Dependencias de Python
├── README.md                # Esta documentación
├── input/                   # Carpeta para archivo de entrada
│   └── exercicies_mock.json # Archivo con ejercicios a procesar
├── models/                  # Carpeta para caché de modelos (se crea automáticamente)
└── output/                  # Carpeta para archivos generados
    ├── enriched_exercises.json      # Ejercicios enriquecidos
    └── processing_progress.json     # Progreso del procesamiento
```

## Requisitos Previos

- Python 3.8 o superior
- **~3-6GB de espacio libre** en disco (para descargar el modelo)
- **8GB de RAM** recomendado (mínimo 6GB disponible)
- Conexión a internet (solo para la primera descarga del modelo)

## Instalación

### 1. Instalar dependencias

```bash
cd exercise-enricher
pip install -r requirements.txt
```

**Nota para Windows**: En algunos casos puede ser necesario instalar PyTorch con soporte CPU explícitamente:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 2. Verificar el archivo de entrada

El archivo `input/exercicies_mock.json` ya debería estar copiado. Si no está, cópialo desde:

```bash
copy ..\gainz_backend\prisma\exercicies_mock.json input\
```

### 3. Primera ejecución (descarga del modelo)

La primera vez que ejecutes el script, se descargará automáticamente el modelo seleccionado desde Hugging Face (esto puede tardar 5-15 minutos dependiendo de tu conexión). Los modelos se guardan en la carpeta `models/` y no será necesario descargarlos nuevamente.

## Uso

### Ejecución Básica

Simplemente ejecuta:
```bash
python enrich_exercises.py
```

### Flujo de Ejecución

1. **Selección de modelo**: El script te preguntará qué modelo local quieres usar:
   ```
   ============================================================
   Selecciona un Modelo Local de LLM
   ============================================================

   Modelos disponibles optimizados para CPU con poca RAM:

     1. Qwen 1.5B - Rápido y ligero (1.5B parámetros) [RECOMENDADO]
        RAM requerida: ~3GB RAM
        Velocidad: Rápido en CPU

     2. TinyLlama 1.1B - El más rápido (1.1B parámetros)
        RAM requerida: ~2.5GB RAM
        Velocidad: Muy rápido en CPU

     3. Phi-3 Mini - Mejor calidad pero más lento (3.8B parámetros)
        RAM requerida: ~5-6GB RAM
        Velocidad: Lento en CPU

   Ingresa tu elección (1-3):
   ```

2. **Carga del modelo**:
   - La primera vez descargará el modelo desde Hugging Face (5-15 minutos)
   - Las siguientes veces cargará el modelo desde la caché local (~30-60 segundos)

3. **Procesamiento**:
   - Muestra el progreso de cada ejercicio
   - Guarda los resultados inmediatamente después de cada ejercicio
   - Puedes interrumpir en cualquier momento con `Ctrl+C`

### Ejemplo de Uso

```bash
$ python enrich_exercises.py

============================================================
Exercise Enrichment Script - Modelos Locales
============================================================

============================================================
Selecciona un Modelo Local de LLM
============================================================

Modelos disponibles optimizados para CPU con poca RAM:

  1. Qwen 1.5B - Rápido y ligero (1.5B parámetros) [RECOMENDADO]
     RAM requerida: ~3GB RAM
     Velocidad: Rápido en CPU

  2. TinyLlama 1.1B - El más rápido (1.1B parámetros)
     RAM requerida: ~2.5GB RAM
     Velocidad: Muy rápido en CPU

  3. Phi-3 Mini - Mejor calidad pero más lento (3.8B parámetros)
     RAM requerida: ~5-6GB RAM
     Velocidad: Lento en CPU

Ingresa tu elección (1-3): 1

============================================================
Inicializando modelo local: qwen-1.5b
============================================================

Dispositivo: CPU
Descargando/cargando modelo (esto puede tardar la primera vez)...

✓ Modelo cargado exitosamente!

Loaded 685 exercises from C:\...\input\exercicies_mock.json

============================================================
Exercise Enrichment Progress
============================================================
Modelo: qwen-1.5b
Total exercises: 685
Already processed: 0
Remaining: 685
============================================================

[1/685] Processing exercise 31...
Processing exercise 31...
✓ Successfully enriched exercise 31

[2/685] Processing exercise 42...
...
```

## Archivos de Salida

### `output/enriched_exercises.json`

Contiene todos los ejercicios enriquecidos con la siguiente estructura:

```json
{
  "id": 31,
  "uuid": "f2733700-aa5d-4df7-bc52-1876ab4fb479",
  "original_category": {
    "id": 8,
    "name": "Arms"
  },
  "original_equipment": [
    {
      "id": 3,
      "name": "Dumbbell"
    }
  ],
  "original_translations": [...],
  "enriched_data": {
    "primary_muscle": {
      "name": "Hombros",
      "name_en": "Shoulders"
    },
    "translations": [
      {
        "name": "Lateral Raise Hold (Axe Hold)",
        "description": "Hold dumbbells with arms extended to the sides at shoulder height. Maintain the position for as long as possible while keeping proper form and core engaged.",
        "language": 2,
        "aliases": ["Side Raise Hold", "Dumbbell Lateral Hold"],
        "notes": ["Keep core engaged", "Avoid arching your back"]
      },
      {
        "name": "Elevación Lateral Sostenida",
        "description": "Sostén mancuernas con los brazos extendidos a los lados a la altura de los hombros. Mantén la posición el mayor tiempo posible manteniendo la forma correcta y el core contraído.",
        "language": 4,
        "aliases": ["Elevación de Hombros Sostenida", "Retención Lateral"],
        "notes": ["Mantén el core activado", "Evita arquear la espalda"]
      }
    ]
  },
  "processed_at": "2025-01-15T10:30:45.123456",
  "model": "qwen-1.5b"
}
```

### `output/processing_progress.json`

Rastrea el progreso del procesamiento:

```json
{
  "processed_exercise_ids": [31, 42, 57, ...],
  "last_updated": "2025-01-15T10:30:45.123456",
  "total_processed": 150,
  "model": "qwen-1.5b"
}
```

## Información Enriquecida

Para cada ejercicio, el modelo local genera (según el esquema Prisma):

| Campo | Descripción |
|-------|-------------|
| `primary_muscle` | Objeto con nombre del músculo en español (`name`) e inglés (`name_en`) |
| `translations` | Array con 2 objetos (inglés y español), cada uno contiene: |
| - `name` | Título del ejercicio |
| - `description` | Descripción detallada (2-4 oraciones con técnica correcta) |
| - `language` | ID del idioma (2=inglés, 4=español) |
| - `aliases` | Array de nombres alternativos o variaciones regionales |
| - `notes` | Array de consejos de ejecución, advertencias de seguridad |

## Comparación de Modelos

| Modelo | Parámetros | RAM Requerida | Velocidad CPU | Calidad | Tamaño Descarga |
|--------|-----------|---------------|---------------|---------|-----------------|
| **Qwen 1.5B** | 1.5B | ~3GB | Rápida | Buena | ~3GB |
| **TinyLlama 1.1B** | 1.1B | ~2.5GB | Muy rápida | Aceptable | ~2.2GB |
| **Phi-3 Mini** | 3.8B | ~5-6GB | Lenta | Muy buena | ~7.6GB |

### ¿Qué modelo elegir?

- **Tienes 8GB RAM o menos**: Usa **Qwen 1.5B** (recomendado) o **TinyLlama 1.1B**
- **Tienes 16GB RAM**: Puedes usar **Phi-3 Mini** para mejor calidad
- **Quieres velocidad**: Usa **TinyLlama 1.1B**
- **Quieres balance**: Usa **Qwen 1.5B** (mejor opción general)

## Reanudar Procesamiento

Si el script se interrumpe (por error o Ctrl+C), simplemente vuelve a ejecutarlo:

```bash
python enrich_exercises.py
```

El script:
- Detectará automáticamente qué ejercicios ya fueron procesados
- Continuará desde donde se quedó
- Preservará todos los datos ya guardados
- Cargará el mismo modelo que usaste anteriormente

## Reiniciar desde Cero

Si quieres volver a procesar todos los ejercicios:

```bash
rm output/enriched_exercises.json
rm output/processing_progress.json
```

O en Windows:
```cmd
del output\enriched_exercises.json
del output\processing_progress.json
```

## Solución de Problemas

### Error: "Falta instalar dependencias requeridas"

**Solución**: Instala las dependencias:
```bash
pip install -r requirements.txt
```

### Error al cargar el modelo o descarga muy lenta

**Solución 1**: Verifica tu conexión a internet (solo necesaria la primera vez)

**Solución 2**: Si la descarga falla, intenta con un modelo más pequeño (TinyLlama 1.1B)

**Solución 3**: Borra la carpeta `models/` y vuelve a intentar

### El ordenador se queda sin memoria (RAM)

**Solución**: Usa un modelo más pequeño:
1. Cierra otras aplicaciones
2. Ejecuta el script de nuevo y selecciona TinyLlama (opción 2)
3. Si persiste, puede que tu sistema tenga menos de 6GB RAM disponible

### El script es muy lento

Esto es esperado con CPU. Tiempos aproximados por ejercicio:
- **TinyLlama 1.1B**: ~10-20 segundos
- **Qwen 1.5B**: ~15-30 segundos
- **Phi-3 Mini**: ~30-60 segundos

Con 685 ejercicios, el proceso completo puede tomar **2-8 horas** dependiendo del modelo.

### Error: "torch not found"

**Solución para Windows**:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**Solución para Linux/Mac**:
```bash
pip install torch
```

### El modelo genera respuestas incorrectas o incompletas

Los modelos pequeños pueden tener limitaciones en calidad. **Soluciones**:

1. Usa el modelo **Qwen 1.5B** (mejor balance)
2. Si tienes 16GB RAM, prueba **Phi-3 Mini** (mejor calidad)
3. Revisa manualmente los resultados en `output/enriched_exercises.json`

## Características Avanzadas

### Añadir Nuevos Modelos

Puedes añadir más modelos editando el diccionario `AVAILABLE_MODELS` en `enrich_exercises.py` (líneas 42-61).

Modelos compatibles de Hugging Face:
- Cualquier modelo con formato "conversacional" (chat/instruct)
- Modelos pequeños optimizados para CPU (< 7B parámetros)

### Procesar Solo Algunos Ejercicios (para pruebas)

Para probar con un subconjunto de ejercicios, modifica la línea 549 en `main()`:

```python
exercises = load_exercises(INPUT_FILE)[:10]  # Solo los primeros 10
```

### Ajustar Parámetros de Generación

En la clase `LocalLLMProvider.generate_response()` (líneas 140-148) puedes ajustar:

```python
max_new_tokens=1200,    # Máximo de tokens a generar
temperature=0.5,        # Creatividad (0.0-1.0, menor = más conservador)
top_p=0.9,             # Nucleus sampling (0.0-1.0)
```

## Licencia

Este script es parte del proyecto GAINZ.
