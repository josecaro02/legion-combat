import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { hasPermission } from '../utils/permissions';
import { getStudents, createStudent, searchStudents } from '../api/students.api';

/**
 * Students Component
 *
 * Muestra lista de estudiantes con funcionalidad de búsqueda en tiempo real.
 * Incluye debounce para optimizar las llamadas a la API.
 */
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

  // Estados para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);

  const canView = hasPermission(user, 'canViewStudents');
  const canCreate = hasPermission(user, 'canCreateStudent');

  useEffect(() => {
    if (canView && token) {
      loadStudents();
    } else {
      setLoading(false);
    }
  }, [canView, token]);

  /**
   * Efecto de búsqueda con debounce
   * Espera 400ms después de que el usuario deja de escribir
   * Solo busca si hay 2 o más caracteres
   */
  useEffect(() => {
    if (!token || !canView) return;

    // Si el input está vacío, limpiar resultados y mostrar lista original
    if (!searchTerm.trim()) {
      setSearchResults(null);
      setSearchLoading(false);
      setSearchError(null);
      return;
    }

    // Solo buscar si tiene 2 o más caracteres
    if (searchTerm.trim().length < 2) {
      setSearchResults(null);
      return;
    }

    setSearchLoading(true);
    setSearchError(null);

    const debounceTimer = setTimeout(async () => {
      try {
        const results = await searchStudents(token, searchTerm.trim());
        setSearchResults(results || []);
      } catch (err) {
        setSearchError(err.message || 'Error al buscar estudiantes');
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 400); // 400ms de debounce

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, token, canView]);

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

  /**
   * Maneja cambios en el input de búsqueda
   * Actualiza searchTerm que dispara el efecto con debounce
   */
  function handleSearchChange(e) {
    setSearchTerm(e.target.value);
  }

  /**
   * Limpia el campo de búsqueda y vuelve a la lista original
   */
  function clearSearch() {
    setSearchTerm('');
    setSearchResults(null);
    setSearchError(null);
  }

  /**
   * Determina qué estudiantes mostrar
   * Si hay resultados de búsqueda, los muestra; si no, muestra la lista original
   */
  const displayedStudents = searchResults !== null ? searchResults : students;
  const isSearching = searchTerm.trim().length >= 2;

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

      {/* Barra de búsqueda */}
      {canView && (
        <div className="mb-4">
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <svg
                className="h-5 w-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Buscar estudiante..."
              value={searchTerm}
              onChange={handleSearchChange}
              className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-10 focus:border-blue-500 focus:outline-none"
            />
            {searchTerm && (
              <button
                onClick={clearSearch}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
              >
                <svg
                  className="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>

          {/* Estados de búsqueda */}
          {searchLoading && (
            <div className="mt-2 text-sm text-gray-500">
              Buscando...
            </div>
          )}

          {searchError && (
            <div className="mt-2 text-sm text-red-600">
              {searchError}
            </div>
          )}

          {isSearching && !searchLoading && searchResults?.length === 0 && (
            <div className="mt-2 text-sm text-gray-600">
              No se encontraron resultados para "{searchTerm}"
            </div>
          )}

          {searchResults?.length > 0 && (
            <div className="mt-2 text-sm text-gray-600">
              {searchResults.length} resultado{searchResults.length !== 1 ? 's' : ''} encontrado{searchResults.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>
      )}

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
              {displayedStudents.length === 0 ? (
                <tr>
                  <td
                    colSpan="4"
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    {isSearching
                      ? `No se encontraron resultados para "${searchTerm}"`
                      : 'No hay estudiantes registrados.'}
                  </td>
                </tr>
              ) : (
                displayedStudents.map(student => (
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
