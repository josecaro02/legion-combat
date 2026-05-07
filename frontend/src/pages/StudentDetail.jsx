import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { hasPermission } from '../utils/permissions';
import { getStudent } from '../api/students.api';
import { getStudentPayments } from '../api/payments.api';

/**
 * StudentDetail Component
 * Rediseñado con estética Premium Oscura
 * Ahora incluye foto y contacto de emergencia
 */
function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, token } = useAuth();

  const [student, setStudent] = useState(null);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [imageError, setImageError] = useState(false);

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
      setImageError(false);
      const [studentData, paymentsData] = await Promise.all([
        getStudent(id),
        getStudentPayments(id),
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

  /**
   * Handle image load error - fallback to initials
   */
  function handleImageError() {
    setImageError(true);
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
          <div className="flex items-center gap-4">
            {/* Foto del estudiante con fallback */}
            <div className="w-16 h-16 md:w-20 md:h-20 rounded-xl overflow-hidden bg-card border-2 border-gold/30 flex-shrink-0">
              {!imageError && student.photo_url ? (
                <img
                  src={student.photo_url}
                  alt={`${student.first_name} ${student.last_name}`}
                  className="w-full h-full object-cover"
                  onError={handleImageError}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gold/10">
                  <span className="text-2xl md:text-3xl text-gold font-bold">
                    {student.first_name && student.last_name
                      ? `${student.first_name.charAt(0)}${student.last_name.charAt(0)}`
                      : '?'}
                  </span>
                </div>
              )}
            </div>

            <div>
              <h1 className="text-3xl md:text-4xl font-legion font-bold tracking-tighter text-white uppercase italic">
                {student.first_name} <span className="text-gold">{student.last_name}</span>
              </h1>
              <p className="text-muted text-sm mt-1">
                {student.course === 'boxing' && 'Boxeador'}
                {student.course === 'kickboxing' && 'Kickboxer'}
                {student.course === 'both' && 'Artista Marcial'}
                {' '}de la Legión
              </p>
            </div>
          </div>

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

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Columna 1: Información Personal */}
          <div className="space-y-4">
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
          </div>

          {/* Columna 2: Ubicación */}
          <div className="space-y-4">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-muted">Ubicación de Entrenamiento</span>
              <p className="text-sm text-white/90 italic">{student.address || 'Sin dirección registrada'}</p>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-muted">En la Legión desde</span>
              <p className="text-sm text-gold/80">{formatDate(student.enrollment_date)}</p>
            </div>
          </div>

          {/* Columna 3: Contacto de Emergencia - Destacado */}
          <div className="space-y-4 p-4 rounded-lg bg-gold/5 border border-gold/20">
            <div className="flex items-center gap-2 text-gold">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span className="text-[10px] uppercase tracking-widest font-bold">Contacto de Emergencia</span>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-muted">Nombre</span>
              <p className="text-sm font-medium text-white">
                {student.emergency_contact_name || 'No registrado'}
              </p>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-muted">Teléfono</span>
              <p className="text-lg font-bold text-gold">
                {student.emergency_contact_phone || 'N/A'}
              </p>
            </div>
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
