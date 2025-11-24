import { Outlet } from 'react-router-dom';
import { Box } from '@mui/material';
import Header from './Header';
import Footer from './Footer';


const Layout = () => (
    <Box style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--color-bg-main)', color: 'var(--color-text-light)', fontFamily: 'var(--font-family-base)' }}>
        <Header />
        <main style={{ flex: 1, background: 'var(--color-bg-main)' }}>
            <Box style={{ width: '100%', padding: '2rem 0.5rem 2.5rem 0.5rem', maxWidth: '100vw' }}>
                <Outlet />
            </Box>
        </main>
        <Footer />
    </Box>
);

export default Layout;