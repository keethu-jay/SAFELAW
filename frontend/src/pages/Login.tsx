import React from "react";


const Login: React.FC = () => {
    return (
        <section
            className="max-w-md mx-auto mt-10"
            style={{
                background: 'var(--color-bg-page)',
                color: 'var(--color-text-dark)',
                borderRadius: '1.5rem',
                boxShadow: '0 4px 32px rgba(9,19,37,0.10)',
                padding: '2.5rem',
                fontFamily: 'var(--font-family-base)',
            }}
        >
            <h1
                className="logo"
                style={{
                    fontFamily: 'var(--font-role-heading)',
                    fontWeight: 700,
                    fontSize: '2rem',
                    color: 'var(--color-accent-primary)',
                    marginBottom: '1.5rem',
                }}
            >
                Login
            </h1>
            <p className="text-content" style={{ color: 'var(--color-text-inactive)', marginBottom: '1.5rem' }}>
                Enter your credentials to access your account (pretend we have authentication set up).
            </p>
            {/* Add your login form below */}
        </section>
    );
};

export default Login;
