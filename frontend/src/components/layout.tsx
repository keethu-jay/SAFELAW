import {Outlet, Link} from 'react-router-dom';

const layout = () => (
    <div className="flex flex-col min-h-screen bg-gray-50">
        <header className="h-16 flex items-center justify-between bg-indigo-700 px-8 text-white shadow">
            <span className="text-lg font-bold">My App</span>
            <nav className="space-x-4">
                <Link to="/" className="hover:underline">Home</Link>
                <Link to="/writer" className="hover:underline">Writer</Link>
                <Link to="/reader" className="hover:underline">Reader</Link>
                <Link to="/profile" className="hover:underline">Profile</Link>
                <Link to="/login" className="hover:underline">Login</Link>
            </nav>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 container mx-auto p-8">
            <Outlet />
        </main>

        {/* Footer */}
        <footer className="h-12 flex items-center justify-center bg-gray-200 text-gray-600 mt-auto">
            © 2025 My App. All rights reserved.
        </footer>

    </div>

);

export default layout;