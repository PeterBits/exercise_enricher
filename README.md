# Exercise Enricher

Script para enriquecer ejercicios de gimnasio utilizando la API de Claude (Anthropic). Procesa ejercicios desde un archivo JSON y genera información detallada en inglés y español.

## Características

- ✅ Enriquece ejercicios con información estructurada
- ✅ Identifica el músculo principal trabajado
- ✅ Genera títulos y descripciones en inglés y español
- ✅ Sistema de progreso incremental (resume desde donde se quedó)
- ✅ Manejo de errores robusto
- ✅ Rate limiting automático

## Estructura del Proyecto

```
exercise-enricher/
├── enrich_exercises.py      # Script principal
├── requirements.txt          # Dependencias de Python
├── .env.example             # Ejemplo de configuración
├── README.md                # Esta documentación
├── input/                   # Carpeta para archivo de entrada
│   └── exercicies_mock.json # Archivo con ejercicios a procesar
└── output/                  # Carpeta para archivos generados
    ├── enriched_exercises.json      # Ejercicios enriquecidos
    └── processing_progress.json     # Progreso del procesamiento
```

## Requisitos Previos

- Python 3.7 o superior
- Una API key de Anthropic (Claude)

## Instalación

### 1. Clonar o navegar al directorio

```bash
cd exercise-enricher
```

### 2. Crear un entorno virtual (recomendado)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar API Key

Copia el archivo de ejemplo y añade tu API key:

```bash
cp .env.example .env
```

Edita `.env` y añade tu API key de Anthropic:

```
ANTHROPIC_API_KEY=tu-api-key-aqui
```

**Alternativa:** También puedes configurar la variable de entorno directamente:

**Windows CMD:**
```cmd
set ANTHROPIC_API_KEY=tu-api-key-aqui
```

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY='tu-api-key-aqui'
```

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY='tu-api-key-aqui'
```

### 5. Preparar el archivo de entrada

Crea la carpeta `input` y copia el archivo de ejercicios:

```bash
mkdir input
```

Copia `exercicies_mock.json` a la carpeta `input/`:

```bash
# Desde la raíz del proyecto GAINZ
cp gainz_backend/prisma/exercicies_mock.json exercise-enricher/input/
```

## Uso

### Ejecutar el script

```bash
python enrich_exercises.py
```

### Proceso de ejecución

El script:

1. Carga los ejercicios desde `input/exercicies_mock.json`
2. Verifica qué ejercicios ya fueron procesados (en `output/processing_progress.json`)
3. Procesa cada ejercicio pendiente:
   - Envía el ejercicio a Claude AI
   - Recibe información enriquecida (músculo principal, títulos, descripciones)
   - Guarda el resultado inmediatamente
   - Actualiza el progreso
4. Incluye un delay de 1 segundo entre peticiones para evitar rate limiting

### Interrumpir y reanudar

- Puedes interrumpir el proceso en cualquier momento con `Ctrl+C`
- El progreso se guarda automáticamente después de cada ejercicio
- Al volver a ejecutar el script, continuará desde donde se quedó

## Archivos de Salida

### `output/enriched_exercises.json`

Contiene todos los ejercicios enriquecidos. Estructura de cada ejercicio:

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
    "primary_muscle": "Shoulders",
    "title_en": "Lateral Raise Hold (Axe Hold)",
    "title_es": "Elevación Lateral Sostenida",
    "description_en": "Hold dumbbells with arms extended to the sides at shoulder height...",
    "description_es": "Sostén mancuernas con los brazos extendidos a los lados a la altura de los hombros..."
  },
  "processed_at": "2024-01-15T10:30:45.123456"
}
```

### `output/processing_progress.json`

Rastrea el progreso del procesamiento:

```json
{
  "processed_exercise_ids": [31, 42, 57, ...],
  "last_updated": "2024-01-15T10:30:45.123456",
  "total_processed": 150
}
```

## Información Enriquecida

Para cada ejercicio, Claude AI genera:

| Campo | Descripción |
|-------|-------------|
| `primary_muscle` | Músculo principal trabajado (ej: "Chest", "Biceps", "Quadriceps") |
| `title_en` | Título claro y conciso en inglés |
| `title_es` | Título traducido al español |
| `description_en` | Descripción detallada en inglés (2-4 oraciones) |
| `description_es` | Descripción detallada en español (2-4 oraciones) |

## Solución de Problemas

### Error: "ANTHROPIC_API_KEY environment variable not set"

**Solución:** Configura tu API key como variable de entorno (ver paso 4 de instalación)

### Error: "Input file not found"

**Solución:** Asegúrate de que `input/exercicies_mock.json` existe

### Error: "anthropic library not found"

**Solución:** Instala las dependencias con `pip install -r requirements.txt`

### El script es muy lento

**Solución:** Esto es normal. El script incluye un delay de 1 segundo entre peticiones para evitar rate limiting. Con miles de ejercicios, puede tomar varias horas.

### Rate limiting / Too many requests

**Solución:** El script ya incluye delays. Si aún así ocurre, aumenta el valor de `delay_seconds` en el código:

```python
enricher.process_all_exercises(exercises, delay_seconds=2.0)  # Aumentar a 2 segundos
```

## Reiniciar desde Cero

Si quieres volver a procesar todos los ejercicios:

```bash
# Elimina los archivos de salida
rm output/enriched_exercises.json
rm output/processing_progress.json
```

## Obtener una API Key de Anthropic

1. Visita [console.anthropic.com](https://console.anthropic.com/)
2. Crea una cuenta o inicia sesión
3. Ve a Settings → API Keys
4. Crea una nueva API key
5. Cópiala y guárdala en tu archivo `.env`

## Costos

- El modelo usado es `claude-3-5-sonnet-20241022`
- Cada ejercicio usa aproximadamente 500-1000 tokens
- Consulta los precios actuales en [anthropic.com/pricing](https://www.anthropic.com/pricing)

## Licencia

Este script es parte del proyecto GAINZ.
