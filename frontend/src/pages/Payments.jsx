import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { hasPermission } from '../utils/permissions';
import { quickPay, getPayments } from '../api/payments.api';
import { getStudents, getUpcomingPayments } from '../api/students.api';
import UpcomingPaymentsList from '../components/UpcomingPaymentsList';

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

  useEffect(() => {
    const preselectedStudentId = location.state?.preselectedStudentId;
    if (preselectedStudentId && token) {
      setShowForm(true);
      setFormData((prev) => ({
        ...prev,
        student_id: preselectedStudentId,
      }));
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

  function validateForm() {
    const errors = {};

    if (!formData.student_id || formData.student_id.trim() === '') {
      errors.student_id = 'Debes seleccionar un estudiante';
    }

    const amountValue = parseFloat(formData.amount);
    if (!formData.amount || isNaN(amountValue) || amountValue <= 0) {
      errors.amount = 'El monto debe ser mayor a 0';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canCreate) return;

    setFormError(null);
    setFormSuccess(false);
    setLastPayment(null);

    if (!validateForm()) return;

    setFormLoading(true);

    try {
      const data = {
        student_id: formData.student_id,
        amount: parseFloat(formData.amount),
        notes: formData.notes || undefined,
      };

      const result = await quickPay(token, data);

      setLastPayment(result);
      setFormSuccess(true);

      setFormData({
        student_id: '',
        amount: '',
        notes: '',
      });
      setFieldErrors({});

      await loadPayments();

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

  function handleInputChange(e) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: null }));
    }
  }

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
      <div className="flex h-64 items-center justify-center bg-black text-white">
        <div className="text-lg animate-pulse">Cargando...</div>
      </div>
    );
  }

  if (!canView) {
    return (
      <div className="rounded-xl border border-red-500 bg-red-900/20 p-4 text-red-300">
        No tienes permiso para ver pagos.
      </div>
    );
  }

  return (
<div className="space-y-8 text-white relative">
      {/* 1. HEADER REFORMADO */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-legion font-bold tracking-widest text-white flex items-center gap-3">
            Pagos
          </h1>
          <p className="text-muted text-sm mt-1 uppercase tracking-tighter">Gestión de recaudos y vencimientos</p>
        </div>

        <div className="flex gap-3">
           <button
            onClick={handleUpcomingPayments}
            disabled={upcomingLoading}
            className="rounded-md border border-gold/50 bg-gold/10 px-4 py-2 text-xs font-legion uppercase tracking-wider text-gold hover:bg-gold hover:text-black transition duration-300 disabled:opacity-50"
          >
            {upcomingLoading ? 'Cargando...' : 'Próximos a vencer'}
          </button>

          {canCreate && (
            <button
              onClick={() => {
                setShowForm(!showForm);
                if (showForm) {
                  setFormError(null);
                  setFieldErrors({});
                  setFormSuccess(false);
                }
              }}
              className="rounded-md bg-gold px-6 py-2 text-xs font-legion font-bold uppercase tracking-widest text-black hover:bg-goldLight transition duration-300 shadow-[0_0_15px_rgba(196,164,124,0.3)]"
            >
              {showForm ? 'Cancelar' : 'Registrar Pago'}
            </button>
          )}
        </div>
      </div>

      {/* 2. FORMULARIO CON ESTÉTICA DE TARJETA (Línea 193 aprox) */}
      {showForm && canCreate && (
        <div className="rounded-xl bg-card/80 backdrop-blur-md border border-border p-6 shadow-soft animate-in fade-in slide-in-from-top-4 duration-300">
          <h2 className="mb-6 text-sm font-legion uppercase tracking-widest text-gold">
            Nuevo Registro de Pago
          </h2>

          <form onSubmit={handleSubmit} className="grid gap-6 md:grid-cols-3">
            <div className="md:col-span-1">
              <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">Estudiante</label>
              <select
                name="student_id"
                value={formData.student_id}
                onChange={handleInputChange}
                disabled={formLoading}
                className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-white focus:border-gold/50 focus:outline-none transition-colors appearance-none"
              >
                <option value="">Seleccionar...</option>
                {students.map((student) => (
                  <option key={student.id} value={student.id} className="bg-[#1a1a1a]">
                    {student.first_name} {student.last_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">Monto</label>
              <input
                type="text"
                name="amount"
                value={formData.amount}
                onChange={handleInputChange}
                className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-gold placeholder-gray-600 focus:border-gold/50 focus:outline-none"
                placeholder="0.00"
              />
            </div>

            <div>
              <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">Notas (Opcional)</label>
              <input
                type="text"
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-white placeholder-gray-600 focus:border-gold/50 focus:outline-none"
                placeholder="Ej: Mensualidad Abril"
              />
            </div>

            <div className="md:col-span-3 flex justify-end">
              <button
                type="submit"
                disabled={!isFormValid() || formLoading}
                className="w-full md:w-auto min-w-[200px] rounded-md bg-white py-3 px-8 text-xs font-bold uppercase tracking-widest text-black hover:bg-gold transition-all duration-300 disabled:opacity-20"
              >
                {formLoading ? 'Procesando...' : 'Confirmar Transacción'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 3. TABLA PREMIUM (Línea 298 aprox) */}
      <div className="rounded-xl bg-card/40 backdrop-blur-sm border border-border shadow-soft overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-white/5">
              <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted">Estudiante</th>
              <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted">Monto</th>
              <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted">Estado</th>
              <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted">Fecha</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-border/50">
            {payments.map((payment) => (
              <tr key={payment.id} className="hover:bg-white/[0.02] transition-colors group">
                <td className="px-6 py-4 text-sm font-medium text-white/90 group-hover:text-white">
                  {payment.student_name || payment.student_id}
                </td>
                <td className="px-6 py-4 text-sm font-semibold text-gold">
                  ${Number(payment.amount).toLocaleString('es-CL')}
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                    payment.status === 'paid' 
                    ? 'bg-green-500/10 text-green-400 border border-green-500/20' 
                    : 'bg-red-500/10 text-red-400 border border-red-500/20'
                  }`}>
                    {payment.status === 'paid' ? 'Completado' : 'Pendiente'}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-muted">
                  {formatDate(payment.payment_date)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Payments;
