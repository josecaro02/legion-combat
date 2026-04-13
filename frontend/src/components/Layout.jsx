import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";

function Layout() {
  return (
    <div className="relative min-h-screen bg-bg text-gray-100 overflow-hidden">
      {/* TEXTURA GLOBAL */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.5] mix-blend-screen"
        style={{
          backgroundImage: "url('/noise.png')",
        }}
      />

      <div className="relative z-10">
        <Navbar />
        <main className="mx-auto max-w-7xl px-6 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default Layout;
