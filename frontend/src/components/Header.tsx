import { NavLink, Link } from 'react-router-dom';
import { Box } from '@mui/material';
import GavelRoundedIcon from '@mui/icons-material/GavelRounded';

const isLoggedIn = false; // TODO: integrate with auth state

const Header = () => (
    <header className="border-b border-white/10 bg-[#0b1726]/90 shadow-lg backdrop-blur">
        <Box className="flex w-full flex-wrap items-center justify-between gap-4 px-4 py-5 sm:flex-nowrap sm:px-10 lg:px-16">
            <div className="flex items-center gap-3">
                <Link to="/" className="flex items-center gap-2 text-lg font-semibold tracking-[0.6em] uppercase text-white hover:text-emerald-200 transition-colors">
                    <GavelRoundedIcon sx={{ fontSize: 24 }} />
                    SafeLaw
                </Link>
            </div>

            <nav className="flex flex-1 items-center justify-end gap-3">
                <NavLink to="/writer" className="safelaw-cta safelaw-cta--primary">
                    Workspace
                </NavLink>
                <NavLink
                    to={isLoggedIn ? '/profile' : '/login'}
                    className="safelaw-cta safelaw-cta--ghost"
                >
                    {isLoggedIn ? 'Profile' : 'Login'}
                </NavLink>
            </nav>
        </Box>
    </header>
);

export default Header;