import { NavLink, Link } from 'react-router-dom';
import { Box } from '@mui/material';
import GavelRoundedIcon from '@mui/icons-material/GavelRounded';
import AccountCircleOutlinedIcon from '@mui/icons-material/AccountCircleOutlined';
import { useAuth } from '../context/AuthContext';

const Header = () => {
    const { user } = useAuth();

    return (
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
                {user && (
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
                )}
                {user ? (
                    <Link
                        to="/profile"
                        style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: '2.75rem',
                            height: '2.75rem',
                            borderRadius: '9999px',
                            border: '1px solid rgba(255,255,255,0.25)',
                            color: 'var(--color-text-light)',
                            transition: 'all 0.2s',
                        }}
                    >
                        <AccountCircleOutlinedIcon fontSize="medium" />
                    </Link>
                ) : (
                    <NavLink
                        to="/login"
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
                        Login
                    </NavLink>
                )}
            </nav>
        </Box>
    </header>
    );
};

export default Header;