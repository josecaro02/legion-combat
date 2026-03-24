# Explicación del Sistema Legión Combat

## Índice

1. [Visión General de la Arquitectura](#visión-general-de-la-arquitectura)
2. [Sistema de Autenticación JWT](#sistema-de-autenticación-jwt)
3. [Sistema de Horarios Recurrentes](#sistema-de-horarios-recurrentes)
4. [Sistema de Pagos](#sistema-de-pagos)
5. [Decisiones de Diseño](#decisiones-de-diseño)
6. [Escalabilidad](#escalabilidad)
7. [Errores Comunes y Cómo Evitarlos](#errores-comunes-y-cómo-evitarlos)
8. [Buenas Prácticas Aplicadas](#buenas-prácticas-aplicadas)

---

## Visión General de la Arquitectura

Este sistema implementa una **Arquitectura en Capas** (Layered Architecture) con separación clara de responsabilidades:

```
┌─────────────────────────────────────┐
│           Controllers               │  ← Routes/Blueprints (Flask)
│    (Auth, Users, Students, etc.)      │     HTTP Request/Response
├─────────────────────────────────────┤
│           Middleware                  │  ← JWT, RBAC
│    (Auth, Authorization)            │
├─────────────────────────────────────┤
│           Schemas                     │  ← Pydantic Models
│    (Validación/Serialización)       │
├─────────────────────────────────────┤
│           Services                    │  ← Lógica de Negocio
│    (AuthService, StudentService)    │
├─────────────────────────────────────┤
│           Repositories                │  ← Acceso a Datos
│    (UserRepository, etc.)           │
├─────────────────────────────────────┤
│           Models                      │  ← SQLAlchemy 2.0
│    (User, Student, Payment, etc.)   │
└─────────────────────────────────────┘
```

### Flujo de una Petición

```
HTTP Request
     ↓
Flask Route (Controller)
     ↓
Middleware (JWT Validation)
     ↓
Schema Validation (Pydantic)
     ↓
Service (Business Logic)
     ↓
Repository (Data Access)
     ↓
Database (PostgreSQL)
```

---

## Sistema de Autenticación JWT

### ¿Por qué JWT con Refresh Tokens?

Los JSON Web Tokens (JWT) permiten autenticación **stateless** - el servidor no necesita mantener sesiones en memoria. Sin embargo, los tokens de larga duración representan un riesgo de seguridad.

**Nuestra solución: Token Rotation**
- **Access Token**: Vida corta (15 minutos), contiene claims del usuario
- **Refresh Token**: Vida larga (7 días), almacenado en BD con metadatos

### Flujo de Autenticación

```
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│ Cliente │                    │  API    │                    │   BD    │
└────┬────┘                    └────┬────┘                    └────┬────┘
     │                              │                              │
     │ POST /login                  │                              │
     │ {email, password}          │                              │
     │─────────────────────────────>│                              │
     │                              │                              │
     │                              │  1. Validar credenciales     │
     │                              │  2. Crear access_token       │
     │                              │  3. Crear refresh_token      │
     │                              │  4. Guardar hash en BD      │
     │                              │─────────────────────────────>│
     │                              │                              │
     │                              │<─────────────────────────────│
     │                              │                              │
     │  {access_token,             │                              │
     │   refresh_token}            │                              │
     │<─────────────────────────────│                              │
     │                              │                              │
     │                              │                              │
     │ POST /refresh                │                              │
     │ {refresh_token}             │                              │
     │─────────────────────────────>│                              │
     │                              │                              │
     │                              │  1. Validar firma/expiración │
     │                              │  2. Buscar hash en BD        │
     │                              │  3. Verificar no revocado    │
     │                              │  4. Detectar reuso           │
     │                              │  5. Crear NUEVOS tokens      │
     │                              │  6. Marcar anterior          │
     │                              │─────────────────────────────>│
     │                              │                              │
     │                              │<─────────────────────────────│
     │                              │                              │
     │  {new_access_token,          │                              │
     │   new_refresh_token}        │                              │
     │<─────────────────────────────│                              │
```

### Detección de Reuso de Tokens

Si un refresh token ya usado se intenta usar nuevamente, el sistema:
1. Detecta que el token tiene `replaced_by_token_id` asignado
2. Considera esto como posible robo de token
3. **Revoca TODOS los tokens del usuario**
4. Requiere login nuevamente

```python
# En auth_service.py
def refresh(self, refresh_token_str, ...):
    stored_token = self.user_repo.get_by_hash(hash_token(refresh_token_str))

    if stored_token.replaced_by_token_id:
        # ¡Posible compromiso! Revocar todo
        self.user_repo.revoke_all_user_tokens(user_id)
        raise AuthenticationError("Token reuse detected")
```

### Almacenamiento de Refresh Tokens

Los refresh tokens se almacenan hasheados (SHA-256) con metadatos:
- `token_hash`: Hash del token (único, indexado)
- `jti`: JWT ID para identificación rápida
- `expires_at`: Fecha de expiración
- `revoked_at`: Fecha de revocación (null = activo)
- `replaced_by_token_id`: Referencia al token que lo reemplazó
- `ip_address`, `user_agent`: Metadatos del cliente

---

## Sistema de Horarios Recurrentes

### Patrón: Template vs Instance

Este patrón separa la **definición** de una clase (template) de las **ocurrencias reales** (instances).

#### ScheduleTemplate (El Patrón)
```python
class ScheduleTemplate:
    day_of_week: DayOfWeek  # Lunes=0, Martes=1, etc.
    start_time: time        # 18:00
    end_time: time          # 19:00
    course_type: CourseType # BOXING, KICKBOXING, BOTH
    max_capacity: int        # 20
    valid_from: date        # Cuándo comienza a aplicar
    valid_to: date          # Cuándo termina (null = indefinido)
    version: int            # Para tracking de cambios
```

#### ClassInstance (La Ocurrencia Real)
```python
class ClassInstance:
    template_id: UUID       # Referencia al template (opcional)
    date: date              # Fecha específica
    start_time: time        # Copia del template (snapshot)
    end_time: time
    course_type: CourseType
    max_capacity: int
    status: ClassStatus     # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    professor_id: UUID
```

### ¿Por qué Separar?

1. **Historial**: Si cambias el horario del lunes, las clases pasadas mantienen su horario original
2. **Excepciones**: Puedes crear una clase especial sin template
3. **Cambios Graduales**: Al modificar un template, creas nueva versión sin afectar el pasado

### Generación Lazy (Bajo Demanda)

En lugar de generar todas las instancias por adelantado (que crearía millones de registros), las creamos **cuando se necesitan**:

```python
def get_or_create_instance(self, template_id, date):
    # 1. Buscar existente
    instance = repo.find_by_template_and_date(template_id, date)
    if instance:
        return instance

    # 2. Validar que la fecha es válida para el template
    template = repo.get_template(template_id)
    if not template.is_valid_for_date(date):
        raise ValueError("Date outside template validity")

    # 3. Crear nueva instancia desde el template
    instance = ClassInstance(
        template_id=template.id,
        date=date,
        start_time=template.start_time,
        end_time=template.end_time,
        ...
    )
    return repo.save(instance)
```

### Modificación de Horarios (Versionado)

Cuando un Owner modifica un horario:

```python
def update_template(self, template_id, **changes):
    old_template = self.get_template(template_id)

    # 1. Cerrar versión anterior
    old_template.valid_to = date.today()
    old_template.is_active = False
    self.repo.update(old_template)

    # 2. Crear nueva versión
    new_template = ScheduleTemplate(
        day_of_week=changes.get('day_of_week', old_template.day_of_week),
        start_time=changes.get('start_time', old_template.start_time),
        ...
        valid_from=date.today() + timedelta(days=1),  # Desde mañana
        version=old_template.version + 1
    )
    return self.repo.create(new_template)
```

**Resultado:**
- Clases pasadas: mantienen referencia al template viejo
- Clases futuras: se crearán desde el nuevo template
- Historial completo: preservado

---

## Sistema de Pagos

El sistema de pagos gestiona las mensualidades de los estudiantes, permitiendo registrar pagos pendientes, marcarlos como pagados, y generar reportes de vencimientos y deudores.

### Modelo de Datos

```python
class Payment:
    id: UUID                    # Identificador único del pago
    student_id: UUID            # Referencia al estudiante
    amount: Decimal             # Monto del pago (ej: 25000.00)
    status: PaymentStatus       # pending, paid, overdue
    due_date: date              # Fecha de vencimiento
    payment_date: date          # Fecha de pago (null si pending)
    idempotency_key: str        # Clave única para evitar duplicados
    notes: str                  # Notas opcionales
    created_at: datetime
    updated_at: datetime
```

### Estados de Pago

- **`pending`**: Pago registrado pero no realizado aún
- **`paid`**: Pago completado exitosamente
- **`overdue`**: Pago vencido (pasó la fecha de vencimiento sin pagar)

### Endpoints de Pagos

Todos los endpoints de pagos requieren autenticación JWT (`Bearer` token) y rol de Professor o Owner.

#### 1. Listar Pagos

```
GET /payments/
```

**Descripción:** Obtiene lista paginada de todos los pagos con filtros opcionales.

**Parámetros de Query:**
- `page` (int, opcional): Número de página, default: 1
- `per_page` (int, opcional): Items por página, default: 20
- `status` (string, opcional): Filtrar por estado (`pending`, `paid`, `overdue`)

**Respuesta 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "student_id": "uuid",
      "amount": "25000.00",
      "status": "pending",
      "due_date": "2024-03-20",
      "payment_date": null,
      "student_name": "Juan Pérez"
    }
  ],
  "total": 150,
  "pages": 8,
  "current_page": 1
}
```

**Uso típico:** Panel de administración para ver todos los pagos, filtrar por estado para ver solo pendientes o vencidos.

---

#### 2. Crear Pago

```
POST /payments/
```

**Descripción:** Registra un nuevo pago pendiente para un estudiante. Usa idempotencia para evitar duplicados.

**Body:**
```json
{
  "student_id": "123e4567-e89b-12d3-a456-426614174000",
  "amount": 25000.00,
  "due_date": "2024-03-20",
  "idempotency_key": "payment-juan-marzo-2024",
  "notes": "Mensualidad marzo 2024"
}
```

**Campos requeridos:**
- `student_id`: UUID del estudiante
- `amount`: Monto numérico positivo
- `due_date`: Fecha de vencimiento (YYYY-MM-DD)
- `idempotency_key`: String único (10-64 chars) para prevenir duplicados

**Respuesta 201:** El pago creado con sus datos.

**Respuesta 400:** Si ya existe un pago con la misma `idempotency_key`, retorna el pago existente (comportamiento idempotente).

**Uso típico:** Registrar la mensualidad de un estudiante. El idempotency_key puede ser generado por el frontend como: `"payment-{student_id}-{mes}-{año}"` para evitar crear el mismo pago dos veces si el usuario hace doble clic.

---

#### 3. Ver Pago por ID

```
GET /payments/{payment_id}
```

**Descripción:** Obtiene información detallada de un pago específico.

**Parámetros de Path:**
- `payment_id`: UUID del pago

**Respuesta 200:** Información completa del pago incluyendo `student_name` (nombre del estudiante).

**Uso típico:** Ver detalles de un pago específico al hacer clic en él desde la lista.

---

#### 4. Actualizar Pago

```
PUT /payments/{payment_id}
```

**Descripción:** Actualiza datos de un pago existente.

**Parámetros de Path:**
- `payment_id`: UUID del pago

**Body (todos opcionales):**
```json
{
  "amount": 30000.00,
  "due_date": "2024-03-25",
  "notes": "Monto actualizado"
}
```

**Campos actualizables:**
- `amount`: Nuevo monto
- `due_date`: Nueva fecha de vencimiento
- `notes`: Nuevas notas

**Restricciones:** No se puede actualizar un pago que ya está `paid` (pagado).

**Uso típico:** Corregir errores en un pago pendiente antes de que se concrete.

---

#### 5. Eliminar Pago

```
DELETE /payments/{payment_id}
```

**Descripción:** Elimina un pago del sistema.

**Parámetros de Path:**
- `payment_id`: UUID del pago

**Restricciones:** Generalmente solo se permite eliminar pagos `pending`, no pagos ya realizados (por integridad contable).

**Uso típico:** Eliminar un pago registrado por error.

---

#### 6. Ver Pagos de un Estudiante

```
GET /payments/student/{student_id}
```

**Descripción:** Obtiene todos los pagos de un estudiante específico.

**Parámetros de Path:**
- `student_id`: UUID del estudiante

**Parámetros de Query:**
- `page`, `per_page`: Paginación
- `status` (opcional): Filtrar por estado

**Respuesta 200:** Lista paginada de pagos del estudiante.

**Uso típico:** Ver historial de pagos de un estudiante específico, ver si tiene pagos pendientes.

---

#### 7. Marcar Pago como Pagado

```
POST /payments/{payment_id}/mark-paid
```

**Descripción:** Marca un pago pendiente como pagado.

**Parámetros de Path:**
- `payment_id`: UUID del pago

**Body (opcional):**
```json
{
  "payment_date": "2024-03-15"
}
```

- `payment_date`: Fecha del pago (default: fecha actual)

**Respuesta 200:** El pago actualizado con status `paid` y `payment_date` establecida.

**Respuesta 400:** Si el pago ya está pagado o está vencido (requiere verificación especial).

**Uso típico:** Cuando un estudiante paga su mensualidad, el profesor marca el pago como realizado.

---

#### 8. Próximos Vencimientos

```
GET /payments/upcoming
```

**Descripción:** Obtiene pagos que vencen en los próximos N días.

**Parámetros de Query:**
- `days` (int, opcional): Días hacia adelante a consultar, default: 5

**Respuesta 200:** Lista de pagos con vencimiento próximo.

**Uso típico:** Alertar a los profesores sobre pagos que vencen pronto para que puedan recordar a los estudiantes.

---

#### 9. Pagos Vencidos

```
GET /payments/overdue
```

**Descripción:** Obtiene todos los pagos que ya vencieron (pasó la fecha de vencimiento y no están pagados).

**Respuesta 200:** Lista de pagos vencidos con información del estudiante.

**Uso típico:** Generar lista de estudiantes morosos para enviar recordatorios o hacer seguimiento.

---

#### 10. Resumen de Deudores

```
GET /payments/overdue/summary
```

**Descripción:** Genera un resumen agregado de deudores, mostrando cuántos pagos debe cada estudiante y el monto total.

**Respuesta 200:**
```json
[
  {
    "student_id": "uuid",
    "student_name": "Juan Pérez",
    "overdue_count": 2,
    "total_amount": "50000.00"
  },
  {
    "student_id": "uuid",
    "student_name": "María García",
    "overdue_count": 1,
    "total_amount": "25000.00"
  }
]
```

**Uso típico:** Reporte de morosidad para la administración, mostrando quiénes deben más y cuánto.

### Flujo Típico de Trabajo

1. **Registro inicial:** Se crean pagos mensuales para cada estudiante al inicio del mes usando `POST /payments/`
2. **Consulta diaria:** Se revisan pagos próximos a vencer con `GET /payments/upcoming`
3. **Cobro:** Cuando un estudiante paga, se marca como pagado con `POST /payments/{id}/mark-paid`
4. **Seguimiento:** Se revisan pagos vencidos con `GET /payments/overdue`
5. **Reportes:** Se genera resumen de deudores con `GET /payments/overdue/summary`

### Idempotencia

El sistema implementa idempotencia mediante la clave `idempotency_key`. Esto significa que si haces la misma petición dos veces con la misma clave, solo se creará un pago (la segunda vez retorna el existente). Esto previene duplicados por errores de red o doble clic.

**Cómo generar la clave:**
```python
idempotency_key = f"payment-{student_id}-{mes}-{año}"
# Ejemplo: "payment-123e4567-...-03-2024"
```

---

## Decisiones de Diseño

### 1. SQLAlchemy 2.0 con DeclarativeBase

**Por qué:**
- Typing nativo con `Mapped[T]`
- Mejor autocompletado IDE
- Detección de errores en tiempo de desarrollo

```python
# SQLAlchemy 2.0 Style
class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True)
```

### 2. Repository Pattern

**Por qué:**
- Abstracción de persistencia
- Facilita testing (mocks)
- Cambio de DB sin tocar services

```python
# Service depende de abstracción, no implementación
class StudentService:
    def __init__(self, repo: StudentRepository = None):
        self.repo = repo or StudentRepository()
```

### 3. Pydantic para Validación

**Por qué:**
- Validación automática de tipos
- Serialización/deserialización
- Documentación OpenAPI automática

### 4. Enum como String en BD

```python
class UserRole(str, Enum):
    OWNER = "owner"
    PROFESSOR = "professor"
```

**Ventajas:**
- Legible en BD (vs enteros mágicos)
- Fácil debugging
- Portable entre DBs

---

## Documentación de API con Flasgger

### ¿Qué es Flasgger?

[Flasgger](https://github.com/flasgger/flasgger) es una biblioteca Flask que genera automáticamente una interfaz **Swagger UI** a partir de docstrings YAML en los endpoints. Esto permite:

1. **Explorar la API** de forma interactiva
2. **Probar endpoints** directamente desde el navegador
3. **Ver modelos de datos** esperados en requests/responses
4. **Autenticación integrada** para probar endpoints protegidos

### Configuración

La configuración de Swagger se define en `app/config.py`:

```python
@classmethod
def get_swagger_template(cls) -> dict:
    return {
        'swagger': '2.0',
        'info': {
            'title': 'Legión Combat API',
            'description': 'Sistema de gestión para gimnasio de boxeo',
            'version': '1.0.0',
        },
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'JWT Authorization header. Ejemplo: "Bearer {token}"'
            }
        },
        'tags': [
            {'name': 'Auth', 'description': 'Autenticación'},
            {'name': 'Students', 'description': 'Gestión de estudiantes'},
            ...
        ]
    }
```

En `app/__init__.py` se inicializa:

```python
from flasgger import Swagger

Swagger(app, template=config.get_swagger_template())
```

### Cómo Documentar un Endpoint

Los docstrings deben seguir el formato **YAML** con separador `---`:

```python
@student_bp.route('/', methods=['GET'])
@jwt_required
@require_professor
def list_students():
    """List students with optional filters.
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: course
        in: query
        type: string
        enum: [boxing, kickboxing, both]
    responses:
      200:
        description: List of students
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                    format: uuid
                  first_name:
                    type: string
      401:
        description: Unauthorized
    """
```

### Elementos Importantes del YAML

#### Tags
Organizan los endpoints por categoría en la UI:
```yaml
tags:
  - Students
```

#### Seguridad (JWT)
Indica que el endpoint requiere autenticación:
```yaml
security:
  - Bearer: []
```

#### Parámetros
Definen inputs del endpoint:

```yaml
parameters:
  # Parámetro de query string
  - name: page
    in: query
    type: integer
    default: 1

  # Parámetro de URL
  - name: student_id
    in: path
    type: string
    format: uuid
    required: true

  # Body de la request (JSON)
  - name: body
    in: body
    required: true
    schema:
      type: object
      required:
        - email
        - password
      properties:
        email:
          type: string
          format: email
          example: "owner@gym.com"
```

#### Respuestas
Documentan los posibles códigos de respuesta:

```yaml
responses:
  200:
    description: Success
    schema:
      type: object
      properties:
        access_token:
          type: string
        expires_in:
          type: integer
  401:
    description: Authentication failed
    schema:
      type: object
      properties:
        error:
          type: string
          example: "AUTHENTICATION_ERROR"
```

### Acceso a Swagger UI

Una vez iniciada la aplicación, la documentación está disponible en:

- **Swagger UI**: `http://localhost:5000/apidocs/`
- **OpenAPI JSON**: `http://localhost:5000/apispec_1.json`

### Ventajas de esta Aproximación

1. **Single Source of Truth**: La documentación vive junto al código
2. **Siempre actualizada**: Si cambia el endpoint, se actualiza la doc
3. **Testing interactivo**: No necesitas Postman para probar
4. **Auto-generada**: No hay que mantener archivos OpenAPI/YAML separados

---

## Escalabilidad

### Optimizaciones Actuales

1. **Índices de Base de Datos**
   ```python
   __table_args__ = (
       Index('ix_payments_student_due_date', 'student_id', 'due_date'),
   )
   ```

2. **Paginación en Todas las Listas**
   ```python
   def list_students(self, page=1, per_page=20):
       skip = (page - 1) * per_page
       return self.repo.get_all(skip, per_page)
   ```

3. **Generación Lazy de Clases**
   - Solo creamos instancias cuando se consultan
   - Evita millones de registros sin uso

### Escalabilidad Horizontal

Para escalar a múltiples servidores:

1. **Base de Datos**
   - Usar PostgreSQL con read replicas
   - Considerar sharding por tenant (si multi-tenant)

2. **Cache**
   ```python
   # Agregar Redis para:
   # - Tokens de blacklist (revocados)
   # - Resultados de queries frecuentes
   # - Templates de horarios (pocos cambios)
   ```

3. **Async Workers**
   ```python
   # Para operaciones pesadas:
   # - Generación masiva de reportes
   # - Notificaciones por email/SMS
   # - Procesamiento de pagos
   ```

---

## Errores Comunes y Cómo Evitarlos

### 1. N+1 Query Problem

**Problema:**
```python
# Esto genera N+1 queries
students = Student.query.all()
for student in students:
    print(student.payments.count())  # Query adicional por estudiante
```

**Solución:**
```python
# Usar eager loading
from sqlalchemy.orm import joinedload

students = db.session.query(Student).options(
    joinedload(Student.payments)
).all()
```

### 2. Token Expirado en Medio de Request

**Problema:** El access token expira mientras el usuario está usando la app.

**Solución:** Cliente debe:
1. Detectar 401 por token expirado
2. Llamar a `/auth/refresh` con refresh_token
3. Reintentar request original con nuevo token

### 3. Race Condition en Pagos

**Problema:** Doble clic en "Crear Pago" crea duplicados.

**Solución:** Idempotency Key
```python
# Cliente genera key única por intento
idempotency_key = f"payment-{student_id}-{mes}-{año}"

# Servicio verifica antes de crear
existing = repo.get_by_idempotency_key(idempotency_key)
if existing:
    return existing  # Retorna existente
```

### 4. Modificar Template Afecta Clases Pasadas

**Problema:** Cambiar horario del lunes modifica clases pasadas.

**Solución:** Nuestro sistema de versionado crea nuevo template para el futuro, preservando el pasado.

---

## Documentación de API con Swagger (Flasgger)

### ¿Qué es Flasgger?

**Flasgger** es una biblioteca Flask que genera automáticamente documentación Swagger/OpenAPI a partir de los docstrings YAML en los endpoints.

### Configuración

La configuración de Swagger se define en `app/config.py`:

```python
@classmethod
def get_swagger_template(cls) -> dict:
    return {
        'swagger': '2.0',
        'info': {
            'title': 'Legión Combat API',
            'description': 'Sistema de gestión para gimnasio de boxeo',
            'version': '1.0.0',
        },
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'JWT Authorization header. Example: "Bearer {token}"'
            }
        },
        'tags': [...]
    }
```

En `app/__init__.py` se inicializa:

```python
from flasgger import Swagger

Swagger(app, template=config.get_swagger_template())
```

### Documentación de Endpoints

Cada endpoint se documenta con un docstring en formato YAML:

```python
@student_bp.route('/', methods=['POST'])
def create_student():
    """Create a new student.
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - first_name
            - last_name
            - course
          properties:
            first_name:
              type: string
              example: "Juan"
            course:
              type: string
              enum: [boxing, kickboxing, both]
    responses:
      201:
        description: Student created successfully
      400:
        description: Validation error
    """
    # ... código del endpoint
```

### Elementos Clave de la Documentación

| Elemento | Descripción |
|----------|-------------|
| `tags` | Agrupa endpoints por categoría |
| `security` | Indica que requiere JWT Bearer token |
| `parameters` | Define query params, path params y body |
| `responses` | Documenta códigos de respuesta y schemas |
| `schema` | Define la estructura de datos esperada |

### Uso de Swagger UI

1. Iniciar la aplicación: `python run.py`
2. Abrir navegador en: `http://localhost:5000/apidocs/`
3. Explorar y probar endpoints directamente desde la UI

### Ventajas

- **Documentación viva**: Se actualiza automáticamente con el código
- **Testing interactivo**: Prueba endpoints desde el navegador
- **Standard**: Usa OpenAPI/Swagger, estándar de la industria
- **Cliente API**: Exporta a Postman, genera clientes SDK

---

## Buenas Prácticas Aplicadas

### 1. Principio de Responsabilidad Única (SRP)

Cada clase tiene una sola razón para cambiar:
- `UserService`: Gestión de usuarios
- `AuthService`: Autenticación
- `StudentRepository`: Acceso a datos de estudiantes

### 2. Inyección de Dependencias

```python
class AuthService:
    def __init__(self, user_repo: UserRepository = None):
        self.user_repo = user_repo or UserRepository()

# En tests:
mock_repo = MockUserRepository()
service = AuthService(mock_repo)
```

### 3. Manejo de Errores Consistente

```python
class AppError(Exception):
    def __init__(self, message, status_code, code):
        ...

class NotFoundError(AppError):
    def __init__(self, resource):
        super().__init__(f"{resource} not found", 404, "NOT_FOUND")

# Todos los errores siguen el mismo formato JSON:
{"error": "NOT_FOUND", "message": "Student not found"}
```

### 4. Validación en Múltiples Capas

- **Schema (Pydantic)**: Tipos y formatos
- **Service**: Reglas de negocio
- **Database**: Constraints y foreign keys

### 5. Testing Piramidal

```
    /\
   /  \  ← Tests de Integración (API endpoints)
  /----\
 /      \ ← Tests de Servicio (lógica de negocio)
/________\
          ← Tests Unitarios (utils, models)
```

---

## Conclusión

Este sistema está diseñado para:

1. **Seguridad**: JWT con rotación, hash de contraseñas bcrypt, validación de inputs
2. **Mantenibilidad**: Arquitectura limpia, tipado, documentación
3. **Escalabilidad**: Optimizaciones de BD, patrones que permiten crecimiento
4. **Usabilidad**: API REST consistente, mensajes de error claros

Las decisiones de diseño priorizan la simplicidad operativa (generación lazy vs batch) mientras mantienen flexibilidad para casos edge (clases especiales sin template).
