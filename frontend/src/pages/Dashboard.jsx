import { useAuth } from '../auth/AuthContext';

/**
 * Dashboard - Main view after login
 *
 * Shows different sections based on user role:
 * - owner: sees Students and Payments sections
 * - professor: sees Students and Register Payment sections
 *
 * Future: Connect to backend for real data
 */
function Dashboard() {
  const { user } = useAuth();
  const role = user?.role;

  const isOwner = role === 'owner';
  const isProfessor = role === 'professor';

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-gray-800">Dashboard</h1>

      <p className="mb-6 text-gray-600">
        Bienvenido, <span className="font-semibold">{user?.email}</span>
        {' '}
        <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800">
          {role}
        </span>
      </p>

      {/* Common section for both roles */}
      <section className="mb-6">
        <h2 className="mb-3 text-lg font-semibold text-gray-700">Estudiantes</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg bg-white p-4 shadow">
            <p className="text-sm text-gray-500">Total Estudiantes</p>
            <p className="text-2xl font-bold text-blue-600">--</p>
          </div>
          <div className="flex items-center justify-end">
            <button className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
              Ver Estudiantes
            </button>
          </div>
        </div>
      </section>

      {/* Owner only: Payments section */}
      {isOwner && (
        <section className="mb-6">
          <h2 className="mb-3 text-lg font-semibold text-gray-700">Pagos</h2>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg bg-white p-4 shadow">
              <p className="text-sm text-gray-500">Pagos Pendientes</p>
              <p className="text-2xl font-bold text-yellow-600">--</p>
            </div>
            <div className="rounded-lg bg-white p-4 shadow">
              <p className="text-sm text-gray-500">Pagos Vencidos</p>
              <p className="text-2xl font-bold text-red-600">--</p>
            </div>
            <div className="flex items-center justify-end">
              <button className="rounded-md bg-yellow-600 px-4 py-2 text-white hover:bg-yellow-700">
                Ver Pagos
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Professor only: Register Payment section */}
      {isProfessor && (
        <section className="mb-6">
          <h2 className="mb-3 text-lg font-semibold text-gray-700">Pagos</h2>
          <div className="rounded-lg bg-white p-6 shadow">
            <p className="mb-4 text-gray-600">
              Registra un nuevo pago para un estudiante.
            </p>
            <button className="rounded-md bg-green-600 px-4 py-2 text-white hover:bg-green-700">
              Registrar Pago
            </button>
          </div>
        </section>
      )}

      {/* Quick actions - visible to both */}
      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-700">Acciones Rápidas</h2>
        <div className="flex flex-wrap gap-3">
          <button className="rounded-md border border-gray-300 bg-white px-4 py-2 hover:bg-gray-50">
            Buscar Estudiante
          </button>
          {isOwner && (
            <button className="rounded-md border border-gray-300 bg-white px-4 py-2 hover:bg-gray-50">
              Generar Reporte
            </button>
          )}
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
