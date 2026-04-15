import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { login as loginApi } from "../api/auth";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { token, user } = await loginApi(email, password);
      console.log(token, user);
      login(token, user);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4 bg-bg relative overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.5] mix-blend-screen"
        style={{ backgroundImage: "url('/noise.png')" }}
      />

      <div className="flex flex-col md:flex-row items-center justify-center gap-12 w-full max-w-5xl z-10">
        <div className="flex justify-self-start md:w-1/2">
          <img
            src="logo.png"
            alt="Legion Combat Logo"
            className="w-64 md:w-80 lg:w-[400px] h-auto object-contain drop-shadow-[0_0_30px_rgba(196,164,124,0.2)]"
          />
        </div>

        <div className="w-full sm:w-[400px] rounded-xl border border-border bg-card/80 backdrop-blur-md p-8 shadow-2xl">
          <h1 className="mb-8 text-center text-2xl font-legion tracking-widest uppercase text-gold">
            Iniciar Sesión
          </h1>

          {error && (
            <div className="mb-4 rounded-lg bg-red-500/10 p-3 text-sm text-red-400 border border-red-500/20">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="mb-2 block text-xs uppercase tracking-wider text-muted ml-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-border bg-bgInput px-3 py-2.5 text-gold placeholder-gray-600 focus:border-gold/50 focus:outline-none transition-all autofill:shadow-[inset_0_0_0px_1000px_#121212] autofill:[-webkit-text-fill-color:#c4a47c]"
                placeholder="usuario@ejemplo.com"
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-xs uppercase tracking-wider text-muted ml-1">
                Contraseña
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-border bg-bgInput px-3 py-2.5 text-gold placeholder-gray-600 focus:border-gold/50 focus:outline-none transition-all autofill:shadow-[inset_0_0_0px_1000px_#121212] autofill:[-webkit-text-fill-color:#c4a47c]"
                placeholder="********"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="font-legion w-full uppercase tracking-[0.2em] px-6 py-3 border border-gold text-gold rounded-md hover:bg-gold hover:text-black transition-all duration-300 active:scale-[0.98] disabled:opacity-50"
            >
              {loading ? "Cargando..." : "Ingresar"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
export default Login;
