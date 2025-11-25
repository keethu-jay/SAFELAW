import React from 'react';
import { Box, Paper, Stack, Typography, Divider, Button } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import LogoutIcon from '@mui/icons-material/Logout';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Hardcoded example data
const lastEdits = [
    { file: 'R v. Smith - Majority Opinion', time: '2 hours ago', type: 'Edit' },
    { file: 'Miller v. Prime Minister - Dissent', time: '1 day ago', type: 'Edit' },
    { file: 'Begum v. SIAC - Concurring', time: '3 days ago', type: 'Edit' },
];

const lastOpenedFiles = [
    { name: 'Cobbe v. Yeoman\'s Row [2008] UKHL 55', opened: '5 hours ago' },
    { name: 'FHR European Ventures v. Cedar Capital [2014] UKSC 45', opened: 'Yesterday' },
    { name: 'R (Citizens UK) v. Home Secretary [2018] EWCA Civ 1812', opened: '2 days ago' },
];

const filesInProcessing = [
    { name: 'Khan v. Information Commissioner [2016] UKUT 486', status: 'Analyzing', progress: 75 },
    { name: 'Perry v. Raleys Solicitors [2019] UKSC 5', status: 'Extracting', progress: 45 },
];

const collaborativeDocs = [
    { name: 'Joint Opinion - R v. Crown Prosecution Service', collaborators: 3, lastActivity: '1 hour ago' },
    { name: 'Appeal Brief - Smith v. Jones', collaborators: 2, lastActivity: '4 hours ago' },
];

const Profile: React.FC = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    return (
        <div style={{ color: 'var(--color-text-light)', fontFamily: 'var(--font-family-base)' }}>
            <div style={{ display: 'grid', gap: '2rem', gridTemplateColumns: 'minmax(0,1fr) minmax(0,0.8fr)', marginBottom: '2rem' }}>
                {/* Left Column: Image + Activity */}
                <Stack spacing={3}>
                    {/* Profile Image */}
                    <Paper
                        elevation={8}
                        style={{
                            borderRadius: '2rem',
                            background: 'var(--color-bg-card)',
                            padding: '2.5rem',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '1.5rem',
                        }}
                    >
                        <Box
                            style={{
                                width: '180px',
                                height: '180px',
                                borderRadius: '50%',
                                background: 'rgba(0, 140, 153, 0.15)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                border: '3px solid var(--color-accent-primary)',
                            }}
                        >
                            <PersonIcon sx={{ fontSize: 100, color: 'var(--color-accent-primary)' }} />
                        </Box>
                        <div style={{ textAlign: 'center' }}>
                            <Typography
                                variant="h5"
                                style={{
                                    fontFamily: 'var(--font-role-heading)',
                                    fontWeight: 700,
                                    color: 'var(--color-text-light)',
                                    marginBottom: '0.5rem',
                                }}
                            >
                                Jane Doe
                            </Typography>
                            <Typography
                                style={{
                                    color: 'var(--color-text-inactive)',
                                    fontSize: '0.9rem',
                                    letterSpacing: '0.1em',
                                    textTransform: 'uppercase',
                                }}
                            >
                                Legal Counsel
                            </Typography>
                        </div>
                    </Paper>

                    {/* Activity Sections */}
                    <Paper
                        elevation={8}
                        style={{
                            borderRadius: '2rem',
                            background: 'rgba(255,255,255,0.05)',
                            padding: '2rem',
                        }}
                    >
                        <Typography
                            variant="h6"
                            style={{
                                fontFamily: 'var(--font-role-heading)',
                                fontWeight: 700,
                                color: 'var(--color-text-light)',
                                marginBottom: '1.5rem',
                            }}
                        >
                            Recent Activity
                        </Typography>

                        {/* Last Edits */}
                        <div style={{ marginBottom: '2rem' }}>
                            <Typography
                                style={{
                                    fontSize: '0.85rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.3em',
                                    color: 'var(--color-text-inactive)',
                                    marginBottom: '1rem',
                                    fontWeight: 600,
                                }}
                            >
                                Last Edits
                            </Typography>
                            <Stack spacing={1.5}>
                                {lastEdits.map((edit, idx) => (
                                    <Box
                                        key={idx}
                                        style={{
                                            background: 'rgba(255,255,255,0.03)',
                                            borderRadius: '1rem',
                                            padding: '1rem',
                                            border: '1px solid rgba(255,255,255,0.08)',
                                        }}
                                    >
                                        <Typography
                                            style={{
                                                color: 'var(--color-text-light)',
                                                fontSize: '0.95rem',
                                                marginBottom: '0.4rem',
                                                fontFamily: 'var(--font-role-body)',
                                            }}
                                        >
                                            {edit.file}
                                        </Typography>
                                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                            <span
                                                style={{
                                                    fontSize: '0.75rem',
                                                    color: 'var(--color-accent-primary)',
                                                    textTransform: 'uppercase',
                                                    letterSpacing: '0.2em',
                                                }}
                                            >
                                                {edit.type}
                                            </span>
                                            <span
                                                style={{
                                                    fontSize: '0.75rem',
                                                    color: 'var(--color-text-inactive)',
                                                }}
                                            >
                                                {edit.time}
                                            </span>
                                        </div>
                                    </Box>
                                ))}
                            </Stack>
                        </div>

                        <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '1.5rem 0' }} />

                        {/* Last Opened Files */}
                        <div style={{ marginBottom: '2rem' }}>
                            <Typography
                                style={{
                                    fontSize: '0.85rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.3em',
                                    color: 'var(--color-text-inactive)',
                                    marginBottom: '1rem',
                                    fontWeight: 600,
                                }}
                            >
                                Last Opened Files
                            </Typography>
                            <Stack spacing={1.5}>
                                {lastOpenedFiles.map((file, idx) => (
                                    <Box
                                        key={idx}
                                        style={{
                                            background: 'rgba(255,255,255,0.03)',
                                            borderRadius: '1rem',
                                            padding: '1rem',
                                            border: '1px solid rgba(255,255,255,0.08)',
                                        }}
                                    >
                                        <Typography
                                            style={{
                                                color: 'var(--color-text-light)',
                                                fontSize: '0.9rem',
                                                marginBottom: '0.4rem',
                                                fontFamily: 'var(--font-role-body)',
                                            }}
                                        >
                                            {file.name}
                                        </Typography>
                                        <span
                                            style={{
                                                fontSize: '0.75rem',
                                                color: 'var(--color-text-inactive)',
                                            }}
                                        >
                                            Opened {file.opened}
                                        </span>
                                    </Box>
                                ))}
                            </Stack>
                        </div>

                        <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '1.5rem 0' }} />

                        {/* Files in Processing */}
                        <div style={{ marginBottom: '2rem' }}>
                            <Typography
                                style={{
                                    fontSize: '0.85rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.3em',
                                    color: 'var(--color-text-inactive)',
                                    marginBottom: '1rem',
                                    fontWeight: 600,
                                }}
                            >
                                Files in Processing
                            </Typography>
                            <Stack spacing={1.5}>
                                {filesInProcessing.map((file, idx) => (
                                    <Box
                                        key={idx}
                                        style={{
                                            background: 'rgba(255,255,255,0.03)',
                                            borderRadius: '1rem',
                                            padding: '1rem',
                                            border: '1px solid rgba(255,255,255,0.08)',
                                        }}
                                    >
                                        <Typography
                                            style={{
                                                color: 'var(--color-text-light)',
                                                fontSize: '0.9rem',
                                                marginBottom: '0.5rem',
                                                fontFamily: 'var(--font-role-body)',
                                            }}
                                        >
                                            {file.name}
                                        </Typography>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                                            <span
                                                style={{
                                                    fontSize: '0.75rem',
                                                    color: 'var(--color-accent-secondary)',
                                                    textTransform: 'uppercase',
                                                    letterSpacing: '0.2em',
                                                }}
                                            >
                                                {file.status}
                                            </span>
                                            <span
                                                style={{
                                                    fontSize: '0.75rem',
                                                    color: 'var(--color-text-inactive)',
                                                }}
                                            >
                                                {file.progress}%
                                            </span>
                                        </div>
                                        <div
                                            style={{
                                                width: '100%',
                                                height: '6px',
                                                background: 'rgba(255,255,255,0.1)',
                                                borderRadius: '999px',
                                                overflow: 'hidden',
                                            }}
                                        >
                                            <div
                                                style={{
                                                    width: `${file.progress}%`,
                                                    height: '100%',
                                                    background: 'var(--color-accent-primary)',
                                                    borderRadius: '999px',
                                                    transition: 'width 0.3s',
                                                }}
                                            />
                                        </div>
                                    </Box>
                                ))}
                            </Stack>
                        </div>

                        <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '1.5rem 0' }} />

                        {/* Collaborative Documents */}
                        <div>
                            <Typography
                                style={{
                                    fontSize: '0.85rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.3em',
                                    color: 'var(--color-text-inactive)',
                                    marginBottom: '1rem',
                                    fontWeight: 600,
                                }}
                            >
                                Collaborative Documents
                            </Typography>
                            <Stack spacing={1.5}>
                                {collaborativeDocs.map((doc, idx) => (
                                    <Box
                                        key={idx}
                                        style={{
                                            background: 'rgba(255,255,255,0.03)',
                                            borderRadius: '1rem',
                                            padding: '1rem',
                                            border: '1px solid rgba(255,255,255,0.08)',
                                        }}
                                    >
                                        <Typography
                                            style={{
                                                color: 'var(--color-text-light)',
                                                fontSize: '0.9rem',
                                                marginBottom: '0.4rem',
                                                fontFamily: 'var(--font-role-body)',
                                            }}
                                        >
                                            {doc.name}
                                        </Typography>
                                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                            <span
                                                style={{
                                                    fontSize: '0.75rem',
                                                    color: 'var(--color-accent-primary)',
                                                }}
                                            >
                                                {doc.collaborators} collaborator{doc.collaborators > 1 ? 's' : ''}
                                            </span>
                                            <span
                                                style={{
                                                    fontSize: '0.75rem',
                                                    color: 'var(--color-text-inactive)',
                                                }}
                                            >
                                                Updated {doc.lastActivity}
                                            </span>
                                        </div>
                                    </Box>
                                ))}
                            </Stack>
                        </div>
                    </Paper>
                </Stack>

                {/* Right Column: About Me */}
                <Paper
                    elevation={8}
                    style={{
                        borderRadius: '2rem',
                        background: 'var(--color-bg-card)',
                        padding: '2.5rem',
                        height: 'fit-content',
                    }}
                >
                    <Typography
                        variant="h5"
                        style={{
                            fontFamily: 'var(--font-role-heading)',
                            fontWeight: 700,
                            color: 'var(--color-text-light)',
                            marginBottom: '1.5rem',
                        }}
                    >
                        About Me
                    </Typography>
                    <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', marginBottom: '1.5rem' }} />
                    <Stack spacing={2}>
                        <div>
                            <Typography
                                style={{
                                    fontSize: '0.85rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.3em',
                                    color: 'var(--color-text-inactive)',
                                    marginBottom: '0.5rem',
                                    fontWeight: 600,
                                }}
                            >
                                Role
                            </Typography>
                            <Typography
                                style={{
                                    color: 'var(--color-text-light)',
                                    fontFamily: 'var(--font-role-body)',
                                }}
                            >
                                Senior Legal Counsel
                            </Typography>
                        </div>
                        <div>
                            <Typography
                                style={{
                                    fontSize: '0.85rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.3em',
                                    color: 'var(--color-text-inactive)',
                                    marginBottom: '0.5rem',
                                    fontWeight: 600,
                                }}
                            >
                                Specialization
                            </Typography>
                            <Typography
                                style={{
                                    color: 'var(--color-text-light)',
                                    fontFamily: 'var(--font-role-body)',
                                }}
                            >
                                Constitutional Law, Administrative Law, Public Law
                            </Typography>
                        </div>
                        <div>
                            <Typography
                                style={{
                                    fontSize: '0.85rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.3em',
                                    color: 'var(--color-text-inactive)',
                                    marginBottom: '0.5rem',
                                    fontWeight: 600,
                                }}
                            >
                                Experience
                            </Typography>
                            <Typography
                                style={{
                                    color: 'var(--color-text-light)',
                                    fontFamily: 'var(--font-role-body)',
                                }}
                            >
                                12 years of practice in UK courts, specializing in judicial review and human rights
                                litigation. Extensive experience drafting opinions for Supreme Court and Court of Appeal
                                cases.
                            </Typography>
                        </div>
                        <div>
                            <Typography
                                style={{
                                    fontSize: '0.85rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.3em',
                                    color: 'var(--color-text-inactive)',
                                    marginBottom: '0.5rem',
                                    fontWeight: 600,
                                }}
                            >
                                Contact
                            </Typography>
                            <Typography
                                style={{
                                    color: 'var(--color-text-light)',
                                    fontFamily: 'var(--font-role-body)',
                                }}
                            >
                                jane.doe@example.co.uk
                            </Typography>
                        </div>
                    </Stack>
                    <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', marginTop: '1.5rem', marginBottom: '1.5rem' }} />
                    <Button
                        variant="outlined"
                        onClick={handleLogout}
                        startIcon={<LogoutIcon />}
                        style={{
                            width: '100%',
                            borderRadius: '999px',
                            padding: '0.75rem 1.5rem',
                            borderWidth: 2,
                            textTransform: 'none',
                            fontWeight: 400,
                            color: 'var(--color-accent-secondary)',
                            borderColor: 'var(--color-accent-secondary)',
                            background: 'transparent',
                            fontFamily: 'var(--font-family-base)',
                            transition: 'all 0.2s',
                        }}
                        onMouseOver={(e) => {
                            e.currentTarget.style.background = 'rgba(196, 98, 60, 0.1)';
                            e.currentTarget.style.borderColor = 'var(--color-accent-secondary-hover)';
                            e.currentTarget.style.color = 'var(--color-accent-secondary-hover)';
                        }}
                        onMouseOut={(e) => {
                            e.currentTarget.style.background = 'transparent';
                            e.currentTarget.style.borderColor = 'var(--color-accent-secondary)';
                            e.currentTarget.style.color = 'var(--color-accent-secondary)';
                        }}
                    >
                        Sign Out
                    </Button>
                </Paper>
            </div>
        </div>
    );
};

export default Profile;
