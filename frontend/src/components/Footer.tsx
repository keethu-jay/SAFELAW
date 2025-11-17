import { Box } from '@mui/material';

const Footer = () => (
    <footer className="border-t border-white/10 bg-[#0b1726]">
        <Box className="flex w-full flex-col gap-2 px-4 py-4 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between sm:px-8 sm:text-sm">
            <span>© {new Date().getFullYear()} SafeLaw</span>
        </Box>
    </footer>
);

export default Footer;

