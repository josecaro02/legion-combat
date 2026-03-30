import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { hasPermission } from '../utils/permissions';
import { getStudents, createStudent } from '../api/students.api';

function Students() {
  const { user, token } = useAuth();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    course: 'boxing',
    phone: '',
    address: '',
  });
  const [formError, setFormError] = useState(null);
  const [formSuccess, setFormSuccess] = useState(false);

  const canView = hasPermission(user, 'canViewStudents');
  const canCreate = hasPermission(user, 'canCreateStudent');

  useEffect(() => {
    if (canView && token) {
      loadStudents();
    } else {
      setLoading(false);
    }
  }, [canView, token]);

  async function loadStudents() {
    try {
      setLoading(true);
      setError(null);
      const result = await getStudents(token);
      setStudents(result.items || []);
    } catch (err) {
      setError(err.message || 'Error al cargar estudiantes');
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canCreate) return;

    try {
      setFormError(null);
      setFormSuccess(false);
      await createStudent(token, formData);
      setFormSuccess(true);
      setFormData({
        first_name: '',
        last_name: '',
        course: 'boxing',
        phone: '',
        address: '',
      });
      loadStudents();
      setTimeout(() => setShowForm(false), 1500);
    } catch (err) {
      setFormError(err.message || 'Error al crear estudiante');
    }
  }

  function handleInputChange(e) {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-lg text-gray-600">Cargando...</div>
      </div>
    );
  }

  if (!canView) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-700">
        No tienes permiso para ver estudiantes.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Estudiantes</h1>
        {canCreate && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            {showForm ? 'Cancelar' : 'Nuevo Estudiante'}
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-700">
          {error}
        </div>
      )}

      {showForm && canCreate && (
        <div className="mb-6 rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-700">
            Crear Estudiante
          </h2>

          {formError && (
            <div className="mb-4 rounded bg-red-100 p-3 text-red-700">
              {formError}
            </div>
          )}

          {formSuccess && (
            <div className="mb-4 rounded bg-green-100 p-3 text-green-700">
              Estudiante creado correctamente.
            </div>
          )}

          <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Nombre *
              </label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleInputChange}
                required
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Apellido *
              </label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleInputChange}
                required
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Curso *
              </label>
              <select
                name="course"
                value={formData.course}
                onChange={handleInputChange}
                required
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              >
                <option value="boxing">Boxeo</option>
                <option value="kickboxing">Kickboxing</option>
                <option value="both">Ambos</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Teléfono
              </label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleInputChange}
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div className="md:col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Dirección
              </label>
              <input
                type="text"
                name="address"
                value={formData.address}
                onChange={handleInputChange}
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div className="md:col-span-2">
              <button
                type="submit"
                className="rounded-md bg-green-600 px-6 py-2 text-white hover:bg-green-700"
              >
                Guardar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="rounded-lg bg-white shadow">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Nombre
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Apellido
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Curso
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Estado
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {students.length === 0 ? (
                <tr>
                  <td
                    colSpan="4"
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    No hay estudiantes registrados.
                  </td>
                </tr>
              ) : (
                students.map(student => (
                  <tr key={student.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {student.first_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {student.last_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <span className="capitalize">{student.course}</span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {student.is_active ? (
                        <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                          Activo
                        </span>
                      ) : (
                        <span className="rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
                          Inactivo
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Students;
