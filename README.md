# Exercise Enricher

Script interactivo para enriquecer ejercicios de gimnasio utilizando IA. Soporta múltiples proveedores de IA: **Claude (Anthropic)** y **OpenAI (GPT-4o)**.

## Características

- ✅ **Soporte multi-proveedor**: Elige entre Claude o OpenAI
- ✅ Enriquece ejercicios con información estructurada
- ✅ Identifica el músculo principal trabajado
- ✅ Genera títulos y descripciones en inglés y español
- ✅ Sistema de progreso incremental (resume desde donde se quedó)
- ✅ Configuración flexible: lee API keys desde .env o las pide interactivamente
- ✅ Manejo de errores robusto
- ✅ Rate limiting automático

## Estructura del Proyecto

```
exercise-enricher/
├── enrich_exercises.py      # Script principal
├── requirements.txt          # Dependencias de Python
├── .env.example             # Ejemplo de configuración
├── .env                     # Tu configuración (crear desde .env.example)
├── README.md                # Esta documentación
├── input/                   # Carpeta para archivo de entrada
│   └── exercicies_mock.json # Archivo con ejercicios a procesar
└── output/                  # Carpeta para archivos generados
    ├── enriched_exercises.json      # Ejercicios enriquecidos
    └── processing_progress.json     # Progreso del procesamiento
```

## Requisitos Previos

- Python 3.7 o superior
- Una API key de Anthropic (Claude) o OpenAI (GPT)

## Instalación

### 1. Instalar dependencias

```bash
cd exercise-enricher
pip install -r requirements.txt
```

### 2. Configurar API Keys (Opcional pero Recomendado)

Copia el archivo de ejemplo:
```bash
copy .env.example .env
```

Edita el archivo `.env` y añade tu(s) API key(s):

```env
# Para usar Claude (Anthropic)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxx

# Para usar OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

> **Nota**: Solo necesitas configurar el API key del proveedor que vayas a usar.

### 3. Verificar el archivo de entrada

El archivo `input/exercicies_mock.json` ya debería estar copiado. Si no está, cópialo desde:

```bash
copy ..\gainz_backend\prisma\exercicies_mock.json input\
```

## Uso

### Ejecución Básica

Simplemente ejecuta:
```bash
python enrich_exercises.py
```

### Flujo de Ejecución

1. **Selección de proveedor**: El script te preguntará qué IA quieres usar:
   ```
   Select AI Provider
   ============================================================
   Available AI providers:
     1. Claude (Anthropic) - Claude 3.5 Sonnet
     2. OpenAI - GPT-4o

   Enter your choice (1 or 2):
   ```

2. **API Key**:
   - Si configuraste el API key en `.env`, el script lo cargará automáticamente ✓
   - Si no encuentra el API key, te lo pedirá de forma segura (no se muestra al escribir)

3. **Procesamiento**:
   - Muestra el progreso de cada ejercicio
   - Guarda los resultados inmediatamente después de cada ejercicio
   - Puedes interrumpir en cualquier momento con `Ctrl+C`

### Ejemplo de Uso

```bash
$ python enrich_exercises.py

============================================================
Exercise Enrichment Script
============================================================

============================================================
Select AI Provider
============================================================

Available AI providers:
  1. Claude (Anthropic) - Claude 3.5 Sonnet
  2. OpenAI - GPT-4o

Enter your choice (1 or 2): 2

✓ API key loaded from .env file for OpenAI
Loaded 685 exercises from C:\...\input\exercicies_mock.json

============================================================
Exercise Enrichment Progress
============================================================
AI Provider: OPENAI
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
    "primary_muscle": "Shoulders",
    "title_en": "Lateral Raise Hold (Axe Hold)",
    "title_es": "Elevación Lateral Sostenida",
    "description_en": "Hold dumbbells with arms extended to the sides at shoulder height. Maintain the position for as long as possible while keeping proper form and core engaged.",
    "description_es": "Sostén mancuernas con los brazos extendidos a los lados a la altura de los hombros. Mantén la posición el mayor tiempo posible manteniendo la forma correcta y el core contraído."
  },
  "processed_at": "2024-01-15T10:30:45.123456",
  "ai_provider": "openai"
}
```

### `output/processing_progress.json`

Rastrea el progreso del procesamiento:

```json
{
  "processed_exercise_ids": [31, 42, 57, ...],
  "last_updated": "2024-01-15T10:30:45.123456",
  "total_processed": 150,
  "ai_provider": "openai"
}
```

## Información Enriquecida

Para cada ejercicio, la IA genera:

| Campo | Descripción |
|-------|-------------|
| `primary_muscle` | Músculo principal trabajado (ej: "Chest", "Biceps", "Quadriceps") |
| `title_en` | Título claro y conciso en inglés |
| `title_es` | Título traducido al español |
| `description_en` | Descripción detallada en inglés (2-4 oraciones con técnica correcta) |
| `description_es` | Descripción detallada en español (2-4 oraciones con técnica correcta) |

## Comparación de Proveedores

| Característica | Claude (Anthropic) | OpenAI (GPT-4o) |
|----------------|-------------------|-----------------|
| Modelo | Claude 3.5 Sonnet | GPT-4o |
| Calidad | Excelente | Excelente |
| Velocidad | Rápida | Rápida |
| Coste aprox. | ~$3 por 1M tokens | ~$2.50 por 1M tokens |
| API Key | [console.anthropic.com](https://console.anthropic.com/settings/keys) | [platform.openai.com](https://platform.openai.com/api-keys) |

> **Nota**: Los costes son aproximados. Cada ejercicio usa ~500-1000 tokens. Consulta los precios actuales en las páginas oficiales.

## Reanudar Procesamiento

Si el script se interrumpe (por error, falta de créditos, o Ctrl+C), simplemente vuelve a ejecutarlo:

```bash
python enrich_exercises.py
```

El script:
- Detectará automáticamente qué ejercicios ya fueron procesados
- Continuará desde donde se quedó
- Preservará todos los datos ya guardados

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

### Error: "API key not found in .env file"

**Solución 1**: Crea el archivo `.env` y añade tu API key:
```bash
copy .env.example .env
# Edita .env y añade tu API key
```

**Solución 2**: El script te pedirá el API key automáticamente si no lo encuentra

### Error: "Your credit balance is too low"

**Solución**: Añade créditos a tu cuenta:
- **Claude**: https://console.anthropic.com/settings/billing
- **OpenAI**: https://platform.openai.com/account/billing

### Error: "anthropic library not found" o "openai library not found"

**Solución**: Instala las dependencias:
```bash
pip install -r requirements.txt
```

### El script es muy lento

Esto es normal. El script incluye un delay de 1 segundo entre peticiones para evitar rate limiting. Con 685 ejercicios, el proceso completo tomará aproximadamente 11-12 minutos.

### Rate limiting / Too many requests

El script ya incluye delays automáticos. Si aún así ocurre, puedes aumentar el delay editando la línea 453 en `enrich_exercises.py`:

```python
enricher.process_all_exercises(exercises, delay_seconds=2.0)  # Cambiar de 1.0 a 2.0
```

## Obtener API Keys

### Claude (Anthropic)
1. Visita https://console.anthropic.com/
2. Crea una cuenta o inicia sesión
3. Ve a Settings → API Keys
4. Crea una nueva API key
5. Cópiala y guárdala en `.env`

### OpenAI
1. Visita https://platform.openai.com/
2. Crea una cuenta o inicia sesión
3. Ve a API Keys
4. Crea una nueva API key
5. Cópiala y guárdala en `.env`

## Características Avanzadas

### Cambiar el Modelo de IA

Puedes cambiar los modelos editando `enrich_exercises.py`:

**Claude**:
```python
self.model = "claude-3-5-sonnet-20241022"  # Línea 54
```

**OpenAI**:
```python
self.model = "gpt-4o"  # Línea 83
# Alternativas: "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"
```

### Procesar Solo Algunos Ejercicios

Para probar con un subconjunto de ejercicios, modifica la línea 446 en `main()`:

```python
exercises = load_exercises(INPUT_FILE)[:10]  # Solo los primeros 10
```

## Licencia

Este script es parte del proyecto GAINZ.
