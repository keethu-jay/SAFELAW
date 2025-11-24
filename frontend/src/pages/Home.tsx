
const Home = () => (
    <section
        className="mx-auto mt-10 max-w-5xl"
        style={{
            background: 'linear-gradient(135deg, #1C2A3D 0%, #091325 100%)',
            borderRadius: '2.5rem',
            padding: '3rem',
            color: 'var(--color-text-light)',
            fontFamily: 'var(--font-family-base)',
            boxShadow: '0 25px 60px rgba(9,19,37,0.25)'
        }}
    >
        <p
            className="logo"
            style={{
                textTransform: 'uppercase',
                letterSpacing: '0.8em',
                color: 'white',
                fontWeight: 300,
                fontFamily: 'var(--font-role-logo)',
                fontSize: '1.1rem',
                marginBottom: '1.5rem',
                position: 'relative',
            }}
        >
            SafeLaw
        </p>
        <h1
            style={{
                fontFamily: 'var(--font-role-heading)',
                fontWeight: 700,
                fontSize: '2.5rem',
                lineHeight: 1.2,
                marginBottom: '1.5rem',
            }}
        >
            Intelligence, drafting, and research in one litigation workspace.
        </h1>
        <p
            className="text-content"
            style={{
                maxWidth: '40rem',
                color: 'var(--color-text-light)',
                fontSize: '1.1rem',
            }}
        >
            SafeLaw amplifies legal teams with contextual drafting, evidence triage, and structured reading modes, merging CorpusStudios logic with GP-TSM clarity.
        </p>
    </section>
);

export default Home;
