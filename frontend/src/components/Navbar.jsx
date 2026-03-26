import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="bg-white shadow">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <Link to="/dashboard" className="text-xl font-bold text-gray-800">
            Legión Combat
          </Link>
          <div className="flex gap-4">
            <Link
              to="/dashboard"
              className="rounded-md px-3 py-2 text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            >
              Dashboard
            </Link>
            <Link
              to="/login"
              className="rounded-md px-3 py-2 text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            >
              Login
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
