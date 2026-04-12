import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { hasPermission } from '../utils/permissions';
import { quickPay, getPayments } from '../api/payments.api';
import { getStudents, getUpcomingPayments } from '../api/students.api';
import UpcomingPaymentsList from '../components/UpcomingPaymentsList';

/**
 * Payments Component
 *
 * Muestra lista de pagos y permite registrar nuevos pagos mediante Quick Pay.
 * Incluye mejoras UX: loading states, validaciones, manejo de errores,
 * feedback visual y reset de formulario.
 */
function Payments() {
  const { user, token } = useAuth();
  const location = useLocation();
  const [payments, setPayments] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    student_id: '',
    amount: '',
    notes: '',
  });
  const [formError, setFormError] = useState(null);
  const [formSuccess, setFormSuccess] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [lastPayment, setLastPayment] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});

  // Upcoming payments state
  const [upcomingData, setUpcomingData] = useState(null);
  const [upcomingLoading, setUpcomingLoading] = useState(false);
  const [upcomingError, setUpcomingError] = useState(null);
  const [upcomingShowList, setUpcomingShowList] = useState(false);

  const canView = hasPermission(user, 'canViewPayments');
  const canCreate = hasPermission(user, 'canCreatePayment');

  useEffect(() => {
    if (canView && token) {
      loadPayments();
    } else {
      setLoading(false);
    }
  }, [canView, token]);

  /**
   * Efecto para manejar estudiante preseleccionado desde navegación
   */
  useEffect(() => {
    const preselectedStudentId = location.state?.preselectedStudentId;
    if (preselectedStudentId && token) {
      setShowForm(true);
      setFormData((prev) => ({
        ...prev,
        student_id: preselectedStudentId,
      }));
      // Limpiar el estado de navegación
      window.history.replaceState({}, document.title);
    }
  }, [location.state, token]);

  useEffect(() => {
    if (token && showForm) {
      loadStudents();
    }
  }, [token, showForm]);

  async function loadPayments() {
    try {
      setLoading(true);
      setError(null);
      const result = await getPayments(token);
      setPayments(result.items || []);
    } catch (err) {
      setError(err.message || 'Error al cargar pagos');
    } finally {
      setLoading(false);
    }
  }

  async function loadStudents() {
    try {
      const result = await getStudents(token);
      setStudents(result.items || []);
    } catch (err) {
      console.error('Error loading students:', err);
    }
  }

  /**
   * Validaciones del formulario
   * Retorna true si el formulario es válido, false en caso contrario
   */
  function validateForm() {
    const errors = {};

    // Validar student_id
    if (!formData.student_id || formData.student_id.trim() === '') {
      errors.student_id = 'Debes seleccionar un estudiante';
    }

    // Validar amount
    const amountValue = parseFloat(formData.amount);
    if (!formData.amount || isNaN(amountValue) || amountValue <= 0) {
      errors.amount = 'El monto debe ser mayor a 0';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  /**
   * Maneja el envío del formulario de pago
   * Incluye validaciones, loading state y manejo de errores
   */
  async function handleSubmit(e) {
    e.preventDefault();
    if (!canCreate) return;

    // Limpiar estados anteriores
    setFormError(null);
    setFormSuccess(false);
    setLastPayment(null);

    // Validar formulario
    if (!validateForm()) {
      return;
    }

    setFormLoading(true);

    try {
      const data = {
        student_id: formData.student_id,
        amount: parseFloat(formData.amount),
        notes: formData.notes || undefined,
      };

      const result = await quickPay(token, data);

      // Guardar referencia al último pago creado para feedback visual
      setLastPayment(result);
      setFormSuccess(true);

      // Resetear formulario
      setFormData({
        student_id: '',
        amount: '',
        notes: '',
      });
      setFieldErrors({});

      // Recargar lista de pagos
      await loadPayments();

      // Cerrar formulario después de 2 segundos
      setTimeout(() => {
        setShowForm(false);
        setFormSuccess(false);
        setLastPayment(null);
      }, 2000);
    } catch (err) {
      setFormError(err.message || 'Error al registrar el pago. Intenta nuevamente.');
    } finally {
      setFormLoading(false);
    }
  }

  /**
   * Maneja cambios en los inputs del formulario
   * Limpia errores de campo al escribir
   */
  function handleInputChange(e) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Limpiar error del campo cuando el usuario escribe
    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: null }));
    }
  }

  /**
   * Verifica si el formulario está listo para enviar
   * Usado para deshabilitar/habilitar el botón de submit
   */
  function isFormValid() {
    const hasStudent = formData.student_id && formData.student_id.trim() !== '';
    const hasAmount = formData.amount && parseFloat(formData.amount) > 0;
    return hasStudent && hasAmount && !formLoading;
  }

  async function handleUpcomingPayments() {
    if (!token) return;
    setUpcomingLoading(true);
    setUpcomingError(null);
    try {
      const result = await getUpcomingPayments(token);
      setUpcomingData(result);
      setUpcomingShowList(true);
    } catch (err) {
      setUpcomingError(err.message || 'Error al cargar próximos pagos');
    } finally {
      setUpcomingLoading(false);
    }
  }

  /**
   * Formatea la fecha para mostrar al usuario
   */
  function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
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
        No tienes permiso para ver pagos.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Pagos</h1>
        {canCreate && (
          <button
            onClick={() => {
              setShowForm(!showForm);
              // Limpiar errores al abrir/cerrar formulario
              if (showForm) {
                setFormError(null);
                setFieldErrors({});
                setFormSuccess(false);
              }
            }}
            className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            {showForm ? 'Cancelar' : 'Registrar Pago'}
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-700">{error}</div>
      )}

      {showForm && canCreate && (
        <div className="mb-6 rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-700">
            Registrar Pago Rápido
          </h2>

          {/* Mensaje de error general */}
          {formError && (
            <div className="mb-4 rounded bg-red-100 p-3 text-red-700">
              <span className="font-medium">Error: </span>
              {formError}
            </div>
          )}

          {/* Mensaje de éxito con detalles */}
          {formSuccess && (
            <div className="mb-4 rounded bg-green-100 p-4 text-green-700">
              <div className="flex items-center gap-2">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="font-medium">Pago registrado correctamente</span>
              </div>
              {lastPayment && (
                <div className="mt-2 pl-7 text-sm">
                  <p>Monto: <span className="font-medium">${lastPayment.amount}</span></p>
                  <p>Fecha: <span className="font-medium">{formatDate(lastPayment.payment_date)}</span></p>
                </div>
              )}
            </div>
          )}

          <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2">
            {/* Campo Estudiante */}
            <div className="md:col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Estudiante <span className="text-red-500">*</span>
              </label>
              <select
                name="student_id"
                value={formData.student_id}
                onChange={handleInputChange}
                disabled={formLoading}
                className={`w-full rounded-md border px-3 py-2 focus:outline-none ${
                  fieldErrors.student_id
                    ? 'border-red-500 focus:border-red-500'
                    : 'border-gray-300 focus:border-blue-500'
                }`}
              >
                <option value="">Seleccionar estudiante</option>
                {students.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.first_name} {student.last_name}
                  </option>
                ))}
              </select>
              {fieldErrors.student_id && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.student_id}</p>
              )}
            </div>

            {/* Campo Monto */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Monto <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleInputChange}
                disabled={formLoading}
                min="1"
                step="1"
                placeholder="25000"
                className={`w-full rounded-md border px-3 py-2 focus:outline-none ${
                  fieldErrors.amount
                    ? 'border-red-500 focus:border-red-500'
                    : 'border-gray-300 focus:border-blue-500'
                }`}
              />
              {fieldErrors.amount && (
                <p className="mt-1 text-xs text-red-600">{fieldErrors.amount}</p>
              )}
            </div>

            {/* Campo Notas */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Notas
              </label>
              <input
                type="text"
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                disabled={formLoading}
                placeholder="Pago mensualidad marzo"
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Botón de submit */}
            <div className="md:col-span-2">
              <button
                type="submit"
                disabled={!isFormValid() || formLoading}
                className={`rounded-md px-6 py-2 text-white transition-colors ${
                  !isFormValid() || formLoading
                    ? 'cursor-not-allowed bg-gray-400'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {formLoading ? (
                  <span className="flex items-center gap-2">
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Procesando...
                  </span>
                ) : (
                  'Registrar Pago'
                )}
              </button>
            </div>
          </form>

          <p className="mt-4 text-xs text-gray-500">
            El pago se creará y se marcará como pagado automáticamente con la
            fecha de hoy.
          </p>
        </div>
      )}

      {/* Upcoming Payments section */}
      <div className="mb-6">
        <button
          onClick={handleUpcomingPayments}
          disabled={upcomingLoading}
          className="rounded-md bg-yellow-600 px-4 py-2 text-white hover:bg-yellow-700 disabled:cursor-not-allowed disabled:bg-gray-400"
        >
          {upcomingLoading ? 'Cargando...' : 'Pagos próximos a vencer'}
        </button>

        {upcomingLoading && (
          <p className="mt-4 text-gray-600">Cargando...</p>
        )}

        {upcomingError && (
          <p className="mt-4 text-red-700">{upcomingError}</p>
        )}

        {upcomingShowList && upcomingData && (
          <UpcomingPaymentsList items={upcomingData.items} />
        )}
      </div>

      <div className="rounded-lg bg-white shadow">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Estudiante
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Monto
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Estado
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  Fecha de Pago
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
                    No hay pagos registrados.
                  </td>
                </tr>
              ) : (
                payments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {payment.student_name || payment.student_id}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      ${payment.amount}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {payment.status === 'paid' ? (
                        <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                          Pagado
                        </span>
                      ) : payment.status === 'pending' ? (
                        <span className="rounded-full bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-800">
                          Pendiente
                        </span>
                      ) : (
                        <span className="rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-800">
                          Vencido
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {payment.payment_date
                        ? new Date(payment.payment_date).toLocaleDateString(
                            'es-CL'
                          )
                        : '-'}
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

export default Payments;
