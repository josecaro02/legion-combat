import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="border-b border-border">
      <div className="mx-9 flex h-16 max-w-7xl items-center justify-between px-6">
        <Link
          to="/dashboard"
          className="font-legion font-bold uppercase tracking-widest text-xl bg-gradient-to-r from-yellow-500 via-yellow-300 to-yellow-600 bg-clip-text text-transparent drop-shadow-[0_0_6px_rgba(212,175,55,0.6)] hover:brightness-125 transition duration-300"
        >
          Legión Combat
        </Link>

        <div className="flex items-center gap-4">
          {user && (
            <>
              <div className="flex items-center gap-2 rounded-lg bg-card px-3 py-1 text-sm">
                <span className="text-gray-300">{user.email}</span>
                <span className="rounded bg-card border border-gold px-2 py-0.5 text-xs text-gold">
                  {user.role}
                </span>
              </div>

              <button
                onClick={handleLogout}
                className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-400 hover:bg-red-500/20 transition"
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
