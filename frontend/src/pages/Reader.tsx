import { NavLink } from 'react-router-dom';


const Reader = () => (
    <div style={{ color: 'var(--color-text-light)', fontFamily: 'var(--font-family-base)' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
            <div style={{ background: 'var(--color-bg-card)', borderRadius: '999px', padding: '0.35rem' }}>
                {[
                    { label: 'Writing', href: '/writer' },
                    { label: 'Reading', href: '/reader' },
                ].map((tab) => (
                    <NavLink
                        key={tab.href}
                        to={tab.href}
                        style={({ isActive }) => ({
                            background: isActive ? 'var(--color-accent-primary)' : 'transparent',
                            color: isActive ? 'var(--color-bg-page)' : 'var(--color-text-inactive)',
                            borderRadius: '999px',
                            padding: '0.55rem 1.6rem',
                            fontSize: '1rem',
                            fontWeight: 600,
                            margin: '0 0.2rem',
                            border: 'none',
                            transition: 'all 0.2s',
                        })}
                    >
                        {tab.label}
                    </NavLink>
                ))}
            </div>
        </div>

        <section
            style={{
                background: 'linear-gradient(135deg, #1C2A3D 0%, #091325 100%)',
                borderRadius: '2rem',
                padding: '2.5rem',
                marginTop: '2rem',
            }}
        >
            <h1
                style={{
                    fontFamily: 'var(--font-role-heading)',
                    fontWeight: 700,
                    fontSize: '2rem',
                    marginBottom: '1.5rem',
                }}
            >
                Reading Workspace
            </h1>
            <p className="text-content" style={{ color: 'var(--color-text-light)' }}>
                GP-TSM plug-in here, add drag-and-drop functionality for case bundles and highlight chains.
            </p>
        </section>
    </div>
);

export default Reader;
