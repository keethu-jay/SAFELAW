// src/App.tsx
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login';
import Writer from './pages/Writer';
import Reader from './pages/Reader';
import Profile from './pages/Profile';
import Layout from './components/layout.tsx';

function App() {
    return (
        <Routes>
            <Route element={<Layout />}>
                <Route path="/login" element={<Login />} />
                <Route index element={<Home />} />
                <Route path="/" element={<Home />} />
                <Route path="/writer" element={<Writer />} />
                <Route path="/reader" element={<Reader />} />
                <Route path="/profile" element={<Profile />} />
            </Route>
        </Routes>
    );
}
export default App;
