import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { hasPermission } from '../utils/permissions';
import { getStudent } from '../api/students.api';
import { getStudentPayments } from '../api/payments.api';

/**
 * StudentDetail Component
 *
 * Muestra el detalle de un estudiante específico y su historial de pagos.
 * Permite navegar al formulario de registro de pago con el estudiante preseleccionado.
 */
function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, token } = useAuth();

  const [student, setStudent] = useState(null);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const canView = hasPermission(user, 'canViewStudents');
  const canCreatePayment = hasPermission(user, 'canCreatePayment');

  useEffect(() => {
    if (canView && token && id) {
      loadStudentData();
    } else {
      setLoading(false);
    }
  }, [canView, token, id]);

  /**
   * Carga los datos del estudiante y sus pagos
   */
  async function loadStudentData() {
    try {
      setLoading(true);
      setError(null);

      // Cargar estudiante y pagos en paralelo
      const [studentData, paymentsData] = await Promise.all([
        getStudent(token, id),
        getStudentPayments(token, id),
      ]);

      setStudent(studentData);
      setPayments(paymentsData.items || []);
    } catch (err) {
      setError(err.message || 'Error al cargar los datos del estudiante');
    } finally {
      setLoading(false);
    }
  }

  /**
   * Navega al formulario de pagos con el estudiante preseleccionado
   */
  function handleRegisterPayment() {
    navigate('/payments', {
      state: { preselectedStudentId: id },
    });
  }

  /**
   * Vuelve a la lista de estudiantes
   */
  function handleGoBack() {
    navigate('/students');
  }

  /**
   * Formatea la fecha para mostrar al usuario
   */
  function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  }

  /**
   * Traduce el estado del pago a español
   */
  function getStatusLabel(status) {
    const labels = {
      paid: 'Pagado',
      pending: 'Pendiente',
      overdue: 'Vencido',
    };
    return labels[status] || status;
  }

  /**
   * Retorna las clases CSS para el badge de estado
   */
  function getStatusClasses(status) {
    const classes = {
      paid: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      overdue: 'bg-red-100 text-red-800',
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
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

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-700">
        <p className="font-medium">Error</p>
        <p>{error}</p>
        <button
          onClick={handleGoBack}
          className="mt-4 rounded-md bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
        >
          Volver a Estudiantes
        </button>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="rounded-lg bg-yellow-50 p-4 text-yellow-700">
        No se encontró el estudiante.
        <button
          onClick={handleGoBack}
          className="mt-4 rounded-md bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
        >
          Volver a Estudiantes
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header con navegación */}
      <div className="mb-6">
        <button
          onClick={handleGoBack}
          className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-800"
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
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          Volver a Estudiantes
        </button>

        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">
            {student.first_name} {student.last_name}
          </h1>
          {canCreatePayment && (
            <button
              onClick={handleRegisterPayment}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              Registrar Pago
            </button>
          )}
        </div>
      </div>

      {/* Información del estudiante */}
      <div className="mb-6 rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-lg font-semibold text-gray-700">
          Información del Estudiante
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <span className="text-sm font-medium text-gray-500">Curso:</span>
            <p className="capitalize text-gray-900">{student.course}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Teléfono:</span>
            <p className="text-gray-900">
              {student.phone || 'No registrado'}
            </p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Dirección:</span>
            <p className="text-gray-900">
              {student.address || 'No registrada'}
            </p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Estado:</span>
            <p>
              {student.is_active ? (
                <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                  Activo
                </span>
              ) : (
                <span className="rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
                  Inactivo
                </span>
              )}
            </p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">
              Fecha de Inscripción:
            </span>
            <p className="text-gray-900">
              {formatDate(student.enrollment_date)}
            </p>
          </div>
        </div>
      </div>

      {/* Historial de pagos */}
      <div className="rounded-lg bg-white shadow">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-700">
            Historial de Pagos
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Monto
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Estado
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Fecha de Pago
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Fecha de Vencimiento
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {payments.length === 0 ? (
                <tr>
                  <td
                    colSpan="4"
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    Este estudiante no tiene pagos registrados.
                  </td>
                </tr>
              ) : (
                payments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      ${payment.amount}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${getStatusClasses(
                          payment.status
                        )}`}
                      >
                        {getStatusLabel(payment.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatDate(payment.payment_date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatDate(payment.due_date)}
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

export default StudentDetail;
