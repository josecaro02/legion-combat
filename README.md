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

# Crear base de datos PostgreSQL
createdb legion_combat_dev

# Iniciar aplicación
python run.py
```

## Configuración

Variables de entorno en `.env`:

```
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/legion_combat_dev
JWT_SECRET_KEY=your-jwt-secret-key
```

## Uso

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

## Licencia

MIT
