import { Box } from '@mui/material';
import { NavLink } from 'react-router-dom';

const heroTextBackground = '/src/depositphotos_723177556-stock-photo-judge-gavel-light-table-office.jpg';

const Home = () => {
    return (
        <Box component="section" sx={styles.heroWrapper}>
            {/* Content Container */}
            <Box sx={styles.contentWrapper}>
                {/* Top Bar - Original SafeLaw Logo */}
                <Box component="p" sx={styles.logo}>SafeLaw</Box>

                {/* Hero Content */}
                <Box sx={styles.heroContent}>
                    {/* Text Container with Background Image Support */}
                    <Box sx={styles.textContainer}>
                        {/* Background Image Layer */}
                        <Box 
                            sx={{
                                ...styles.textBackgroundImage,
                                backgroundImage: `url(${heroTextBackground})`,
                            }} 
                        />
                        {/* Text Content Overlay */}
                        <Box sx={styles.textOverlay}>
                            {/* Badge */}
                            <Box sx={styles.badge}>
                                <Box component="span" sx={styles.badgeDot} />
                                <Box component="span" sx={styles.badgeText}>AI-Powered Legal Intelligence</Box>
                            </Box>

                            {/* Main Headline */}
                            <Box component="h1" sx={styles.headline}>
                                Intelligence, Drafting &amp;
                                <br />
                                <Box component="span" sx={styles.headlineAccent}>Research</Box> in One
                                <br />
                                Litigation Workspace
                            </Box>

                            {/* Subheadline */}
                            <Box component="p" sx={styles.subheadline}>
                                SafeLaw amplifies legal teams with contextual drafting, evidence triage, 
                                and structured reading modes—merging precision with clarity.
                            </Box>
                        </Box>
                    </Box>

                    {/* Buttons Container */}
                    <Box sx={styles.buttonsRow}>
                        {/* Writing Button Box */}
                        <Box sx={styles.buttonBox}>
                            <Box sx={styles.buttonRow}>
                                <Box 
                                    component={NavLink} 
                                    to="/writer" 
                                    sx={styles.ctaPrimary}
                                >
                                    Writing Tool
                                </Box>
                                <Box 
                                    component={NavLink} 
                                    to="https://glassmanlab.seas.harvard.edu/papers/corpusstudio.pdf" 
                                    sx={styles.ctaPrimaryOutline}
                                >
                                    Corpus Studio
                                </Box>
                            </Box>
                            <Box component="p" sx={styles.captionText}>
                                AI-powered contextual drafting with intelligent clause suggestions and legal document assembly.
                            </Box>
                        </Box>

                        {/* Reading Button Box */}
                        <Box sx={styles.buttonBox}>
                            <Box sx={styles.buttonRow}>
                                <Box 
                                    component={NavLink} 
                                    to="/reader" 
                                    sx={styles.ctaSecondary}
                                >
                                    Reading Tool
                                </Box>
                                <Box 
                                    component={NavLink} 
                                    to="https://glassmanlab.seas.harvard.edu/papers/gptsm.pdf" 
                                    sx={styles.ctaSecondaryOutline}
                                >
                                    GP-TSM
                                </Box>
                            </Box>
                            <Box component="p" sx={styles.captionText}>
                                Advanced document summarizer that analyzes case files and generates concise, actionable insights.
                            </Box>
                        </Box>
                    </Box>
                    <Box sx={styles.trustSection}>
                    </Box>
                </Box>
            </Box>

            {/* Inline Keyframes */}
            <style>{`
                @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Sora:wght@300;400;500;600&display=swap');
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            `}</style>
        </Box>
    );
};

const styles = {
    heroWrapper: {
        position: 'relative',
        minHeight: '100vh',
        width: '100%',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #1C2A3D 0%, #091325 100%)',
    },
    
    contentWrapper: {
        position: 'relative',
        zIndex: 10,
        margin: '0 auto',
        padding: '1rem 3rem',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
    },
    
    logo: {
        textTransform: 'uppercase',
        letterSpacing: '0.8em',
        color: 'white',
        fontWeight: 300,
        fontFamily: 'var(--font-role-logo)',
        fontSize: '1.1rem',
        marginBottom: '1.5rem',
        position: 'relative',
    },
    
    heroContent: {
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        paddingTop: '1rem',
        paddingBottom: '4rem',
    },

    textContainer: {
        position: 'relative',
        borderRadius: '16px',
        overflow: 'hidden',
        marginBottom: '2.5rem',
    },

    textBackgroundImage: {
        position: 'absolute',
        inset: 0,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        opacity: 1,
    },

    textOverlay: {
        position: 'relative',
        zIndex: 1,
        padding: '2.5rem',
        background: 'rgba(9, 19, 37, 0.7)',
        backdropFilter: 'blur(8px)',
    },
    
    badge: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.75rem',
        background: 'rgba(196, 98, 60, 0.1)',
        border: '1px solid rgba(196, 98, 60, 0.2)',
        borderRadius: '100px',
        padding: '0.5rem 1.25rem',
        marginBottom: '2rem',
        width: 'fit-content',
    },
    
    badgeDot: {
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: '#C4623C',
        animation: 'pulse 2s ease-in-out infinite',
    },
    
    badgeText: {
        fontFamily: "'Sora', sans-serif",
        fontSize: '0.8rem',
        fontWeight: 500,
        color: '#C4623C',
        letterSpacing: '0.05em',
    },
    
    headline: {
        fontFamily: "'Cormorant Garamond', Georgia, serif",
        fontSize: 'clamp(2.5rem, 5vw, 4.5rem)',
        fontWeight: 600,
        lineHeight: 1.1,
        color: '#fff',
        margin: '0 0 1.75rem 0',
        letterSpacing: '-0.02em',
    },
    
    headlineAccent: {
        color: '#C4623C',
        fontStyle: 'italic',
    },
    
    subheadline: {
        fontFamily: "'Sora', sans-serif",
        fontSize: '1.125rem',
        fontWeight: 300,
        lineHeight: 1.7,
        color: 'rgba(255, 255, 255, 0.6)',
        margin: 0,
        maxWidth: '560px',
    },

    buttonsRow: {
        display: 'flex',
        gap: '10%',
        marginBottom: '3rem',
        padding: '0 5%',
    },

    buttonBox: {
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        textAlign: 'left',
        padding: '2rem',
        background: '#1C2A3D',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
    },

    buttonRow: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-evenly',
        width: '100%',
        marginBottom: '1rem',
    },
    
    ctaPrimary: {
        fontFamily: "'Sora', sans-serif",
        fontSize: '0.95rem',
        fontWeight: 500,
        color: '#fff',
        background: '#C4623C',
        border: 'none',
        borderRadius: '50px',
        padding: '1rem 2rem',
        minWidth: '180px',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        textDecoration: 'none',
        transition: 'all 0.3s ease',
        boxShadow: '0 0 20px rgba(196, 98, 60, 0.3)',
        '&:hover': {
            background: '#FF8C47',
            transform: 'translateY(-2px)',
            boxShadow: '0 0 30px rgba(255, 140, 71, 0.5)',
        },
    },
    
    ctaSecondary: {
        fontFamily: "'Sora', sans-serif",
        fontSize: '0.95rem',
        fontWeight: 500,
        color: '#fff',
        background: '#008C99',
        border: 'none',
        borderRadius: '50px',
        padding: '1rem 2rem',
        minWidth: '180px',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        textDecoration: 'none',
        transition: 'all 0.3s ease',
        boxShadow: '0 0 20px rgba(0, 140, 153, 0.3)',
        '&:hover': {
            background: '#00D9ED',
            transform: 'translateY(-2px)',
            boxShadow: '0 0 30px rgba(0, 217, 237, 0.5)',
        },
    },

    ctaPrimaryOutline: {
        fontFamily: "'Sora', sans-serif",
        fontSize: '0.95rem',
        fontWeight: 500,
        color: '#C4623C',
        background: 'transparent',
        border: '2px solid #C4623C',
        borderRadius: '50px',
        padding: '1rem 2rem',
        minWidth: '180px',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        textDecoration: 'none',
        transition: 'all 0.3s ease',
        '&:hover': {
            color: '#FF8C47',
            borderColor: '#FF8C47',
            transform: 'translateY(-2px)',
            boxShadow: '0 0 20px rgba(255, 140, 71, 0.3)',
        },
    },

    ctaSecondaryOutline: {
        fontFamily: "'Sora', sans-serif",
        fontSize: '0.95rem',
        fontWeight: 500,
        color: '#008C99',
        background: 'transparent',
        border: '2px solid #008C99',
        borderRadius: '50px',
        padding: '1rem 2rem',
        minWidth: '180px',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        textDecoration: 'none',
        transition: 'all 0.3s ease',
        '&:hover': {
            color: '#00D9ED',
            borderColor: '#00D9ED',
            transform: 'translateY(-2px)',
            boxShadow: '0 0 20px rgba(0, 217, 237, 0.3)',
        },
    },

    captionText: {
        fontFamily: "'Sora', sans-serif",
        fontSize: '0.85rem',
        fontWeight: 300,
        lineHeight: 1.5,
        color: 'rgba(255, 255, 255, 0.5)',
        margin: 0,
    },
    
    trustSection: {
        paddingTop: '2rem',
        borderTop: '3px solid rgba(255, 255, 255, 0.15)',
    },
    
    trustLabel: {
        fontFamily: "'Sora', sans-serif",
        fontSize: '0.75rem',
        fontWeight: 400,
        color: 'rgba(255, 255, 255, 0.4)',
        textTransform: 'uppercase',
        letterSpacing: '0.15em',
        marginBottom: '1rem',
    },
    
    trustLogos: {
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        flexWrap: 'wrap',
    },
    
    trustLogo: {
        fontFamily: "'Cormorant Garamond', Georgia, serif",
        fontSize: '1rem',
        fontWeight: 500,
        color: 'rgba(255, 255, 255, 0.5)',
        fontStyle: 'italic',
    },
    
    trustDivider: {
        color: 'rgba(255, 255, 255, 0.2)',
    },
};

export default Home;