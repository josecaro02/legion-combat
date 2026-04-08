# Legión Combat API

Sistema de gestión para gimnasio de boxeo con API REST completa.

## Características

- **Autenticación JWT Avanzada**: Access tokens (15 min) + Refresh tokens (7 días) con rotación y detección de reuso
- **Autorización RBAC**: Roles de Owner y Professor con permisos diferenciados
- **Gestión de Estudiantes**: Registro, búsqueda, activación/desactivación
- **Sistema de Pagos**: Con idempotencia, vencimientos y reportes
- **Horarios Recurrentes**: Templates vs Instancias con generación lazy
- **Control de Asistencia**: Registro multi-estudiante y reportes

## Stack Tecnológico

- Python 3.11+
- Flask + Flask-SQLAlchemy
- SQLAlchemy 2.0 (modo DeclarativeBase)
- PostgreSQL
- Pydantic (validación/serialización)
- PyJWT + bcrypt
- pytest (testing)
- Flasgger (documentación Swagger UI)

## Documentación de API (Swagger UI)

La API incluye documentación interactiva generada automáticamente con **Flasgger**.

### Acceder a la documentación

Una vez iniciada la aplicación:

- **Swagger UI**: `http://localhost:5000/apidocs/`
- **OpenAPI JSON**: `http://localhost:5000/apispec_1.json`

### Usar Swagger UI

1. **Explorar endpoints**: Navega por las categorías (Auth, Students, Payments, etc.)
2. **Ver modelos**: Cada endpoint muestra los parámetros esperados y respuestas
3. **Probar endpoints**:
   - Haz clic en un endpoint para expandirlo
   - Click en "Try it out"
   - Completa los parámetros
   - Para endpoints protegidos, haz clic en "Authorize" e ingresa: `Bearer <tu_token>`
   - Click en "Execute"

### Autenticación en Swagger UI

Los endpoints protegidos requieren un JWT token:

1. Primero ejecuta el endpoint `/auth/login` con tus credenciales
2. Copia el `access_token` de la respuesta
3. Haz clic en el botón **"Authorize"** (candado arriba a la derecha)
4. Ingresa: `Bearer eyJhbG...` (tu token completo)
5. Haz clic en "Authorize" y cierra el modal
6. Ahora todos los requests incluirán automáticamente el header de autorización

## Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd legion-combat

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements/dev.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Crear base de datos PostgreSQL (ver sección abajo)
createdb legion_combat_dev

# Iniciar aplicación
python run.py
```

### Instalar PostgreSQL en Ubuntu/Debian

Si obtienes el error `createdb: command not found` o similar:

```bash
# 1. Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# 2. Iniciar el servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. Crear usuario y base de datos
# Reemplaza 'tu_usuario' con tu usuario de Linux ($USER)
sudo -u postgres psql -c "CREATE USER tu_usuario WITH CREATEDB;"
sudo -u postgres psql -c "ALTER USER tu_usuario WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "ALTER USER tu_usuario WITH SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE legion_combat_dev;"

# 4. Verificar instalación
psql --version
sudo systemctl status postgresql
```

**Nota**: Asegúrate que el usuario de PostgreSQL coincida con tu usuario de Linux para usar `createdb` sin `-U`.

Si prefieres usar el usuario `postgres`:
```bash
sudo -u postgres createdb legion_combat_dev
```

Y actualiza tu `.env`:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legion_combat_dev
```

## Migraciones de Base de Datos (Alembic)

Este proyecto usa **Alembic** para gestionar migraciones de base de datos con SQLAlchemy.

### Configuración inicial (ya realizada)

La configuración de Alembic ya está completa:
- Archivo `alembic.ini` configurado
- `migrations/env.py` importa los modelos automáticamente
- Las migraciones se guardan en `migrations/versions/`

### Comandos básicos

```bash
# Ver estado actual de migraciones
alembic current

# Crear nueva migración (después de modificar modelos)
alembic revision --autogenerate -m "descripcion del cambio"

# Aplicar migraciones pendientes
alembic upgrade head

# Revertir última migración (cuidado: perderás datos de las tablas afectadas)
alembic downgrade -1

# Revertir a versión específica
alembic downgrade <revision_id>

# Ver historial de migraciones
alembic history
```

### Flujo de trabajo para cambios en modelos

1. **Modificar modelos** en `app/models/`

2. **Crear migración**:
   ```bash
   alembic revision --autogenerate -m "agregar columna telefono a estudiantes"
   ```

3. **Revisar el script generado** en `migrations/versions/`
   - Verificar que los cambios sean correctos
   - Revisar especialmente operaciones que puedan causar pérdida de datos

4. **Aplicar migración**:
   ```bash
   alembic upgrade head
   ```

### Flujo de trabajo para nuevo desarrollador

Si clonas el proyecto por primera vez:

```bash
# 1. Crear base de datos
createdb legion_combat_dev

# 2. Aplicar todas las migraciones
alembic upgrade head

# 3. La aplicación ya está lista para usar
python run.py
```

### Buenas prácticas

- **Siempre revisa** los scripts de migración autogenerados antes de aplicarlos
- **Nunca** uses `db.drop_all()` en producción
- **Nunca** modifiques migraciones ya aplicadas en producción
- Mantén las migraciones **pequeñas y enfocadas** (una lógica de cambio por migración)
- En desarrollo, si necesitas limpiar todo:
  ```bash
  # Peligro: solo en desarrollo con datos de prueba
  alembic downgrade base  # Revertir todo
  alembic upgrade head  # Aplicar de nuevo
  ```

### Troubleshooting

**Error: `type "xxx" already exists`**
- Los tipos ENUM de PostgreSQL no se eliminaron correctamente
- Solución: eliminar manualmente los tipos ENUM del schema público

**Error: `relation "xxx" already exists`**
- Intentaste crear tablas que ya existen
- Solución: `alembic stamp head` para marcar la BD como actualizada

**Alembic no detecta cambios**
- Asegúrate de importar el modelo en `app/models/__init__.py`
- Verifica que el modelo herede de `Base` (de `app.extensions`)

### Crear usuario Owner inicial

```python
from app import create_app
from app.extensions import db
from app.models.user import User, UserRole
from app.utils.password_utils import hash_password

app = create_app()
with app.app_context():
    owner = User(
        email='owner@gym.com',
        password_hash=hash_password('securepassword'),
        first_name='Owner',
        last_name='Gym',
        role=UserRole.OWNER
    )
    db.session.add(owner)
    db.session.commit()
```

### Autenticación

Puedes probar la API usando **Swagger UI** (recomendado) o curl:

#### Opción 1: Swagger UI (Interactivo)

1. Abre `http://localhost:5000/apidocs/`
2. Expande el endpoint `POST /auth/login`
3. Click "Try it out"
4. Ingresa credenciales en el body:
   ```json
   {
     "email": "owner@gym.com",
     "password": "securepassword"
   }
   ```
5. Click "Execute"
6. Copia el `access_token` de la respuesta
7. Click en "Authorize" e ingresa: `Bearer eyJhbG...` (tu token)

#### Opción 2: Curl

```bash
# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "owner@gym.com", "password": "securepassword"}'

# Response: {"access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 900}

# Usar token
curl -X GET http://localhost:5000/students/ \
  -H "Authorization: Bearer <access_token>"
```

## Endpoints Principales

### Auth
- `POST /auth/login` - Login
- `POST /auth/refresh` - Refrescar tokens
- `POST /auth/logout` - Logout
- `POST /auth/logout-all` - Logout global
- `GET /auth/me` - Info usuario actual
- `PUT /auth/me/password` - Cambiar contraseña

### Users (Owner only)
- `POST /users/professors` - Crear profesor
- `GET /users/professors` - Listar profesores
- `PUT /users/professors/{id}` - Actualizar profesor
- `DELETE /users/professors/{id}` - Eliminar profesor

### Students
- `GET /students/` - Listar estudiantes
- `POST /students/` - Crear estudiante
- `GET /students/{id}` - Ver estudiante
- `PUT /students/{id}` - Actualizar estudiante
- `DELETE /students/{id}` - Eliminar estudiante
- `POST /students/{id}/deactivate` - Desactivar
- `POST /students/{id}/activate` - Activar

### Payments
- `GET /payments/` - Listar pagos
- `POST /payments/` - Crear pago
- `POST /payments/quick-pay` - Crear y marcar como pagado (Quick Pay)
- `POST /payments/{id}/mark-paid` - Marcar como pagado
- `GET /payments/upcoming` - Próximos vencimientos
- `GET /payments/overdue` - Pagos vencidos
- `GET /payments/overdue/summary` - Resumen deudores

### Schedules (Owner only)
- `GET /schedules/templates` - Listar templates
- `POST /schedules/templates` - Crear template
- `PUT /schedules/templates/{id}` - Actualizar template
- `DELETE /schedules/templates/{id}` - Eliminar template

### Classes
- `GET /classes/` - Listar clases
- `GET /classes/range` - Clases por rango de fechas
- `POST /classes/` - Crear clase
- `PUT /classes/{id}` - Actualizar clase
- `POST /classes/{id}/cancel` - Cancelar clase

### Attendance
- `POST /attendance/` - Registrar asistencia
- `GET /attendance/daily/{date}` - Resumen diario
- `GET /attendance/student/{id}` - Historial estudiante

## Testing

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Solo tests unitarios
pytest tests/unit/

# Solo tests de integración
pytest tests/integration/
```

## Estructura del Proyecto

```
app/
├── __init__.py          # Flask factory
├── config.py            # Configuraciones
├── extensions.py        # Extensiones Flask
├── models/              # Modelos SQLAlchemy
├── schemas/             # Schemas Pydantic
├── services/            # Lógica de negocio
├── repositories/        # Acceso a datos
├── controllers/         # Routes/Blueprints
├── middleware/          # JWT y RBAC
├── utils/               # Utilidades
└── exceptions/          # Excepciones custom

tests/
├── conftest.py          # Fixtures pytest
├── unit/                # Tests unitarios
└── integration/         # Tests de integración
```

## Sistema de Permisos (Frontend)

Se implementó un sistema de permisos centralizado y reutilizable para controlar el acceso a funcionalidades según el rol del usuario.

### Archivo: `src/utils/permissions.js`

```javascript
export const permissions = {
  canViewStudents: ['owner', 'professor'],
  canCreateStudent: ['owner', 'professor'],
  canEditStudent: ['owner', 'professor'],
  canDeleteStudent: ['owner'],
  canViewPayments: ['owner', 'professor'],
  canCreatePayment: ['owner', 'professor'],
  canViewReports: ['owner'],
};

export const hasPermission = (user, permission) => {
  return permissions[permission]?.includes(user?.role);
};
```

### Uso de hasPermission

```jsx
import { useAuth } from '../auth/AuthContext';
import { hasPermission } from '../utils/permissions';

function MyComponent() {
  const { user } = useAuth();

  const canView = hasPermission(user, 'canViewStudents');
  const canCreate = hasPermission(user, 'canCreateStudent');

  return (
    <div>
      {canView && <StudentsList />}
      {canCreate && <CreateStudentButton />}
    </div>
  );
}
```

### Ventajas del sistema

- **Centralizado**: Todos los permisos en un solo lugar
- **Reutilizable**: Función `hasPermission` usada en toda la aplicación
- **Mantenible**: Cambiar permisos solo requiere editar un archivo
- **Testable**: Fácil de probar con diferentes roles

## API Frontend - Estudiantes

Archivo: `src/api/students.api.js`

### Funciones disponibles

```javascript
import { getStudents, createStudent, searchStudents } from '../api/students.api';

// Listar estudiantes (con paginación y filtros)
const result = await getStudents(token, { page: 1, per_page: 20 });
// Retorna: { items: [...], total: 50, pages: 3, current_page: 1 }

// Crear estudiante
const newStudent = await createStudent(token, {
  first_name: 'Juan',
  last_name: 'Pérez',
  course: 'boxing', // 'boxing', 'kickboxing', 'both'
  phone: '+56912345678',
  address: 'Av. Principal 123'
});

// Buscar estudiantes
const found = await searchStudents(token, 'juan');
```

### Endpoints del backend

- `GET /students/` - Listar estudiantes
- `POST /students/` - Crear estudiante
- `GET /students/search?q={query}` - Buscar por nombre
- `GET /students/{id}` - Obtener estudiante específico
- `POST /students/{id}/deactivate` - Desactivar estudiante
- `POST /students/{id}/activate` - Activar estudiante

## Página de Estudiantes

Archivo: `src/pages/Students.jsx`

### Funcionalidades

- **Listado**: Tabla con todos los estudiantes (nombre, apellido, curso, estado)
- **Permisos**: Solo usuarios con `canViewStudents` pueden ver la página
- **Creación**: Formulario condicional visible solo para `canCreateStudent`
- **Estados**: Maneja loading, error y mensajes de éxito

### Componente

```jsx
function Students() {
  const { user, token } = useAuth();
  const canView = hasPermission(user, 'canViewStudents');
  const canCreate = hasPermission(user, 'canCreateStudent');

  // Carga estudiantes del backend real
  useEffect(() => {
    if (canView && token) {
      loadStudents();
    }
  }, [canView, token]);

  // Render condicional según permisos
  if (!canView) return <div>No tienes permiso</div>;

  return (
    // Lista de estudiantes + formulario condicional
  );
}
```


## Flujo de Pagos (Quick Pay)



Se implementó un endpoint simplificado para registrar pagos en una sola operación.



### Endpoint: `POST /payments/quick-pay`



**Propósito**: Crear el pago y marcarlo como pagado automáticamente.



**Request**:

```json

{

  "student_id": "uuid",

  "amount": 25000,

  "notes": "Pago mensualidad marzo"

}

```



**Lógica del backend**:

1. Obtiene la fecha actual del servidor (`date.today()`)

2. Crea el pago con `status = pending` inicialmente

3. Inmediatamente lo marca como pagado con `payment_date = today`

4. Retorna el pago completo con `status = paid`




### Frontend: Payments.jsx



Archivo: `src/pages/Payments.jsx`



**Características**:

- Formulario simplificado: solo `student_id`, `amount`, `notes`

- **No envía fechas**: el backend controla las fechas

- Usa `quickPay()` para crear y pagar en una llamada

- Lista muestra `status` y `payment_date`



### Decisiones Tomadas



1. **Backend como fuente de verdad**: Las fechas se generan en el servidor, no en el cliente

2. **Un solo endpoint**: Simplifica la lógica de frontend (antes eran 2 llamadas)

3. **Seguridad**: Previene manipulación de fechas desde el frontend

4. **Consistencia**: Todas las fechas usan la hora del servidor

## Flujo de Pagos (Quick Pay)

Se implementó un flujo simplificado para registrar pagos que combina la creación y el marcado como pagado en un solo paso.

### Endpoint

```
POST /payments/quick-pay
```

### Request

```json
{
  "student_id": "uuid",
  "amount": 25000,
  "notes": "Pago mensualidad marzo"
}
```

**Campos requeridos:**
- `student_id`: UUID del estudiante
- `amount`: Monto del pago (número positivo)

**Campos opcionales:**
- `notes`: Notas adicionales sobre el pago

### Lógica del Backend

1. **Validación**: Verifica que `student_id` y `amount` estén presentes
2. **Creación**: Crea el pago con:
   - `due_date`: fecha actual (hoy)
   - `status`: pending (inicialmente)
   - `idempotency_key`: generado automáticamente
3. **Marcado**: Inmediatamente marca el pago como pagado:
   - `status`: paid
   - `payment_date`: fecha actual (hoy)
4. **Retorno**: Devuelve el pago completo con status "paid"

### Decisiones Técnicas

**¿Por qué Quick Pay?**

1. **Backend controla fechas**: El frontend NO envía fechas. El backend es la única fuente de verdad para las fechas de pago.

2. **Simplificación**: Un solo endpoint reduce la complejidad en el frontend. Antes se necesitaba:
   - Llamar a `POST /payments/` para crear
   - Llamar a `POST /payments/{id}/mark-paid` para marcar como pagado

3. **Seguridad**: Evita inconsistencias donde el frontend podría enviar fechas incorrectas o futuras.

4. **Consistencia**: Todos los pagos registrados mediante Quick Pay tienen fechas confiables generadas por el servidor.

### Uso en Frontend

```javascript
import { quickPay } from '../api/payments.api';

// Registrar pago - el backend asigna todas las fechas
const payment = await quickPay(token, {
  student_id: 'uuid-del-estudiante',
  amount: 25000,
  notes: 'Pago mensualidad'
});

// payment.status === 'paid'
// payment.payment_date === fecha de hoy
```

### UI: Payments.jsx

La página de pagos usa el flujo simplificado:

- **Formulario**: Solo campos `student_id`, `amount`, `notes`
- **Sin fechas**: El usuario no selecciona fechas
- **Confirmación**: Al guardar, el pago aparece inmediatamente como "Pagado"
- **Refresh**: La lista se actualiza automáticamente después del registro

### Comparación: Flujo Tradicional vs Quick Pay

**Tradicional (2 pasos):**
```javascript
const payment = await createPayment(token, { student_id, amount, due_date });
await markPaymentAsPaid(token, payment.id);
```

**Quick Pay (1 paso):**
```javascript
const payment = await quickPay(token, { student_id, amount });
```

## Frontend

El frontend está en la carpeta `frontend/` y está construido con React + Vite + Tailwind CSS.

### Requisitos Frontend

- Node.js >= 18
- Backend corriendo en http://localhost:5000

### Instalación y Ejecución

```bash
cd frontend
npm install
npm run dev
```

El frontend estará disponible en http://localhost:5173

### Funcionalidades Frontend

- **Login**: Autenticación real con el backend
- **Rutas Protegidas**: `/dashboard` requiere autenticación
- **Persistencia**: Token guardado en localStorage
- **Roles**: Soporta `owner` y `professor`

### Dashboard Dinámico

El Dashboard muestra contenido diferente según los permisos del usuario autenticado:

**Común para owner y professor:**
- Sección **Estudiantes**: Ver lista de estudiantes
- Sección **Pagos**: Ver pagos pendientes y vencidos
- Sección **Registrar Pago**: Crear nuevos pagos

**Solo owner:**
- Botón **Generar Reporte**

**Implementación (con sistema de permisos):**
```jsx
import { hasPermission } from '../utils/permissions';

const { user } = useAuth();
const canViewPayments = hasPermission(user, 'canViewPayments');
const canCreatePayment = hasPermission(user, 'canCreatePayment');
const canViewReports = hasPermission(user, 'canViewReports');

// Render condicional basado en permisos
{canViewPayments && <PaymentsSection />}
{canCreatePayment && <RegisterPaymentButton />}
{canViewReports && <GenerateReportButton />}
```

### Estructura Frontend

```
frontend/
├── src/
│   ├── api/           # Funciones de API (auth.js, client.js)
│   ├── auth/          # AuthContext.jsx
│   ├── components/    # Layout, Navbar, ProtectedRoute
│   ├── hooks/         # Custom hooks
│   ├── pages/         # Login, Dashboard
│   ├── router/        # AppRouter.jsx
│   └── main.jsx       # Entry point
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Dashboard Conectado a Backend

El Dashboard ahora consume datos reales del backend en tiempo real.

### Endpoints Utilizados

- `GET /students/` - Obtiene el listado completo de estudiantes
- `GET /payments/` - Obtiene el listado completo de pagos

### Datos Mostrados

| Métrica | Descripción | Origen |
|---------|-------------|--------|
| Total Estudiantes | Cantidad de estudiantes registrados | Backend - `GET /students/` |
| Total Pagos | Cantidad de pagos registrados | Backend - `GET /payments/` |
| Último Pago | Fecha del pago más reciente | Cálculo frontend sobre datos de `/payments/` |

### Implementación

```jsx
// Dashboard.jsx - Lógica de conexión
useEffect(() => {
  async function fetchDashboardData() {
    if (!token) return;

    setLoading(true);
    try {
      const [studentsData, paymentsData] = await Promise.all([
        canViewStudents ? authGet('/students/', token) : Promise.resolve([]),
        canViewPayments ? authGet('/payments/', token) : Promise.resolve([])
      ]);

      setStudents(studentsData.items || studentsData || []);
      setPayments(paymentsData.items || paymentsData || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  fetchDashboardData();
}, [token, canViewStudents, canViewPayments]);
```

### Estados de UI

- **Cargando**: Muestra "Cargando..." mientras se obtienen los datos
- **Error**: Muestra mensaje de error si falla alguna petición
- **Datos vacíos**: Muestra "--" cuando no hay datos disponibles

### Limitación Actual (Quick Pay)

Debido al uso del flujo **Quick Pay**:

- Todos los pagos registrados tienen `status = "paid"`
- No existen pagos "pending" ni "overdue" reales
- La UI ha sido adaptada para mostrar:
  - **Total Pagos** en lugar de "Pagos Pendientes"
  - **Último Pago** (fecha más reciente) en lugar de "Pagos Vencidos"

Esto refleja la naturaleza del sistema donde los pagos se registran al momento de ser recibidos.

### Cómo Probar

1. Iniciar sesión en la aplicación
2. Navegar al Dashboard
3. Verificar que se muestran:
   - Total de estudiantes (número real)
   - Total de pagos (número real)
   - Fecha del último pago registrado

### Flujo de Datos

```
Usuario → Dashboard.jsx → authGet() → Backend API
                              ↓
                        HTTP GET /students/
                        HTTP GET /payments/
                              ↓
                        JSON Response
                              ↓
                    Calcula métricas → Render UI
```

## Mejoras UX en Pagos

Se implementaron mejoras significativas en la experiencia de usuario del módulo de pagos para hacerlo más intuitivo, robusto y amigable.

### 1. Loading States

**Durante el envío del formulario:**
- El botón se deshabilita mientras se procesa el pago
- Se muestra un spinner de carga animado
- Texto cambia de "Registrar Pago" a "Procesando..."

```jsx
<button disabled={formLoading}>
  {formLoading ? (
    <span className="flex items-center gap-2">
      <svg className="animate-spin" ... />
      Procesando...
    </span>
  ) : 'Registrar Pago'}
</button>
```

### 2. Mensaje de Éxito

Al completarse el pago exitosamente, se muestra:

- **Icono de check** verde
- **Mensaje claro**: "Pago registrado correctamente"
- **Detalles del pago**: Monto y fecha del pago recién creado
- **Auto-cierre**: El formulario se cierra automáticamente después de 2 segundos

```jsx
{formSuccess && (
  <div className="rounded bg-green-100 p-4 text-green-700">
    <div className="flex items-center gap-2">
      <CheckIcon />
      <span className="font-medium">Pago registrado correctamente</span>
    </div>
    {lastPayment && (
      <div className="mt-2 text-sm">
        <p>Monto: <span className="font-medium">${lastPayment.amount}</span></p>
        <p>Fecha: <span className="font-medium">{formatDate(lastPayment.payment_date)}</span></p>
      </div>
    )}
  </div>
)}
```

### 3. Manejo de Errores

**Errores por campo:**
- Borde rojo en el input con error
- Mensaje específico debajo de cada campo
- Limpieza automática de errores al escribir

**Error general:**
- Mensaje destacado en rojo con icono
- Texto descriptivo: "Error al registrar el pago. Intenta nuevamente."

```jsx
// Errores de validación
const [fieldErrors, setFieldErrors] = useState({});

// Mostrar error en campo
<select className={`border ${fieldErrors.student_id ? 'border-red-500' : 'border-gray-300'}`}>
{fieldErrors.student_id && (
  <p className="text-xs text-red-600">{fieldErrors.student_id}</p>
)}
```

### 4. Reset de Formulario

Después de un pago exitoso:

1. **Limpieza de campos**: `student_id`, `amount`, `notes` → `''`
2. **Limpieza de errores**: `fieldErrors` → `{}`
3. **Cierre automático**: El formulario se cierra después de 2 segundos
4. **Refresh de lista**: La tabla se actualiza inmediatamente

```jsx
setFormData({ student_id: '', amount: '', notes: '' });
setFieldErrors({});
await loadPayments(); // Recarga la tabla
```

### 5. Validaciones

**Validaciones en tiempo real:**

| Campo | Validación | Mensaje de error |
|-------|------------|------------------|
| `student_id` | Requerido | "Debes seleccionar un estudiante" |
| `amount` | > 0 | "El monto debe ser mayor a 0" |
| `amount` | Número válido | (HTML5 native validation) |

**Implementación:**

```jsx
function validateForm() {
  const errors = {};

  if (!formData.student_id) {
    errors.student_id = 'Debes seleccionar un estudiante';
  }

  const amountValue = parseFloat(formData.amount);
  if (!formData.amount || isNaN(amountValue) || amountValue <= 0) {
    errors.amount = 'El monto debe ser mayor a 0';
  }

  setFieldErrors(errors);
  return Object.keys(errors).length === 0;
}
```

### 6. Feedback Visual

**Detalles del último pago:**

Después de crear un pago, se muestra:
- Monto del pago registrado
- Fecha de pago formateada (DD/MM/YYYY)

```jsx
const [lastPayment, setLastPayment] = useState(null);

// Al crear pago exitoso
const result = await quickPay(token, data);
setLastPayment(result);

// Mostrar en UI
<p>Monto: <span className="font-medium">${lastPayment.amount}</span></p>
<p>Fecha: <span className="font-medium">{formatDate(lastPayment.payment_date)}</span></p>
```

### 7. UX Extra (Bonus)

**Botón deshabilitado si faltan campos:**

```jsx
function isFormValid() {
  const hasStudent = formData.student_id?.trim() !== '';
  const hasAmount = parseFloat(formData.amount) > 0;
  return hasStudent && hasAmount && !formLoading;
}

<button disabled={!isFormValid() || formLoading}>
```

**Estilos de error en campos:**

```jsx
<select className={`border px-3 py-2 ${
  fieldErrors.student_id
    ? 'border-red-500 focus:border-red-500'  // Error
    : 'border-gray-300 focus:border-blue-500' // Normal
}`}>
```

**Limpieza de errores al escribir:**

```jsx
function handleInputChange(e) {
  const { name, value } = e.target;
  setFormData(prev => ({ ...prev, [name]: value }));

  // Limpiar error del campo
  if (fieldErrors[name]) {
    setFieldErrors(prev => ({ ...prev, [name]: null }));
  }
}
```

**Indicadores de campo obligatorio:**

```jsx
<label>
  Estudiante <span className="text-red-500">*</span>
</label>
```

### Resumen de Estados

```
Usuario abre formulario
        ↓
Selecciona estudiante y monto
        ↓
Hace clic en "Registrar Pago"
        ↓
┌─────────────────┬─────────────────┐
│  VALIDACIÓN OK  │ VALIDACIÓN FAIL │
│                 │                 │
│  Botón cambia   │  Muestra errores│
│  a "Procesando" │  en campos      │
│                 │                 │
│  Request al API │  Usuario corrige│
│                 │                 │
│  ÉXITO          │                 │
│  - Verde: "Pago │                 │
│    registrado"  │                 │
│  - Detalles     │                 │
│  - Reset campos │                 │
│  - Refresh lista│                 │
│  - Auto-cierre  │                 │
└─────────────────┴─────────────────┘
```

### Cómo Probar

1. **Abrir formulario**: Clic en "Registrar Pago"
2. **Validaciones**: Intentar enviar sin completar campos → ver errores
3. **Crear pago**: Completar campos válidos → clic en "Registrar Pago"
4. **Ver loading**: Botón cambia a "Procesando..." con spinner
5. **Ver éxito**: Mensaje verde con check y detalles del pago
6. **Ver lista**: La tabla se actualiza con el nuevo pago
7. **Auto-cierre**: El formulario se cierra solo después de 2 segundos

## Búsqueda de Estudiantes

Se implementó una funcionalidad de búsqueda en tiempo real para encontrar estudiantes por nombre o apellido.

### Endpoint Utilizado

- `GET /students/search?q={texto}` - Busca estudiantes por nombre

### Comportamiento del Input

| Condición | Acción |
|-----------|--------|
| Input vacío | Muestra la lista completa de estudiantes |
| 1 carácter | No realiza búsqueda (espera...) |
| ≥ 2 caracteres | Lanza búsqueda con debounce de 400ms |
| Resultados encontrados | Muestra cantidad de resultados |
| Sin resultados | Muestra "No se encontraron resultados" |

### Implementación del Debounce

```jsx
useEffect(() => {
  if (!token) return;

  // Limpiar resultados si input vacío
  if (!searchTerm || searchTerm.trim() === '') {
    setSearchResults(null);
    return;
  }

  // No buscar si tiene menos de 2 caracteres
  if (searchTerm.trim().length < 2) {
    return;
  }

  setSearchLoading(true);

  const timeoutId = setTimeout(async () => {
    try {
      const results = await searchStudents(token, searchTerm.trim());
      setSearchResults(results || []);
    } catch (err) {
      setSearchError(err.message);
    } finally {
      setSearchLoading(false);
    }
  }, 400); // 400ms de debounce

  return () => clearTimeout(timeoutId);
}, [searchTerm, token]);
```

### UI de Búsqueda

**Input con icono de búsqueda:**
```jsx
<div className="relative">
  <div className="absolute inset-y-0 left-0 flex items-center pl-3">
    <SearchIcon className="h-5 w-5 text-gray-400" />
  </div>
  <input
    type="text"
    placeholder="Buscar estudiante..."
    value={searchTerm}
    onChange={handleSearchChange}
    className="w-full py-2 pl-10 pr-10"
  />
  {/* Botón limpiar (X) aparece cuando hay texto */}
  {searchTerm && (
    <button onClick={clearSearch}>
      <XIcon className="h-5 w-5" />
    </button>
  )}
</div>
```

**Estados visuales:**
- **Cargando**: "Buscando..." debajo del input
- **Error**: Mensaje en rojo
- **Sin resultados**: "No se encontraron resultados para 'texto'"
- **Con resultados**: "X resultados encontrados"

### Lógica de Visualización

```jsx
// Determina qué estudiantes mostrar
const displayedStudents = searchResults !== null ? searchResults : students;
const isSearching = searchTerm.trim().length >= 2;

// En la tabla
{isSearching
  ? `No se encontraron resultados para "${searchTerm}"`
  : 'No hay estudiantes registrados.'}
```

### Estados del Componente

```jsx
const [searchTerm, setSearchTerm] = useState('');
const [searchResults, setSearchResults] = useState(null);
const [searchLoading, setSearchLoading] = useState(false);
const [searchError, setSearchError] = useState(null);
```

- `searchTerm`: Texto actual del input
- `searchResults`: Resultados de la búsqueda (null = no hay búsqueda activa)
- `searchLoading`: Indicador de carga durante la búsqueda
- `searchError`: Mensaje de error si falla la petición

### Cómo Probar

1. Ir a `/students`
2. Escribir un nombre en el input de búsqueda
3. Esperar 400ms (debounce)
4. Ver resultados filtrados
5. Ver mensaje con cantidad de resultados
6. Borrar el input (X) → vuelve la lista completa
7. Escribir texto que no exista → ver "No se encontraron resultados"

### Edge Cases Manejados

- **Query < 2 chars**: No se realiza la búsqueda
- **Input vacío**: Se limpian resultados y se muestra lista original
- **Usuario escribe rápido**: El debounce cancela búsquedas previas
- **Error de red**: Se muestra mensaje de error amigable
- **Token expirado**: Se maneja en el catch del error

## Detalle de Estudiante

Se implementó una página de detalle para visualizar la información completa de un estudiante y su historial de pagos.

### Endpoint Utilizado

- `GET /payments/student/{student_id}` - Obtiene todos los pagos de un estudiante específico

### Navegación

Desde la lista de estudiantes (`/students`), cada fila es clickeable y lleva al detalle del estudiante:

```
/students/:id
```

### Componente: StudentDetail.jsx

Archivo: `src/pages/StudentDetail.jsx`

**Funcionalidades:**

- **Información del estudiante**: Nombre, curso, teléfono, dirección, estado y fecha de inscripción
- **Historial de pagos**: Tabla con montos, estados, fechas de pago y vencimiento
- **Registro rápido**: Botón "Registrar Pago" que navega a `/payments` con el estudiante preseleccionado
- **Navegación**: Botón "Volver" para regresar a la lista de estudiantes

### Estructura de Datos Mostrados

**Información del Estudiante:**
| Campo | Descripción |
|-------|-------------|
| Nombre | first_name + last_name |
| Curso | boxing / kickboxing / both |
| Teléfono | phone (si existe) |
| Dirección | address (si existe) |
| Estado | Activo / Inactivo |
| Inscripción | enrollment_date |

**Historial de Pagos:**
| Campo | Descripción |
|-------|-------------|
| Monto | amount |
| Estado | Pagado / Pendiente / Vencido (con badge de color) |
| Fecha de Pago | payment_date |
| Fecha de Vencimiento | due_date |

### UX y Estados

**Loading State:**
- Muestra "Cargando..." centrado mientras se obtienen los datos

**Error State:**
- Mensaje de error con botón para volver a la lista de estudiantes

**Sin Pagos:**
- Mensaje: "Este estudiante no tiene pagos registrados."

### Integración con Quick Pay

El botón "Registrar Pago" utiliza la navegación de React Router para pasar el ID del estudiante:

```jsx
function handleRegisterPayment() {
  navigate('/payments', {
    state: { preselectedStudentId: id },
  });
}
```

En `Payments.jsx`, el componente detecta este estado y:
1. Abre automáticamente el formulario de registro
2. Preselecciona el estudiante en el dropdown
3. Limpia el estado de navegación para evitar repeticiones

```jsx
useEffect(() => {
  const preselectedStudentId = location.state?.preselectedStudentId;
  if (preselectedStudentId && token) {
    setShowForm(true);
    setFormData(prev => ({ ...prev, student_id: preselectedStudentId }));
    window.history.replaceState({}, document.title);
  }
}, [location.state, token]);
```

### Cómo Probar

1. **Navegar a estudiantes**: Ir a `/students`
2. **Seleccionar estudiante**: Hacer clic en cualquier fila de la tabla
3. **Ver detalle**: Se muestra la información del estudiante y su historial de pagos
4. **Registrar pago**: Clic en "Registrar Pago" → redirige a `/payments` con el estudiante preseleccionado
5. **Volver**: Clic en "Volver a Estudiantes" para regresar a la lista

## Detalle de Estudiante

Se implementó una página para visualizar el detalle de un estudiante específico y su historial de pagos.

### Página: StudentDetail.jsx

Archivo: `src/pages/StudentDetail.jsx`

### Cómo Navegar

Desde la lista de estudiantes (`/students`):
1. Haz clic en cualquier fila de la tabla de estudiantes
2. Se navegará automáticamente a `/students/{id}`

Desde cualquier otra página:
1. Navegar directamente a `/students/{id}` reemplazando `{id}` con el UUID del estudiante

### Información Mostrada

#### Información del Estudiante
- **Nombre completo**: Nombre y apellido del estudiante
- **Curso**: El curso al que está inscrito (boxeo, kickboxing, ambos)
- **Teléfono**: Número de contacto (si existe)
- **Dirección**: Dirección registrada (si existe)
- **Estado**: Activo o inactivo
- **Fecha de Inscripción**: Fecha en que se registró

#### Historial de Pagos
Tabla con los pagos del estudiante mostrando:
- **Monto**: Valor del pago en pesos chilenos
- **Estado**: Pagado (verde), Pendiente (amarillo), Vencido (rojo)
- **Fecha de Pago**: Cuándo se realizó el pago
- **Fecha de Vencimiento**: Fecha límite del pago

### Endpoint Utilizado

```
GET /payments/student/{student_id}
```

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "amount": 25000,
      "status": "paid",
      "payment_date": "2024-03-15",
      "due_date": "2024-03-31"
    }
  ],
  "total": 5,
  "pages": 1,
  "current_page": 1
}
```

### Estados de UI

- **Cargando**: Muestra "Cargando..." mientras se obtienen los datos del estudiante y sus pagos
- **Error**: Muestra mensaje de error si falla la carga con botón para volver a la lista
- **Sin pagos**: Muestra mensaje "Este estudiante no tiene pagos registrados." cuando el estudiante no tiene pagos

### Funcionalidad Bonus: Registrar Pago

El botón **"Registrar Pago"** en la esquina superior derecha permite:
1. Navegar a la página de pagos (`/payments`)
2. Abrir automáticamente el formulario de registro
3. Preseleccionar al estudiante actual en el dropdown

**Flujo de navegación**:
```javascript
navigate('/payments', {
  state: { preselectedStudentId: id },
});
```

### Cómo Probar

1. Ir a la página de estudiantes (`/students`)
2. Hacer clic en cualquier estudiante de la tabla
3. Verificar que se muestra:
   - Información completa del estudiante
   - Tabla con el historial de pagos
   - Mensaje si el estudiante no tiene pagos
4. (Opcional) Clic en "Registrar Pago" para ir a la página de pagos con el estudiante preseleccionado

### Componentes Utilizados

| Componente | Descripción |
|-------------|-------------|
| `useParams` | Obtiene el `id` del estudiante de la URL |
| `useNavigate` | Navega a la lista de estudiantes o a pagos |
| `getStudent` | Obtiene datos del estudiante por ID |
| `getStudentPayments` | Obtiene los pagos del estudiante |

## Manejo de Fechas y Consistencia en Pagos

El sistema implementa un manejo estandarizado de fechas para garantizar consistencia entre backend y frontend, evitando problemas de zonas horarias y formatos.

### Estándar Global

Todas las fechas en el sistema siguen estas reglas:

1. **Usar SIEMPRE datetime con timezone (UTC)**
   ```python
   from datetime import datetime, timezone
   now = datetime.now(timezone.utc)
   ```

2. **NO usar:**
   - `date.today()` - No tiene información de hora ni timezone
   - `datetime.now()` sin timezone - Puede causar inconsistencias

3. **Para sumar meses usar relativedelta:**
   ```python
   from dateutil.relativedelta import relativedelta
   due_date = now + relativedelta(months=1)
   ```

### Diferencia: 30 días vs 1 mes

Es importante entender la diferencia:

| Método | Resultado | Casos borde |
|--------|-----------|-------------|
| `timedelta(days=30)` | Simplemente suma 30 días | Enero 31 → Marzo 2 |
| `relativedelta(months=1)` | Suma 1 mes calendario | Enero 31 → Febrero 28/29 |

**Ejemplo práctico:**
```python
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

fecha = datetime(2024, 1, 31, 10, 0, 0)

# Suma 30 días
fecha + timedelta(days=30)  # → 2024-03-01 10:00:00

# Suma 1 mes
fecha + relativedelta(months=1)  # → 2024-02-29 10:00:00 (bisiesto)
```

### Quick Pay con Fechas Correctas

El endpoint `/payments/quick-pay` ahora implementa:

1. **payment_date**: Fecha/hora actual UTC del servidor
2. **due_date**: Fecha/hora actual + 1 mes (usando relativedelta)

```python
now = datetime.now(timezone.utc)
due_date = now + relativedelta(months=1)

payment = payment_service.create_payment(
    student_id=student_id,
    amount=amount,
    due_date=due_date,  # ← 1 mes desde ahora
    ...
)
payment = payment_service.mark_as_paid(payment.id, now)
```

### Serialización ISO 8601

Todas las fechas se envían en formato ISO 8601:
```
2024-03-20T15:30:00+00:00
```

**Frontend:** JavaScript automáticamente parsea este formato:
```javascript
const date = new Date('2024-03-20T15:30:00+00:00');
date.toLocaleDateString('es-CO');  // → "20/03/2024"
```

### Casos Borde Manejados

| Fecha inicial | +1 mes | Resultado |
|---------------|--------|-----------|
| 2024-01-31 | relativedelta(months=1) | 2024-02-29 (bisiesto) |
| 2024-03-31 | relativedelta(months=1) | 2024-04-30 |
| 2024-05-31 | relativedelta(months=1) | 2024-06-30 |

### Por Qué es Importante la Consistencia

1. **Evita desfases de horas**: Usar UTC evita problemas cuando el servidor y cliente están en zonas horarias diferentes

2. **Cálculos precisos**: `relativedelta` respeta el calendario real, no solo suma días

3. **Compatibilidad**: ISO 8601 es un estándar universal que cualquier lenguaje puede parsear

4. **Claridad**: Saber que todas las fechas son UTC elimina ambigüedad

### Cambios Realizados

**Backend:**
- Modelo `Payment`: `due_date` y `payment_date` ahora son `DateTime(timezone=True)`
- Schemas Pydantic: Campos de fecha cambiados a `datetime`
- Controllers: Usan `datetime.now(timezone.utc)` en lugar de `date.today()`
- Quick Pay: `due_date = now + relativedelta(months=1)`

**Frontend:**
- `formatDate` recibe strings ISO 8601 y usa `new Date()` para parsear
- No modifica timezone manualmente, solo formatea lo recibido

## Manejo de Fechas y Consistencia en Pagos

El sistema implementa un manejo consistente de fechas usando **datetime UTC con timezone** en todo el backend.

### Estándar Global

**Reglas aplicadas en TODO el proyecto:**

1. **Usar SIEMPRE datetime con timezone (UTC)**
   ```python
   from datetime import datetime, timezone
   now = datetime.now(timezone.utc)
   ```

2. **NO usar:**
   - `date.today()` - no tiene información de hora ni timezone
   - `datetime.now()` sin timezone - no es aware

3. **Para sumar meses usar relativedelta:**
   ```python
   from dateutil.relativedelta import relativedelta
   due_date = now + relativedelta(months=1)
   ```

### Diferencia: 30 días vs 1 mes

| Enfoque | Problema | Ejemplo |
|---------|----------|---------|
| `timedelta(days=30)` | Ignora calendario | 31 enero → 2 marzo |
| `relativedelta(months=1)` | Respeta calendario | 31 enero → 28/29 febrero |

**Siempre usar `relativedelta`** para cálculos de meses para respetar el calendario real.

### Cambios en Quick Pay

El endpoint `/payments/quick-pay` ahora:

1. Usa `datetime.now(timezone.utc)` para obtener fecha/hora actual
2. Calcula `due_date` como `now + relativedelta(months=1)`
3. Guarda ambos campos como datetime con timezone

**Ejemplo:**
```python
now = datetime.now(timezone.utc)  # 2024-03-20T15:30:00+00:00
due_date = now + relativedelta(months=1)  # 2024-04-20T15:30:00+00:00

payment = create_payment(
    due_date=due_date,
    ...
)
payment = mark_as_paid(payment.id, now)
```

### Serialización ISO 8601

Todas las fechas se envían en formato **ISO 8601**:
```json
{
  "payment_date": "2024-03-20T15:30:00+00:00",
  "due_date": "2024-04-20T15:30:00+00:00"
}
```

El frontend puede parsear esto directamente con `new Date()`:
```javascript
const date = new Date("2024-03-20T15:30:00+00:00");
```

### Frontend

La función `formatDate` en el frontend:
- NO modifica timezone manualmente
- Solo formatea la fecha recibida
- Usa `toLocaleDateString()` para mostrar en formato local

```javascript
function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-CO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}
```

### Por Qué es Importante la Consistencia

1. **Sin desfase de horas**: Todos los datetime tienen timezone UTC
2. **Cálculos correctos**: Los vencimientos se calculan correctamente
3. **Comparaciones confiables**: `due_date < now` funciona siempre
4. **Caso borde manejado**: 31 enero → 28/29 febrero funciona correctamente
5. **Frontend sin lógica compleja**: Solo formatea lo que recibe

### Endpoints Afectados

Todos los endpoints de pagos ahora usan datetime UTC:
- `POST /payments/` - Crear pago
- `POST /payments/quick-pay` - Pago rápido
- `POST /payments/{id}/mark-paid` - Marcar como pagado
- `GET /payments/` - Listar pagos
- `GET /payments/upcoming` - Próximos vencimientos
- `GET /payments/overdue` - Pagos vencidos
- `GET /students/upcoming-payments` - Próximos pagos por estudiante

## Licencia

MIT
