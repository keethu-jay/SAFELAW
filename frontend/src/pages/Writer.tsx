import { Box, Button, Chip, Divider, Paper, Stack, Typography } from '@mui/material';
import { NavLink } from 'react-router-dom';

const suggestionItems = [
    {
        title: "The plaintiff's argument regarding unjust enrichment is strongly supported by the precedent set in “Smith v. Jones”.",
        tag: 'Similarity 92%',
    },
    {
        title: 'Furthermore, evidence presented indicates a clear breach of fiduciary duty by the defendant.',
        tag: 'Similarity 85%',
    },
    {
        title: 'This aligns with the established principle of “res ipsa loquitur”, implying negligence on the part of the defendant.',
        tag: 'Similarity 78%',
    },
    {
        title: 'It is therefore incumbent upon the court to…',
        tag: 'Similarity 74%',
    },
];

const Writer = () => (
    <div style={{ color: 'var(--color-text-light)', fontFamily: 'var(--font-family-base)' }}>
        <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '2rem' }}>
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


        <div style={{ display: 'grid', gap: '2rem', gridTemplateColumns: 'minmax(0,1.7fr) minmax(0,1fr)' }}>
            <Paper
                elevation={8}
                style={{
                    borderRadius: '2rem',
                    background: 'linear-gradient(135deg, #1C2A3D 0%, #091325 100%)',
                    padding: '2.5rem',
                    color: 'var(--color-text-light)',
                }}
            >
                <Stack spacing={4}>
                    <div>
                        <p style={{ textTransform: 'uppercase', letterSpacing: '0.4em', color: 'var(--color-accent-primary)', fontSize: '1rem', marginBottom: '1rem' }}>Draft Legal Brief</p>
                        <Typography variant="h4" style={{ fontFamily: 'var(--font-role-heading)', fontWeight: 700, color: 'var(--color-text-light)' }}>
                            Case of John Doe v. Acme Corp.
                        </Typography>
                    </div>

                    <Divider style={{ borderColor: 'var(--color-text-inactive)' }} />

                    <Stack direction="row" spacing={1}>
                        {['B', 'I', 'U'].map((icon) => (
                            <Button
                                key={icon}
                                variant="outlined"
                                size="small"
                                style={{
                                    color: 'var(--color-text-inactive)',
                                    borderColor: 'var(--color-text-inactive)',
                                    minWidth: '44px',
                                    borderRadius: '12px',
                                    fontWeight: 300,
                                    fontFamily: 'var(--font-family-base)',
                                }}
                            >
                                {icon}
                            </Button>
                        ))}
                    </Stack>

                    <Box
                        component="textarea"
                        defaultValue={`WHEREAS, the Plaintiff, John Doe, asserts a claim for breach of contract against the Defendant, Acme Corporation, stemming from a purported failure to deliver services as outlined in the agreement dated January 15, 2023...`}
                        style={{
                            minHeight: '360px',
                            width: '100%',
                            resize: 'none',
                            borderRadius: '1.5rem',
                            background: 'rgba(9,19,37,0.8)',
                            padding: '1.5rem',
                            fontSize: '1.1rem',
                            color: 'var(--color-text-light)',
                            fontFamily: 'var(--font-family-base)',
                            outline: 'none',
                            border: '1px solid var(--color-text-inactive)',
                        }}
                    />

                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="flex-end">
                        <Button
                            variant="outlined"
                            style={{
                                borderRadius: '999px',
                                padding: '0.75rem 1.5rem',
                                borderWidth: 2,
                                textTransform: 'none',
                                fontWeight: 300,
                                color: 'var(--color-accent-primary)',
                                borderColor: 'var(--color-accent-primary)',
                                background: 'transparent',
                                fontFamily: 'var(--font-family-base)',
                            }}
                        >
                            Save Draft
                        </Button>
                        <Button
                            variant="contained"
                            style={{
                                borderRadius: '999px',
                                padding: '0.75rem 1.5rem',
                                fontWeight: 300,
                                textTransform: 'none',
                                background: 'var(--color-accent-primary)',
                                color: 'var(--color-bg-page)',
                                boxShadow: '0 4px 15px rgba(0, 217, 237, 0.4)',
                                fontFamily: 'var(--font-family-base)',
                            }}
                        >
                            Export Document
                        </Button>
                    </Stack>
                </Stack>
            </Paper>

            <Paper
                elevation={8}
                style={{
                    borderRadius: '2rem',
                    background: 'var(--color-bg-card)',
                    padding: '2.5rem',
                    color: 'var(--color-text-light)',
                }}
            >
                <Typography variant="h6" style={{ color: 'var(--color-text-light)', fontFamily: 'var(--font-role-heading)', fontWeight: 700 }}>
                    SafeLaw Suggestions
                </Typography>
                <Divider style={{ margin: '1.5rem 0', borderColor: 'var(--color-text-inactive)' }} />
                <Stack spacing={3}>
                    {suggestionItems.map((suggestion) => (
                        <Box
                            key={suggestion.title}
                            style={{ borderRadius: '1rem', border: '1px solid var(--color-accent-secondary)', background: 'rgba(255,255,255,0.05)', padding: '1.25rem', fontSize: '1rem', color: 'var(--color-text-light)' }}
                        >
                            <Typography style={{ color: 'var(--color-text-light)', fontSize: '1.1rem' }}>{suggestion.title}</Typography>
                            <Stack
                                direction="row"
                                alignItems="center"
                                justifyContent="space-between"
                                style={{ marginTop: '1rem', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.2em', color: 'var(--color-text-inactive)' }}
                            >
                                <Stack direction="row" spacing={1.5}>
                                    {['Source', 'Insert'].map((action) => (
                                        <Button
                                            key={action}
                                            variant="text"
                                            style={{
                                                color: 'var(--color-accent-secondary)',
                                                fontWeight: 300,
                                                letterSpacing: '0.15em',
                                                textTransform: 'uppercase',
                                                padding: '0.45em 1.2em',
                                                fontFamily: 'var(--font-family-base)',
                                                borderRadius: '999px',
                                                transition: 'all 0.2s',
                                                position: 'relative',
                                                background: 'none',
                                                border: 'none',
                                            }}
                                            onMouseOver={e => {
                                                e.currentTarget.style.color = 'var(--color-accent-secondary-hover)';
                                                e.currentTarget.style.background = 'rgba(255, 140, 71, 0.18)';
                                                e.currentTarget.style.boxShadow = '0 0 12px 2px rgba(255, 140, 71, 0.25)';
                                                e.currentTarget.style.border = '1.5px solid #23272f';
                                            }}
                                            onFocus={e => {
                                                e.currentTarget.style.color = 'var(--color-accent-secondary-hover)';
                                                e.currentTarget.style.background = 'rgba(255, 140, 71, 0.18)';
                                                e.currentTarget.style.boxShadow = '0 0 12px 2px rgba(255, 140, 71, 0.25)';
                                                e.currentTarget.style.border = '1.5px solid #23272f';
                                            }}
                                            onMouseOut={e => {
                                                e.currentTarget.style.color = 'var(--color-accent-secondary)';
                                                e.currentTarget.style.background = 'none';
                                                e.currentTarget.style.boxShadow = 'none';
                                                e.currentTarget.style.border = 'none';
                                            }}
                                            onBlur={e => {
                                                e.currentTarget.style.color = 'var(--color-accent-secondary)';
                                                e.currentTarget.style.background = 'none';
                                                e.currentTarget.style.boxShadow = 'none';
                                                e.currentTarget.style.border = 'none';
                                            }}
                                        >
                                            {action}
                                        </Button>
                                    ))}
                                </Stack>
                                <Chip
                                    label={suggestion.tag}
                                    size="small"
                                    style={{
                                        backgroundColor: 'rgba(0, 140, 153, 0.15)',
                                        color: 'var(--color-accent-primary)',
                                        fontWeight: 600,
                                        letterSpacing: '0.1em',
                                        textTransform: 'uppercase',
                                    }}
                                />
                            </Stack>
                        </Box>
                    ))}
                </Stack>
            </Paper>
        </div>
    </div>
);

export default Writer;
