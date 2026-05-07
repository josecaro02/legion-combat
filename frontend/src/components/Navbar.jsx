import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="border-b border-border bg-bg/95 backdrop-blur-sm sticky top-0 z-50">
      {/* 1. Ajuste de márgenes: mx-auto es mejor que mx-9 para centrar */}
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
        <Link
          to="/dashboard"
          className="font-legion font-bold uppercase tracking-widest text-lg md:text-xl bg-gradient-to-r from-yellow-500 via-yellow-300 to-yellow-600 bg-clip-text text-transparent drop-shadow-[0_0_6px_rgba(212,175,55,0.6)] shrink-0"
        >
          Legion Combat
        </Link>

        <div className="flex items-center gap-2 sm:gap-4">
          {user && (
            <>
              {/* 2. Contenedor de usuario responsivo */}
              <div className="flex items-center gap-2 rounded-lg bg-card/50 border border-border/40 px-2 sm:px-3 py-1 text-sm">
                {/* Ocultamos el email en móviles muy pequeños o lo truncamos */}
                <span className="hidden md:inline text-gray-300">
                  {user.email}
                </span>
                
                {/* El Rol siempre visible pero con texto más pequeño en móvil */}
                <span className="rounded border border-gold/50 px-1.5 py-0.5 text-[10px] sm:text-xs text-gold uppercase font-bold tracking-tighter sm:tracking-normal">
                  {user.role}
                </span>
              </div>

              {/* 3. Botón de salir ajustado */}
              <button
                onClick={handleLogout}
                className="rounded-md bg-red-500/10 px-3 py-1.5 sm:py-2 text-xs sm:text-sm text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors"
              >
                Salir
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;