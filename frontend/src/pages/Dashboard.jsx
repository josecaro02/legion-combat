import { useState, useEffect } from "react";
import { useAuth } from "../auth/AuthContext";
import { useNavigate } from "react-router-dom";
import { hasPermission } from "../utils/permissions";
import { authGet } from "../api/client";
import { getUpcomingPayments } from "../api/students.api";
import UpcomingPaymentsList from "../components/UpcomingPaymentsList";

function Dashboard() {
  const { user, token } = useAuth();
  const navigate = useNavigate();

  const canViewStudents = hasPermission(user, "canViewStudents");
  const canViewPayments = hasPermission(user, "canViewPayments");
  const canViewReports = hasPermission(user, "canViewReports");

  const [students, setStudents] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [upcomingData, setUpcomingData] = useState(null);
  const [upcomingLoading, setUpcomingLoading] = useState(false);
  const [upcomingError, setUpcomingError] = useState(null);
  const [upcomingShowList, setUpcomingShowList] = useState(false);

  useEffect(() => {
    async function fetchDashboardData() {
      if (!token) return;

      setLoading(true);
      setError(null);

      try {
        if (canViewStudents) {
          const studentsData = await authGet("/students/", token);
          setStudents(studentsData.items || studentsData || []);
        }

        if (canViewPayments) {
          const paymentsData = await authGet("/payments/", token);
          setPayments(paymentsData.items || paymentsData || []);
        }
      } catch (err) {
        setError(err.message || "Error al cargar los datos");
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, [token, canViewStudents, canViewPayments]);

  const totalStudents = students.length;
  const totalPayments = payments.length;

  const getLastPaymentDate = () => {
    if (!payments || payments.length === 0) return null;
    const paidPayments = payments.filter((p) => p.payment_date);
    if (paidPayments.length === 0) return null;

    const sorted = paidPayments.sort(
      (a, b) => new Date(b.payment_date) - new Date(a.payment_date),
    );

    return sorted[0].payment_date;
  };

  const lastPaymentDate = getLastPaymentDate();

  async function handleUpcomingPayments() {
    if (!token) return;
    setUpcomingLoading(true);
    setUpcomingError(null);
    try {
      const result = await getUpcomingPayments(token, 30);
      setUpcomingData(result);
      setUpcomingShowList(true);
    } catch (err) {
      setUpcomingError(err.message || "Error al cargar próximos pagos");
    } finally {
      setUpcomingLoading(false);
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return "Sin registros";
    const date = new Date(dateString);
    return date.toLocaleDateString("es-CL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bg text-text p-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="flex h-64 items-center justify-center">
          <p className="text-muted">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen text-text p-6 overflow-hidden">
      <div className="relative z-10">
        <h1 className="mb-2 text-3xl font-semibold">Dashboard</h1>

        <p className="mb-8 text-muted">
          Bienvenido,{" "}
          <span className="text-white font-semibold">{user?.email}</span>{" "}
          <span className="border border-border px-2 py-1 text-xs rounded-full">
            {user?.role}
          </span>
        </p>

        {error && (
          <div className="mb-6 rounded-md border border-red-700 bg-red-900/20 p-4 text-red-400">
            {error}
          </div>
        )}

        <div className="grid  gap-6 md:grid-cols-2">
          <section className="mb-8">
            <h2 className="font-legion uppercase tracking-wide text-sm text-muted mb-3">
              Estudiantes
            </h2>
            <div className="bg-card/80 backdrop-blur-sm border border-border rounded-md p-5 shadow-soft flex justify-between">
              <div>
                <p className="text-md text-muted mb-2">Total Estudiantes</p>
                <p className="text-2xl font-semibold text-white">
                  {totalStudents > 0 ? totalStudents : "--"}
                </p>
              </div>

              <button
                onClick={() => navigate("/students")}
                className="text-lg text-gold hover:text-goldLight transition hover:scale-125 transition-transform duration-300"
              >
                Ver →
              </button>
            </div>
          </section>

          {canViewPayments && (
            <section className="mb-8">
              <h2 className="font-legion uppercase tracking-wide text-sm text-muted mb-3">
                Pagos
              </h2>

              <div className="bg-card/80 backdrop-blur-sm border border-border rounded-md p-5 shadow-soft relative">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-md text-muted mb-2 tracking-wider">
                      Total Pagos
                    </p>
                    <p className="text-2xl font-bold text-white">
                      {totalPayments > 0 ? totalPayments : "0"}
                    </p>
                  </div>

                  <div className="w-[1px] h-12 bg-border mx-6" />

                  <div className="flex-[1.5]">
                    <p className="text-md text-muted mb-2 tracking-wider">
                      Último Pago
                    </p>
                    <p className="text-2xl font-semibold text-gold tracking-tight">
                      {lastPaymentDate ? formatDate(lastPaymentDate) : "--"}
                    </p>
                  </div>
                  <button
                    onClick={() => navigate("/payments")}
                    className="text-lg text-gold hover:text-goldLight transition hover:scale-125 transition-transform duration-300"
                  >
                    Ver →
                  </button>
                </div>
              </div>
            </section>
          )}
        </div>
        {hasPermission(user, "canCreatePayment") && (
          <section className="mb-8">
            <h2 className="font-legion uppercase tracking-wide text-sm text-muted mb-3">
              Registrar Pago
            </h2>

            <div className="bg-card/80 backdrop-blur-sm border border-border rounded-md p-6 shadow-soft">
              <p className="mb-4 text-muted">
                Registra un nuevo pago para un estudiante.
              </p>

              <button className="font-legion uppercase tracking-wide px-6 py-2 border border-gold text-gold rounded-sm hover:bg-gold hover:text-black transition duration-200">
                Registrar Pago
              </button>
            </div>
          </section>
        )}

        {canViewPayments && (
          <section className="mb-8">
            <h2 className="font-legion uppercase tracking-wide text-sm text-muted mb-3">
              Próximos Pagos
            </h2>

            <div className="mb-4">
              <button
                onClick={handleUpcomingPayments}
                disabled={upcomingLoading}
                className="text-sm text-muted hover:text-gold transition disabled:text-gray-600"
              >
                {upcomingLoading ? "Cargando..." : "Ver →"}
              </button>
            </div>

            {upcomingLoading && <p className="text-muted">Cargando...</p>}
            {upcomingError && <p className="text-red-400">{upcomingError}</p>}

            {upcomingShowList && upcomingData && (
              <UpcomingPaymentsList items={upcomingData.items} />
            )}
          </section>
        )}

        <section>
          <h2 className="font-legion uppercase tracking-wide text-sm text-muted mb-3">
            Acciones Rápidas
          </h2>

          <div className="flex gap-6">
            <button className="text-sm text-muted hover:text-gold transition">
              Buscar Estudiante
            </button>

            {canViewReports && (
              <button className="text-sm text-muted hover:text-gold transition">
                Generar Reporte
              </button>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default Dashboard;
