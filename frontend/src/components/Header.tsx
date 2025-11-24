import { NavLink, Link } from 'react-router-dom';
import { Box } from '@mui/material';
import GavelRoundedIcon from '@mui/icons-material/GavelRounded';

const isLoggedIn = false; // TODO: integrate with auth state

const Header = () => (
    <header style={{ borderBottom: '1px solid var(--color-text-inactive)', background: 'rgba(28,42,61,0.95)', boxShadow: '0 2px 12px rgba(9,19,37,0.10)', backdropFilter: 'blur(8px)' }}>
        <Box style={{ display: 'flex', width: '100%', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', padding: '1.25rem 2.5rem', fontFamily: 'var(--font-family-base)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Link
                    to="/"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontFamily: 'var(--font-role-logo)',
                        fontWeight: 300,
                        letterSpacing: '0.6em',
                        textTransform: 'uppercase',
                        color: 'white',
                        fontSize: '1.3rem',
                        textDecoration: 'none',
                        position: 'relative',
                    }}
                >
                    <GavelRoundedIcon sx={{ fontSize: 24, color: 'var(--color-accent-secondary)' }} />
                    SafeLaw
                </Link>
            </div>

            <nav style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'flex-end', gap: '1rem' }}>
                <NavLink to="/writer" style={{
                    background: 'var(--color-accent-primary)',
                    color: 'var(--color-bg-page)',
                    border: 'none',
                    borderRadius: '9999px',
                    padding: '0.75rem 1.5rem',
                    fontWeight: 400,
                    fontFamily: 'var(--font-family-base)',
                    textDecoration: 'none',
                    transition: 'all 0.2s',
                }}>
                    Workspace
                </NavLink>
                <NavLink
                    to={isLoggedIn ? '/profile' : '/login'}
                    style={{
                        background: 'transparent',
                        color: 'var(--color-accent-primary)',
                        border: '1px solid var(--color-accent-primary)',
                        borderRadius: '9999px',
                        padding: '0.75rem 1.5rem',
                        fontWeight: 400,
                        fontFamily: 'var(--font-family-base)',
                        textDecoration: 'none',
                        transition: 'all 0.2s',
                    }}
                >
                    {isLoggedIn ? 'Profile' : 'Login'}
                </NavLink>
            </nav>
        </Box>
    </header>
);

export default Header;