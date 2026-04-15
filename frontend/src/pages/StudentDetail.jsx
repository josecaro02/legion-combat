import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { hasPermission } from '../utils/permissions';
import { getStudent } from '../api/students.api';
import { getStudentPayments } from '../api/payments.api';

/**
 * StudentDetail Component
 * Rediseñado con estética Premium Oscura
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

  async function loadStudentData() {
    try {
      setLoading(true);
      setError(null);
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

  function handleRegisterPayment() {
    navigate('/payments', { state: { preselectedStudentId: id } });
  }

  function handleGoBack() {
    navigate('/students');
  }

  function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  }

  function getStatusLabel(status) {
    const labels = { paid: 'Pagado', pending: 'Pendiente', overdue: 'Vencido' };
    return labels[status] || status;
  }

  // Modificado: Ahora retorna clases acordes al tema oscuro
  function getStatusClasses(status) {
    const classes = {
      paid: 'bg-green-500/10 text-green-400 border border-green-500/20',
      pending: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20',
      overdue: 'bg-red-500/10 text-red-400 border border-red-500/20',
    };
    return classes[status] || 'bg-gray-500/10 text-gray-400 border border-gray-500/20';
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-lg font-legion uppercase tracking-widest text-gold animate-pulse">Cargando...</div>
      </div>
    );
  }

  if (!canView) {
    return (
      <div className="rounded-xl border border-red-500/50 bg-red-900/20 p-4 text-red-300">
        No tienes permiso para acceder a esta información.
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="rounded-xl border border-border bg-card/40 p-6 text-center">
        <p className="text-red-400 mb-4 font-bold uppercase tracking-widest">{error || "Estudiante no encontrado"}</p>
        <button onClick={handleGoBack} className="text-xs font-legion text-gold hover:text-white transition-colors uppercase underline underline-offset-4">
          Volver a la lista
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-white pb-10">
      {/* 1. HEADER Y NAVEGACIÓN */}
      <div className="flex flex-col gap-4">
        <button
          onClick={handleGoBack}
          className="group flex w-fit items-center gap-2 text-[10px] font-legion uppercase tracking-widest text-muted hover:text-gold transition-colors"
        >
          <svg className="h-4 w-4 transform group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Volver a Estudiantes
        </button>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
          <h1 className="text-4xl font-legion font-bold tracking-tighter text-white uppercase italic">
            {student.first_name} <span className="text-gold">{student.last_name}</span>
          </h1>
          {canCreatePayment && (
            <button
              onClick={handleRegisterPayment}
              className="rounded-md bg-gold px-6 py-2.5 text-xs font-legion font-bold uppercase tracking-widest text-black hover:bg-goldLight transition duration-300 shadow-[0_0_20px_rgba(212,175,55,0.2)]"
            >
              Registrar Pago
            </button>
          )}
        </div>
      </div>

      {/* 2. INFORMACIÓN DEL ESTUDIANTE (TARJETA CRISTAL) */}
      <div className="rounded-xl bg-card/40 backdrop-blur-md border border-border p-6 shadow-soft">
        <h2 className="mb-6 text-[10px] font-legion uppercase tracking-[0.3em] text-gold/80 border-b border-white/5 pb-2">
          Expediente del Guerrero
        </h2>
        <div className="grid gap-6 md:grid-cols-3">
          <div className="space-y-1">
            <span className="text-[10px] uppercase tracking-widest text-muted">Disciplina</span>
            <p className="text-sm font-bold uppercase text-white tracking-wide">{student.course}</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] uppercase tracking-widest text-muted">Contacto Directo</span>
            <p className="text-sm text-white/90">{student.phone || 'N/A'}</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] uppercase tracking-widest text-muted">Estado Actual</span>
            <div>
              <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold uppercase ${student.is_active ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'}`}>
                {student.is_active ? 'Activo' : 'Inactivo'}
              </span>
            </div>
          </div>
          <div className="md:col-span-2 space-y-1">
            <span className="text-[10px] uppercase tracking-widest text-muted">Ubicación de Entrenamiento</span>
            <p className="text-sm text-white/90 italic">{student.address || 'Sin dirección registrada'}</p>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] uppercase tracking-widest text-muted">En la Legión desde</span>
            <p className="text-sm text-gold/80">{formatDate(student.enrollment_date)}</p>
          </div>
        </div>
      </div>

      {/* 3. HISTORIAL DE PAGOS (TABLA PREMIUM) */}
      <div className="rounded-xl bg-card/20 backdrop-blur-sm border border-border overflow-hidden">
        <div className="bg-white/5 px-6 py-4 border-b border-border">
          <h2 className="text-[10px] font-legion uppercase tracking-[0.3em] text-muted">
            Historial de Operaciones
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-black/20">
                <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-widest text-muted">Monto</th>
                <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-widest text-muted">Estado</th>
                <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-widest text-muted">Fecha Pago</th>
                <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-widest text-muted">Vencimiento</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {payments.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center text-xs text-muted italic uppercase tracking-widest">
                    No se registran transacciones para este guerrero.
                  </td>
                </tr>
              ) : (
                payments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-6 py-4 text-sm font-bold text-white">${payment.amount}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center rounded px-2 py-0.5 text-[9px] font-bold uppercase tracking-tighter ${getStatusClasses(payment.status)}`}>
                        {getStatusLabel(payment.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-white/70">{formatDate(payment.payment_date)}</td>
                    <td className="px-6 py-4 text-xs font-medium text-gold/60">{formatDate(payment.due_date)}</td>
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