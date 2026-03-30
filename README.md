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

## Licencia

MIT
