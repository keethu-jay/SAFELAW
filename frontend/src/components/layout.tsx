import { Outlet } from 'react-router-dom';
import { Box } from '@mui/material';
import Header from './Header';
import Footer from './Footer';

const Layout = () => (
    <Box className="flex min-h-screen flex-col bg-[#040b13] text-white">
        <Header />
        <main className="flex-1 bg-[#050e1a]">
            <Box className="w-full px-4 py-6 sm:px-8 sm:py-10">
                <Outlet />
            </Box>
        </main>
        <Footer />
    </Box>
);

export default Layout;