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
    <div className="space-y-6 text-white">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="safelaw-subnav">
                {[
                    { label: 'Writing', href: '/writer' },
                    { label: 'Reading', href: '/reader' },
                ].map((tab) => (
                    <NavLink
                        key={tab.href}
                        to={tab.href}
                        className={({ isActive }) => (isActive ? 'active' : undefined)}
                    >
                        {tab.label}
                    </NavLink>
                ))}
            </div>
         
        </div>

        <div className="grid gap-8 grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)] max-sm:flex max-sm:flex-col">
            <Paper
                elevation={8}
                className="border border-white/5 bg-gradient-to-br from-[#0f172a] via-[#101f31] to-[#0b1424]"
                sx={{ borderRadius: '30px', padding: { xs: '24px', md: '40px' } }}
            >
                <Stack spacing={4}>
                    <div>
                        <p className="text-sm uppercase tracking-[0.4em] text-emerald-300">Draft Legal Brief</p>
                        <Typography variant="h4" className="font-semibold text-white">
                            Case of John Doe v. Acme Corp.
                        </Typography>
                    </div>

                    <Divider className="border-white/10" />

                    <Stack direction="row" spacing={1}>
                        {['B', 'I', 'U'].map((icon) => (
                            <Button
                                key={icon}
                                variant="outlined"
                                size="small"
                                sx={{
                                    color: '#a7b9d6',
                                    borderColor: 'rgba(255,255,255,0.15)',
                                    minWidth: '44px',
                                    borderRadius: '12px',
                                    fontWeight: 700,
                                }}
                            >
                                {icon}
                            </Button>
                        ))}
                    </Stack>

                    <Box
                        component="textarea"
                        defaultValue={`WHEREAS, the Plaintiff, John Doe, asserts a claim for breach of contract against the Defendant, Acme Corporation, stemming from a purported failure to deliver services as outlined in the agreement dated January 15, 2023...`}
                        className="min-h-[360px] w-full resize-none rounded-3xl bg-[#050d18]/80 p-6 text-base leading-relaxed text-slate-200 outline-none ring-1 ring-inset ring-white/5 focus:ring-2 focus:ring-emerald-400"
                    />

                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="flex-end">
                        <Button
                            variant="outlined"
                            className="border-emerald-400/60 text-emerald-300"
                            sx={{
                                borderRadius: '999px',
                                px: 4,
                                py: 1.5,
                                borderWidth: 2,
                                textTransform: 'none',
                                fontWeight: 600,
                            }}
                        >
                            Save Draft
                        </Button>
                        <Button
                            variant="contained"
                            className="bg-emerald-400"
                            sx={{
                                borderRadius: '999px',
                                px: 4,
                                py: 1.5,
                                fontWeight: 700,
                                textTransform: 'none',
                                backgroundColor: '#2dd4bf',
                                color: '#042f2e',
                                '&:hover': { backgroundColor: '#14b8a6' },
                            }}
                        >
                            Export Document
                        </Button>
                    </Stack>
                </Stack>
            </Paper>

            <Paper
                elevation={8}
                className="border border-white/5 bg-[#0d1726]"
                sx={{ borderRadius: '30px', padding: { xs: '24px', md: '32px' } }}
            >
                <Typography variant="h6" className="text-white">
                    SafeLaw Suggestions
                </Typography>
                <Divider className="my-4 border-white/10" />
                <Stack spacing={3}>
                    {suggestionItems.map((suggestion) => (
                        <Box
                            key={suggestion.title}
                            className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm leading-relaxed text-slate-200"
                        >
                            <Typography className="text-base text-white">{suggestion.title}</Typography>
                            <Stack
                                direction="row"
                                alignItems="center"
                                justifyContent="space-between"
                                className="mt-4 text-xs uppercase tracking-[0.3em] text-slate-400"
                            >
                                <Stack direction="row" spacing={1.5}>
                                    {['Source', 'Insert'].map((action) => (
                                        <Button
                                            key={action}
                                            variant="text"
                                            sx={{
                                                color: '#6ee7b7',
                                                fontWeight: 700,
                                                letterSpacing: '0.25em',
                                                textTransform: 'uppercase',
                                                paddingX: 0,
                                            }}
                                        >
                                            {action}
                                        </Button>
                                    ))}
                                </Stack>
                                <Chip
                                    label={suggestion.tag}
                                    size="small"
                                    sx={{
                                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                                        color: '#6ee7b7',
                                        fontWeight: 600,
                                        letterSpacing: '0.2em',
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
