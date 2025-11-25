import { FormEvent, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CircularProgress } from '@mui/material';
import { useAuth } from '../context/AuthContext';

const Login = () => {
    const { login, user } = useAuth();
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (user) {
            navigate('/profile');
        }
    }, [user, navigate]);

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();
        setSubmitting(true);
        setError(null);
        const { error: loginError } = await login(email, password);
        if (loginError) {
            setError(loginError);
        } else {
            navigate('/profile');
        }
        setSubmitting(false);
    };

    return (
        <section
            className="max-w-md mx-auto mt-16"
            style={{
                background: 'linear-gradient(145deg, rgba(28,42,61,0.9), rgba(5,11,19,0.95))',
                borderRadius: '1.75rem',
                boxShadow: '0 25px 65px rgba(4,11,19,0.55)',
                padding: '2.5rem',
                color: 'var(--color-text-light)',
                fontFamily: 'var(--font-family-base)',
                border: '1px solid rgba(255,255,255,0.06)',
            }}
        >
            <header style={{ marginBottom: '2rem' }}>
                <p style={{ textTransform: 'uppercase', letterSpacing: '0.6em', fontSize: '0.8rem', color: 'var(--color-accent-secondary)' }}>
                    SafeLaw Access
                </p>
                <h1 style={{ fontFamily: 'var(--font-role-heading)', fontSize: '2.4rem', margin: '0.75rem 0 0', color: 'white' }}>
                    Sign in to workspace
                </h1>
            </header>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <label style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.9rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'var(--color-text-inactive)' }}>
                    Email
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        style={{
                            borderRadius: '1rem',
                            border: '1px solid rgba(255,255,255,0.15)',
                            padding: '0.9rem 1.1rem',
                            background: 'rgba(5,11,19,0.4)',
                            color: 'white',
                            fontSize: '1rem',
                            fontFamily: 'var(--font-family-base)',
                        }}
                        placeholder="clerk@example.com"
                    />
                </label>

                <label style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.9rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'var(--color-text-inactive)' }}>
                    Password
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        style={{
                            borderRadius: '1rem',
                            border: '1px solid rgba(255,255,255,0.15)',
                            padding: '0.9rem 1.1rem',
                            background: 'rgba(5,11,19,0.4)',
                            color: 'white',
                            fontSize: '1rem',
                            fontFamily: 'var(--font-family-base)',
                        }}
                        placeholder="••••••••"
                    />
                </label>

                {error && (
                    <p style={{ color: '#f87171', fontSize: '0.9rem', letterSpacing: '0.1em' }}>
                        {error}
                    </p>
                )}

                <button
                    type="submit"
                    disabled={submitting}
                    style={{
                        borderRadius: '999px',
                        border: 'none',
                        padding: '0.95rem 1.5rem',
                        background: submitting ? 'rgba(45,212,191,0.5)' : 'var(--color-accent-primary)',
                        color: 'var(--color-bg-page)',
                        fontSize: '1rem',
                        fontWeight: 600,
                        letterSpacing: '0.3em',
                        textTransform: 'uppercase',
                        cursor: submitting ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        transition: 'all 0.2s',
                    }}
                >
                    {submitting ? (
                        <>
                            <CircularProgress size={18} sx={{ color: '#F5F2EF' }} />
                            Authenticating
                        </>
                    ) : (
                        'Login'
                    )}
                </button>
            </form>
        </section>
    );
};

export default Login;
