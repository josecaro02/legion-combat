import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { hasPermission } from '../utils/permissions';
import { quickPay, getPayments } from '../api/payments.api';
import { getStudents } from '../api/students.api';

function Payments() {
  const { user, token } = useAuth();
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

  const canView = hasPermission(user, 'canViewPayments');
  const canCreate = hasPermission(user, 'canCreatePayment');

  useEffect(() => {
    if (canView && token) {
      loadPayments();
    } else {
      setLoading(false);
    }
  }, [canView, token]);

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

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canCreate) return;

    try {
      setFormError(null);
      setFormSuccess(false);

      const data = {
        student_id: formData.student_id,
        amount: parseFloat(formData.amount),
        notes: formData.notes || undefined,
      };

      await quickPay(token, data);
      setFormSuccess(true);
      setFormData({
        student_id: '',
        amount: '',
        notes: '',
      });
      loadPayments();
      setTimeout(() => setShowForm(false), 1500);
    } catch (err) {
      setFormError(err.message || 'Error al registrar pago');
    }
  }

  function handleInputChange(e) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
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
            onClick={() => setShowForm(!showForm)}
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

          {formError && (
            <div className="mb-4 rounded bg-red-100 p-3 text-red-700">
              {formError}
            </div>
          )}

          {formSuccess && (
            <div className="mb-4 rounded bg-green-100 p-3 text-green-700">
              Pago registrado correctamente.
            </div>
          )}

          <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Estudiante *
              </label>
              <select
                name="student_id"
                value={formData.student_id}
                onChange={handleInputChange}
                required
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              >
                <option value="">Seleccionar estudiante</option>
                {students.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.first_name} {student.last_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Monto *
              </label>
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleInputChange}
                required
                min="1"
                step="1"
                placeholder="25000"
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Notas
              </label>
              <input
                type="text"
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                placeholder="Pago mensualidad marzo"
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div className="md:col-span-2">
              <button
                type="submit"
                className="rounded-md bg-green-600 px-6 py-2 text-white hover:bg-green-700"
              >
                Registrar Pago
              </button>
            </div>
          </form>

          <p className="mt-4 text-xs text-gray-500">
            El pago se creará y se marcará como pagado automáticamente con la
            fecha de hoy.
          </p>
        </div>
      )}

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
