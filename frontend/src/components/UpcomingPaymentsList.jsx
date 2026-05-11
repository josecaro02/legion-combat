import { useState, useMemo } from 'react';

/**
 * UpcomingPaymentsList - Displays a list of students with upcoming payments
 *
 * Shows student name, phone, course, last payment date, and due date.
 * Supports toggling sort order by due_soon_date (ASC/DESC).
 */
function UpcomingPaymentsList({ items }) {
  const [sortAsc, setSortAsc] = useState(true);

  const sorted = useMemo(() => {
    return [...items].sort((a, b) => {
      const dateA = new Date(a.due_soon_date);
      const dateB = new Date(b.due_soon_date);
      return sortAsc ? dateA - dateB : dateB - dateA;
    });
  }, [items, sortAsc]);

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const courseLabel = (course) => {
    const labels = {
      boxing: 'Boxeo',
      kickboxing: 'Kickboxing',
      boxing_school: 'Boxing School',
    };
    return labels[course] || course;
  };

  return (
    <div className="mt-4 rounded-lg bg-white shadow">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-sm font-semibold text-gray-700">
          Pagos próximos a vencer
        </h3>
        <button
          onClick={() => setSortAsc((prev) => !prev)}
          className="rounded border border-gray-300 px-3 py-1 text-xs text-gray-600 hover:bg-gray-50"
        >
          {sortAsc ? 'Próximo primero ↑' : 'Lejano primero ↓'}
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Estudiante
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Teléfono
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Curso
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Último pago
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Vence pronto
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sorted.length === 0 ? (
              <tr>
                <td
                  colSpan="5"
                  className="px-4 py-8 text-center text-gray-500"
                >
                  No hay pagos próximos
                </td>
              </tr>
            ) : (
              sorted.map((p) => (
                <tr key={p.student_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {p.student.first_name} {p.student.last_name}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {p.student.phone || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {courseLabel(p.student.course)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {formatDate(p.last_payment_date)}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className="rounded-full bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-800">
                      {formatDate(p.due_soon_date)}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default UpcomingPaymentsList;