import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { hasPermission } from '../utils/permissions';
import { getStudents, createStudent, searchStudents } from '../api/students.api';
import CameraCapture from '../components/CameraCapture';
import { uploadStudentPhoto, isCloudinaryConfigured } from '../utils/cloudinary';

/**
 * Students Component
 *
 * Muestra lista de estudiantes con funcionalidad de búsqueda en tiempo real.
 * Incluye debounce para optimizar las llamadas a la API.
 * Ahora con captura de foto y contacto de emergencia.
 */
function Students() {
  const navigate = useNavigate();
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
    emergency_contact_name: '',
    emergency_contact_phone: '',
    photo_url: '',
  });
  const [formError, setFormError] = useState(null);
  const [formSuccess, setFormSuccess] = useState(false);

  // Estados para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);

  // Estados para la foto
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [showCamera, setShowCamera] = useState(false);

  const canView = hasPermission(user, 'canViewStudents');
  const canCreate = hasPermission(user, 'canCreateStudent');

  // Verificar si Cloudinary está configurado
  const cloudinaryReady = isCloudinaryConfigured();

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

  /**
   * Handle photo capture from camera
   */
  async function handlePhotoCapture(file) {
    setCapturedPhoto(file);
    setShowCamera(false);
    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(false);

    try {
      const result = await uploadStudentPhoto(file);
      setFormData(prev => ({ ...prev, photo_url: result.secure_url }));
      setUploadSuccess(true);
      setFormError(null)
    } catch (err) {
      console.error('Upload error:', err);
      setUploadError(err.message || 'Error al subir la imagen. Intenta de nuevo.');
      // Limpiar la foto capturada si falla la subida
      setCapturedPhoto(null);
    } finally {
      setIsUploading(false);
    }
  }

  /**
   * Handle camera error
   */
  function handleCameraError(errorMessage) {
    setUploadError(errorMessage);
  }

  /**
   * Remove captured photo
   */
  function removePhoto() {
    setCapturedPhoto(null);
    setFormData(prev => ({ ...prev, photo_url: '' }));
    setUploadSuccess(false);
    setUploadError(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canCreate) return;

    
    if (!formData.photo_url) {
      setFormError('La foto del estudiante es obligatoria');
      return;
    }
    
    if (!formData.emergency_contact_name.trim() || !formData.emergency_contact_phone.trim()) {
      setFormError('El contacto de emergencia es requerido (nombre y teléfono)');
      return;
    }

    try {
      setFormError(null);
      setFormSuccess(false);
      await createStudent(token, formData);
      setFormSuccess(true);
      // Reset form
      setFormData({
        first_name: '',
        last_name: '',
        course: 'boxing',
        phone: '',
        address: '',
        emergency_contact_name: '',
        emergency_contact_phone: '',
        photo_url: '',
      });
      setCapturedPhoto(null);
      setUploadSuccess(false);
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
   * Navega al detalle del estudiante
   */
  function handleStudentClick(studentId) {
    navigate(`/students/${studentId}`);
  }

  /**
   * Limpia el campo de búsqueda y vuelve a la lista original
   */
  function clearSearch() {
    setSearchTerm('');
    setSearchResults(null);
    setSearchError(null);
  }

  /* Si hay resultados de búsqueda, los muestra; si no, muestra la lista original */
  const displayedStudents = searchResults !== null ? searchResults : students;
  const isSearching = searchTerm.trim().length >= 2;

  // Mostrar foto del estudiante (de la lista o placeholder)
  function getStudentPhotoUrl(student) {
    if (student.photo_url) {
      return student.photo_url;
    }
    // Placeholder con iniciales
    return null;
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
      <div className="rounded-xl border border-red-500 bg-red-900/20 p-4 text-red-300">
        No tienes permiso para ver estudiantes.
      </div>
    );
  }

  return (
    <div className="space-y-8 text-white relative">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-legion font-bold tracking-widest text-white flex items-center gap-3">
            <span className="text-gold">🥊</span> ESTUDIANTES
          </h1>
          <p className="text-muted text-sm mt-1 uppercase tracking-tighter">Administración de la Legión</p>
        </div>
        {canCreate && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="rounded-md bg-gold px-6 py-2 text-xs font-legion font-bold uppercase tracking-widest text-black hover:bg-goldLight transition duration-300 shadow-[0_0_15px_rgba(196,164,124,0.3)]"
          >
            {showForm ? 'Cancelar' : 'Nuevo Estudiante'}
          </button>
        )}
      </div>

      {/* Barra de búsqueda */}
      {canView && (
        <div className="mb-4 relative group">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
            <svg
              className="h-5 w-5 text-gold/50 group-focus-within:text-gold transition-colors"
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
            placeholder="BUSCAR GUERRERO..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="w-full rounded-xl border border-border bg-card/40 backdrop-blur-md py-3 pl-12 pr-12 text-gold placeholder-gray-600 focus:border-gold/50 focus:outline-none transition-all"
          />
          {searchTerm && (
            <button
              onClick={clearSearch}
              className="absolute inset-y-0 right-0 flex items-center pr-4 text-gray-500 hover:text-gold"
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

          {/* Estados de búsqueda actualizados al diseño premium */}
          <div className="absolute left-0 -bottom-6 flex w-full justify-between px-2">
            {searchLoading && (
              <div className="text-[10px] uppercase tracking-widest text-gold/70 animate-pulse">
                Buscando...
              </div>
            )}

            {searchError && (
              <div className="text-[10px] uppercase tracking-widest text-red-400">
                {searchError}
              </div>
            )}

            {isSearching && !searchLoading && searchResults?.length === 0 && (
              <div className="text-[10px] uppercase tracking-widest text-muted">
                No se encontraron resultados para "<span className="text-white">{searchTerm}</span>"
              </div>
            )}

            {searchResults?.length > 0 && (
              <div className="text-[10px] uppercase tracking-widest text-muted">
                <span className="text-gold font-bold">{searchResults.length}</span> resultado{searchResults.length !== 1 ? 's' : ''} encontrado{searchResults.length !== 1 ? 's' : ''}
              </div>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-xl border border-red-500 bg-red-900/20 p-4 text-red-300">
          {error}
        </div>
      )}

      {showForm && canCreate && (
        <div className="mb-6 rounded-xl bg-card/80 backdrop-blur-md border border-border p-6 shadow-soft animate-in fade-in slide-in-from-top-4 duration-300">
          <h2 className="mb-6 text-sm font-legion uppercase tracking-widest text-gold">
            Registrar Nuevo Ingreso
          </h2>

          {formError && (
            <div className="mb-4 rounded bg-red-800/40 p-3 text-red-300 text-sm">
              {formError}
            </div>
          )}

          {formSuccess && (
            <div className="mb-4 rounded bg-green-800/40 p-4 text-green-300 text-sm">
              Estudiante creado correctamente.
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Sección: Foto del Estudiante */}
            <div className="border-b border-border/50 pb-6">
              <h3 className="text-[10px] uppercase tracking-widest text-gold/80 mb-4">
                Foto del Guerrero
              </h3>

              {!cloudinaryReady && (
                <div className="mb-4 rounded-lg border border-yellow-500/50 bg-yellow-900/20 p-3 text-yellow-300 text-xs">
                  <div className="flex items-center gap-2">
                    <svg className="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span>Servicio de fotos no configurado. Contacta al administrador.</span>
                  </div>
                </div>
              )}

              {showCamera && cloudinaryReady && (
                <div className="mb-4">
                  <CameraCapture
                    onCapture={handlePhotoCapture}
                    onError={handleCameraError}
                    className="mb-4"
                  />
                </div>
              )}

              {!showCamera && !capturedPhoto && (
                <div className="flex items-center gap-4">
                  <button
                    type="button"
                    onClick={() => setShowCamera(true)}
                    disabled={!cloudinaryReady}
                    className="flex items-center gap-2 rounded-lg border border-gold/50 bg-gold/10 px-4 py-3 text-sm text-gold hover:bg-gold/20 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Capturar Foto
                  </button>
                  <span className="text-xs text-muted">
                    * La foto es obligatoria
                  </span>
                </div>
              )}

              {/* Preview de foto capturada */}
              {capturedPhoto && (
                <div className="relative inline-block">
                  <div className="w-32 h-32 rounded-xl overflow-hidden border-2 border-gold/50">
                    <img
                      src={URL.createObjectURL(capturedPhoto)}
                      alt="Foto capturada"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={removePhoto}
                    className="absolute -top-2 -right-2 rounded-full bg-red-500 text-white p-1 hover:bg-red-600 transition"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Estados de upload */}
              {isUploading && (
                <div className="mt-4 flex items-center gap-2 text-sm text-gold">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Subiendo imagen...
                </div>
              )}

              {uploadSuccess && (
                <div className="mt-4 flex items-center gap-2 text-sm text-green-400">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Imagen subida correctamente
                </div>
              )}

              {uploadError && (
                <div className="mt-4 rounded bg-red-800/40 p-3 text-red-300 text-sm">
                  {uploadError}
                </div>
              )}
            </div>

            {/* Sección: Datos Personales */}
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">
                  Nombre *
                </label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-white focus:border-gold/50 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">
                  Apellido *
                </label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-white focus:border-gold/50 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">
                  Teléfono
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  required
                  minLength={10}
                  pattern="\d{10,}"
                  title="Debe contener al menos 10 dígitos"
                  className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-white focus:border-gold/50 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">
                  Dirección
                </label>
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-white focus:border-gold/50 focus:outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">
                  Curso *
                </label>
                <select
                  name="course"
                  value={formData.course}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-white text-center focus:border-gold/50 focus:outline-none"
                >
                  <option value="boxing" className="bg-[#1a1a1a]">BOXEO</option>
                  <option value="kickboxing" className="bg-[#1a1a1a]">KICKBOXING</option>
                  <option value="boxing_school" className="bg-[#1a1a1a]">BOXING SCHOOL</option>
                </select>
              </div>
            </div>

            {/* Sección: Contacto de Emergencia */}
            <div className="border-t border-border/50 pt-6">
              <h3 className="text-[10px] uppercase tracking-widest text-gold/80 mb-4">
                Contacto de Emergencia *
              </h3>
              <div className="grid gap-6 md:grid-cols-2">
                <div>
                  <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">
                    Nombre Contacto *
                  </label>
                  <input
                    type="text"
                    name="emergency_contact_name"
                    value={formData.emergency_contact_name}
                    onChange={handleInputChange}
                    required
                    placeholder="Ej: María Pérez (Madre)"
                    className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-white focus:border-gold/50 focus:outline-none placeholder:text-gray-600"
                  />
                </div>

                <div>
                  <label className="text-[10px] uppercase tracking-widest text-muted mb-2 block ml-1">
                    Teléfono Contacto *
                  </label>
                  <input
                    type="tel"
                    name="emergency_contact_phone"
                    value={formData.emergency_contact_phone}
                    onChange={handleInputChange}
                    required
                    minLength={10}
                    pattern="\d{10,}"
                    title="Debe contener al menos 10 dígitos"
                    placeholder="Ej: 3123456789"
                    className="w-full rounded-lg bg-bgInput border border-border px-3 py-2.5 text-white focus:border-gold/50 focus:outline-none placeholder:text-gray-600"
                  />
                </div>
              </div>
            </div>

            <div className="md:col-span-2 flex justify-end">
              <button
                type="submit"
                disabled={isUploading}
                className="w-full md:w-auto min-w-[200px] rounded-md bg-white py-3 px-8 text-xs font-bold uppercase tracking-widest text-black hover:bg-gold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? 'Subiendo foto...' : 'Guardar'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="rounded-xl bg-card/40 backdrop-blur-sm border border-border shadow-soft overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border bg-white/5">
                <th className="px-4 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted w-16">
                  Foto
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted">
                  Nombre
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted">
                  Apellido
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted">
                  Curso
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted">
                  Contacto Emergencia
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-legion uppercase tracking-[0.2em] text-muted">
                  Estado
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {displayedStudents.length === 0 ? (
                <tr>
                  <td
                    colSpan="6"
                    className="px-6 py-8 text-center text-sm text-muted"
                  >
                    {isSearching
                      ? `No se encontraron resultados para "${searchTerm}"`
                      : 'No hay estudiantes registrados.'}
                  </td>
                </tr>
              ) : (
                displayedStudents.map(student => (
                  <tr
                    key={student.id}
                    onClick={() => handleStudentClick(student.id)}
                    className="cursor-pointer hover:bg-white/[0.02] transition-colors group"
                  >
                    {/* Foto del estudiante */}
                    <td className="px-4 py-3">
                      <div className="w-10 h-10 rounded-full overflow-hidden bg-card border border-border flex items-center justify-center">
                        {student.photo_url ? (
                          <img
                            src={student.photo_url}
                            alt={`${student.first_name} ${student.last_name}`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.parentElement.innerHTML = `<span class="text-xs text-gold font-bold">${student.first_name.charAt(0)}</span>`;
                            }}
                          />
                        ) : (
                          <span className="text-xs text-gold font-bold">
                            {student.first_name ? student.first_name.charAt(0).toUpperCase() : '?'}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-white/90 group-hover:text-gold transition-colors">
                      {student.first_name}
                    </td>
                    <td className="px-6 py-4 text-sm text-white/80 group-hover:text-gold transition-colors">
                      {student.last_name}
                    </td>
                    <td className="px-6 py-4 text-xs text-muted uppercase tracking-tighter">
                      {student.course}
                    </td>
                    <td className="px-6 py-4 text-xs text-white/70">
                      {student.emergency_contact_name || '-'}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                        student.is_active
                        ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                        : 'bg-red-500/10 text-red-400 border border-red-500/20'
                      }`}>
                        {student.is_active ? 'Activo' : 'Inactivo'}
                      </span>
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
