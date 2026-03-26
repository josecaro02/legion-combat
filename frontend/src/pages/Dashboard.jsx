import { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { authGet } from '../api/client';

function Dashboard() {
  const { user, token } = useAuth();
  const [data, setData] = useState({ students: 0, payments: 0, attendances: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Example: fetch dashboard data with auth token
    async function fetchData() {
      setLoading(true);
      try {
        // Example authenticated request
        // const result = await authGet('/students/', token);
        // setData(result);

        // Simulated data for now
        setData({ students: 45, payments: 12, attendances: 38 });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [token]);

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-gray-800">Dashboard</h1>

      <p className="mb-6 text-gray-600">
        Bienvenido, <span className="font-semibold">{user?.email}</span>.
        Rol: <span className="font-semibold">{user?.role}</span>.
      </p>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mt-8 grid gap-6 md:grid-cols-3">
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-2 text-lg font-semibold text-gray-700">Estudiantes</h2>
          <p className="text-3xl font-bold text-blue-600">
            {loading ? '...' : data.students}
          </p>
        </div>
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-2 text-lg font-semibold text-gray-700">Pagos Pendientes</h2>
          <p className="text-3xl font-bold text-yellow-600">
            {loading ? '...' : data.payments}
          </p>
        </div>
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-2 text-lg font-semibold text-gray-700">Asistencias Hoy</h2>
          <p className="text-3xl font-bold text-green-600">
            {loading ? '...' : data.attendances}
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
