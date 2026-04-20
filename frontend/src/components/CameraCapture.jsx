import { useState, useRef, useCallback, useEffect } from "react";

/**
 * CameraCapture Component
 *
 * Captures photos using navigator.mediaDevices.getUserMedia
 * Features: Camera preview, capture, retake, permission error handling
 *
 * @param {Object} props
 * @param {Function} props.onCapture - Called with captured image Blob when photo is taken
 * @param {Function} props.onError - Called when camera error occurs
 * @param {string} [props.className] - Additional CSS classes
 */
function CameraCapture({ onCapture, onError, className = "" }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Start camera stream
   */
  /* comentaraio funcion start camera --------------------------
  const startCamera = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Check if getUserMedia is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Tu navegador no soporta acceso a la cámara');
      }

      // Request camera access - prefer front-facing camera
      const constraints = {
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsStreaming(true);
      }
    } catch (err) {
      console.error('Camera error:', err);
      let errorMessage = 'Error al acceder a la cámara';

      // Handle specific permission errors
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = 'Permiso de cámara denegado. Por favor permite el acceso en la configuración de tu navegador.';
      } else if (err.name === 'NotFoundError') {
        errorMessage = 'No se encontró una cámara disponible.';
      } else if (err.name === 'NotReadableError') {
        errorMessage = 'La cámara está siendo usada por otra aplicación.';
      }

      setError(errorMessage);
      if (onError) onError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [onError]);
    comentario funcion start camera ------------------------------
 */

  const startCamera = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Tu navegador no soporta acceso a la cámara");
      }

      const constraints = {
        video: {
          facingMode: "user",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      setIsStreaming(true); // Primero activamos el estado para que aparezca el <video>
    } catch (err) {
      setError("Error al acceder a la cámara");
      if (onError) onError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [onError]);

  useEffect(() => {
    if (isStreaming && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [isStreaming]);


  // nuevo camviooos ---------------------------
  /**
   * Stop camera stream
   */
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  /**
   * Capture photo from video stream
   */
  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to blob with compression
    canvas.toBlob(
      (blob) => {
        if (blob) {
          // Create a File object from the blob
          const file = new File([blob], `student-photo-${Date.now()}.jpg`, {
            type: "image/jpeg",
            lastModified: Date.now(),
          });

          setCapturedImage(URL.createObjectURL(blob));
          stopCamera();

          if (onCapture) {
            onCapture(file);
          }
        }
      },
      "image/jpeg",
      0.85, // Quality: 85% for good balance between quality and size
    );
  }, [onCapture, stopCamera]);

  /**
   * Retake photo - restart camera
   */
  const retakePhoto = useCallback(() => {
    setCapturedImage(null);
    startCamera();
  }, [startCamera]);

  /**
   * Cleanup on unmount
   */
  const cleanup = useCallback(() => {
    stopCamera();
    if (capturedImage) {
      URL.revokeObjectURL(capturedImage);
    }
  }, [stopCamera, capturedImage]);

  // Expose cleanup for parent component
  /*
  -------------------------- cambios viejos
  useState(() => {
    return cleanup;
  });
  -----------------------------cambios viejos

  /*
  ---------------------------------- cambios nuevos
*/
  useEffect(() => {
    return () => {
      stopCamera();
      if (capturedImage) {
        URL.revokeObjectURL(capturedImage);
      }
    };
  }, [stopCamera, capturedImage]);

  /*-------------------------------------- cambios nuevos

  */
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Hidden canvas for image processing */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Error Message */}
      {error && (
        <div className="rounded-lg border border-red-500/50 bg-red-900/20 p-4 text-red-300 text-sm">
          <div className="flex items-center gap-2">
            <svg
              className="h-5 w-5 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{error}</span>
          </div>
          <button
            onClick={() => {
              setError(null);
              startCamera();
            }}
            className="mt-2 text-xs text-gold hover:text-goldLight underline"
          >
            Intentar de nuevo
          </button>
        </div>
      )}

      {/* Camera Preview or Captured Image */}
      <div className="relative aspect-video w-full max-w-md mx-auto overflow-hidden rounded-xl border-2 border-dashed border-border bg-card/50">
        {!isStreaming && !capturedImage && !error && (
          <div className="flex h-full flex-col items-center justify-center gap-4 p-6 text-center">
            <div className="rounded-full bg-gold/10 p-4">
              <svg
                className="h-8 w-8 text-gold"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-white">
                Capturar Foto del Estudiante
              </p>
              <p className="mt-1 text-xs text-muted">
                Se requiere acceso a la cámara
              </p>
            </div>
            <button
              onClick={startCamera}
              disabled={isLoading}
              className="rounded-md bg-gold px-6 py-2 text-xs font-bold uppercase tracking-widest text-black hover:bg-goldLight transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Iniciando..." : "Iniciar Cámara"}
            </button>
          </div>
        )}

        {isStreaming && (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="h-full w-full object-cover"
            />
            {/* Camera overlay indicators */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute top-4 left-4 right-4 flex justify-between text-[10px] uppercase tracking-widest text-white/70">
                <span className="bg-black/50 px-2 py-1 rounded">En vivo</span>
              </div>
              {/* Corner markers */}
              <div className="absolute top-4 left-4 w-6 h-6 border-l-2 border-t-2 border-gold" />
              <div className="absolute top-4 right-4 w-6 h-6 border-r-2 border-t-2 border-gold" />
              <div className="absolute bottom-4 left-4 w-6 h-6 border-l-2 border-b-2 border-gold" />
              <div className="absolute bottom-4 right-4 w-6 h-6 border-r-2 border-b-2 border-gold" />
            </div>
          </>
        )}

        {capturedImage && (
          <img
            src={capturedImage}
            alt="Foto capturada"
            className="h-full w-full object-cover"
          />
        )}
      </div>

      {/* Controls */}
      {isStreaming && (
        <div className="flex justify-center gap-4">
          <button
            onClick={capturePhoto}
            className="flex items-center gap-2 rounded-full bg-gold px-6 py-3 text-xs font-bold uppercase tracking-widest text-black hover:bg-goldLight transition duration-300 shadow-[0_0_15px_rgba(196,164,124,0.3)]"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            Capturar
          </button>
          <button
            onClick={stopCamera}
            className="rounded-full border border-border bg-card/50 px-6 py-3 text-xs font-bold uppercase tracking-widest text-muted hover:text-white hover:border-gold/50 transition duration-300"
          >
            Cancelar
          </button>
        </div>
      )}

      {capturedImage && (
        <div className="flex justify-center gap-4">
          <button
            onClick={retakePhoto}
            className="flex items-center gap-2 rounded-full border border-gold bg-transparent px-6 py-3 text-xs font-bold uppercase tracking-widest text-gold hover:bg-gold/10 transition duration-300"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Tomar otra
          </button>
        </div>
      )}
    </div>
  );
}

export default CameraCapture;
