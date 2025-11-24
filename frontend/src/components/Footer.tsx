import { Box } from '@mui/material';


const Footer = () => (
    <footer style={{ borderTop: '1px solid var(--color-text-inactive)', background: 'var(--color-bg-card)' }}>
        <Box style={{ display: 'flex', width: '100%', flexDirection: 'column', gap: '0.5rem', padding: '1rem 2rem', color: 'var(--color-text-inactive)', fontFamily: 'var(--font-family-base)', fontSize: '0.95rem' }}>
            <span>© {new Date().getFullYear()} SafeLaw</span>
        </Box>
    </footer>
);

export default Footer;

