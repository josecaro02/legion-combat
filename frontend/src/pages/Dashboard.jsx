function Dashboard() {
  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-gray-800">Dashboard</h1>
      <p className="text-gray-600">
        Bienvenido al sistema de gestión de Legión Combat.
      </p>

      <div className="mt-8 grid gap-6 md:grid-cols-3">
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-2 text-lg font-semibold text-gray-700">Estudiantes</h2>
          <p className="text-3xl font-bold text-blue-600">--</p>
        </div>
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-2 text-lg font-semibold text-gray-700">Pagos Pendientes</h2>
          <p className="text-3xl font-bold text-yellow-600">--</p>
        </div>
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-2 text-lg font-semibold text-gray-700">Asistencias Hoy</h2>
          <p className="text-3xl font-bold text-green-600">--</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
