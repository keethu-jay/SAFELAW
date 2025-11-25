import { useMemo, useState } from 'react';
import { Box, Button, Chip, Divider, Paper, Stack, Typography } from '@mui/material';
import { NavLink } from 'react-router-dom';

type JudgmentType = 'majority' | 'dissenting' | 'concurring';
type CourtLevel = 'supreme' | 'tribunal';

type Suggestion = {
    title: string;
    similarity: number;
    citation: string;
    judgment: JudgmentType;
};

type SimilarityLegendItem = {
    label: string;
    range: string;
    className: string;
};

const supremeSuggestions: Suggestion[] = [
    {
        title: 'The claimant’s unjust enrichment theory mirrors the reasoning in Cobbe v Yeoman’s Row Management Ltd.',
        similarity: 92,
        citation: '[2008] UKHL 55',
        judgment: 'majority',
    },
    {
        title: 'Disclosure shows a fiduciary breach comparable to FHR European Ventures LLP v Cedar Capital Partners LLC.',
        similarity: 85,
        citation: '[2014] UKSC 45',
        judgment: 'majority',
    },
    {
        title: 'Failure to act with candour reflects the criticism in R (Citizens UK) v Secretary of State for the Home Department.',
        similarity: 78,
        citation: '[2018] EWCA Civ 1812',
        judgment: 'concurring',
    },
    {
        title: 'The dissent in R (Miller) v The Prime Minister highlights limits on prerogative power where accountability is reduced.',
        similarity: 74,
        citation: '[2019] UKSC 41',
        judgment: 'dissenting',
    },
    {
        title: 'American Cyanamid Co v Ethicon Ltd confirms interim relief where balance of convenience tilts towards preservation.',
        similarity: 57,
        citation: '[1975] UKHL 1',
        judgment: 'concurring',
    },
    {
        title: 'Lord Carnwath’s dissent in R (Keyu) v Secretary of State illustrates remittal where discretion is fettered.',
        similarity: 34,
        citation: '[2015] UKSC 69',
        judgment: 'dissenting',
    },
    {
        title: 'Perry v Raleys Solicitors underscores the evidential weight of contemporaneous notes in professional negligence claims.',
        similarity: 68,
        citation: '[2019] UKSC 5',
        judgment: 'majority',
    },
    {
        title: 'Serious Fraud Office v ENRC shows that staggered disclosure can evidence bad faith in corporate investigations.',
        similarity: 48,
        citation: '[2018] EWCA Civ 2006',
        judgment: 'concurring',
    },
    {
        title: 'In R (Begum) v Special Immigration Appeals Commission the Court stressed proportionality when national security is invoked.',
        similarity: 29,
        citation: '[2021] UKSC 7',
        judgment: 'dissenting',
    },
];

const tribunalSuggestions: Suggestion[] = [
    {
        title: 'Tribunal awards of aggravated damages track Khan v Information Commissioner where interference was deliberate.',
        similarity: 63,
        citation: '[2016] UKUT 486 (AAC)',
        judgment: 'majority',
    },
    {
        title: 'The Investigatory Powers Tribunal in Privacy International v Secretary of State required heightened proportionality for targeted warrants.',
        similarity: 76,
        citation: '[2021] UKIP Trib 2 (IPT)',
        judgment: 'majority',
    },
    {
        title: 'FTT (Tax) panels since 2022 emphasise contemporaneous ledgers when challenging VAT assessments on honest traders.',
        similarity: 55,
        citation: '[2023] UKFTT 211 (TC)',
        judgment: 'concurring',
    },
    {
        title: 'The Employment Appeal Tribunal found that staged disclosures justify punitive uplifts under s.207A TULRCA where mala fides is shown.',
        similarity: 46,
        citation: '[2022] UKEAT 0138_21_1409',
        judgment: 'dissenting',
    },
    {
        title: 'The Lands Chamber reiterated that expert diaries are determinative during compulsory purchase compensation reviews.',
        similarity: 37,
        citation: '[2023] UKUT 289 (LC)',
        judgment: 'concurring',
    },
];

const similarityLegend: SimilarityLegendItem[] = [
    { label: 'Very Low', range: '0-20%', className: 'very-low' },
    { label: 'Low', range: '21-40%', className: 'low' },
    { label: 'Moderate', range: '41-60%', className: 'moderate' },
    { label: 'High', range: '61-80%', className: 'high' },
    { label: 'Very High', range: '81-100%', className: 'very-high' },
];

const getSimilarityClass = (score: number) => {
    if (score <= 20) return 'very-low';
    if (score <= 40) return 'low';
    if (score <= 60) return 'moderate';
    if (score <= 80) return 'high';
    return 'very-high';
};

const DEFAULT_TEXT = `WHEREAS, the Plaintiff, John Doe, asserts a claim for breach of contract against the Defendant, Acme Corporation, stemming from a purported failure to deliver services as outlined in the agreement dated January 15, 2023...`;

const Writer = () => {
    const [draftText, setDraftText] = useState(DEFAULT_TEXT);
    const [judgmentFilter, setJudgmentFilter] = useState<JudgmentType | 'all'>('all');
    const [filterOpen, setFilterOpen] = useState(false);
    const [legendOpen, setLegendOpen] = useState(false);
    const [courtLevel, setCourtLevel] = useState<CourtLevel>('supreme');

    const filteredSuggestions = useMemo(() => {
        const pool = courtLevel === 'supreme' ? supremeSuggestions : tribunalSuggestions;
        return judgmentFilter === 'all' ? pool : pool.filter((item) => item.judgment === judgmentFilter);
    }, [courtLevel, judgmentFilter]);

    const handleInsert = (suggestion: Suggestion) => {
        setDraftText((current) => `${current.trim()}\n\n${suggestion.title} (${suggestion.citation})`);
    };

    return (
    <div style={{ color: 'var(--color-text-light)', fontFamily: 'var(--font-family-base)' }}>
        <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{ background: 'var(--color-bg-card)', borderRadius: '999px', padding: '0.8rem 0.5rem' }}>
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
                        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                            <div>
                                <p style={{ textTransform: 'uppercase', letterSpacing: '0.4em', color: 'var(--color-accent-primary)', fontSize: '1rem', marginBottom: '0.75rem' }}>Draft Court Opinion</p>
                                <Typography variant="h4" style={{ fontFamily: 'var(--font-role-heading)', fontWeight: 700, color: 'var(--color-text-light)' }}>
                                    Judgment for Case of The Crown v. Acme Corp.
                                </Typography>
                            </div>
                            <div style={{ display: 'flex', gap: '0.4rem', background: 'rgba(255,255,255,0.08)', borderRadius: '999px', padding: '0.2rem' }}>
                                {(['supreme', 'tribunal'] as CourtLevel[]).map((level) => (
                                    <button
                                        key={level}
                                        type="button"
                                        onClick={() => setCourtLevel(level)}
                                        style={{
                                            border: 'none',
                                            borderRadius: '999px',
                                            padding: '0.4rem 1.3rem',
                                            textTransform: 'uppercase',
                                            letterSpacing: '0.25em',
                                            fontSize: '0.7rem',
                                            cursor: 'pointer',
                                            background: courtLevel === level ? 'rgba(0, 140, 153, 0.25)' : 'transparent',
                                            color: courtLevel === level ? 'var(--color-accent-primary)' : 'var(--color-text-light)',
                                            fontFamily: 'var(--font-role-body)',
                                        }}
                                    >
                                        {level}
                                    </button>
                                ))}
                            </div>
                        </div>
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
                        value={draftText}
                        onChange={(event) => setDraftText(event.target.value)}
                        style={{
                            minHeight: '360px',
                            width: '100%',
                            resize: 'none',
                            borderRadius: '1.5rem',
                            background: 'var(--color-bg-page)',
                            padding: '1.5rem',
                            fontSize: '1.1rem',
                            color: 'var(--color-text-dark)',
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
                <div style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: '1.25rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', marginTop: '1rem' }}>
                    <button
                        type="button"
                        onClick={() => setFilterOpen((open) => !open)}
                        style={{
                            width: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            border: 'none',
                            background: 'transparent',
                            color: 'var(--color-text-light)',
                            textTransform: 'uppercase',
                            letterSpacing: '0.3em',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            fontFamily: 'var(--font-role-body)',
                            cursor: 'pointer',
                        }}
                    >
                        Judgment Filter
                        <span style={{ fontSize: '0.65rem', color: 'var(--color-text-inactive)' }}>
                            {filterOpen ? 'Hide' : 'Show'} ({judgmentFilter})
                        </span>
                    </button>
                    {filterOpen && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.85rem' }}>
                            {['all', 'majority', 'dissenting', 'concurring'].map((type) => (
                                <button
                                    key={type}
                                    type="button"
                                    onClick={() => setJudgmentFilter(type as JudgmentType | 'all')}
                                    style={{
                                        padding: '0.45rem 1.3rem',
                                        borderRadius: '999px',
                                        border: '1px solid rgba(255,255,255,0.15)',
                                        background:
                                            judgmentFilter === type
                                                ? 'rgba(0, 140, 153, 0.2)'
                                                : 'rgba(255,255,255,0.05)',
                                        color: 'var(--color-text-light)',
                                        letterSpacing: '0.25em',
                                        fontSize: '0.7rem',
                                        textTransform: 'uppercase',
                                        fontFamily: 'var(--font-role-body)',
                                        cursor: 'pointer',
                                        boxShadow:
                                            judgmentFilter === type
                                                ? '0 0 12px rgba(0,140,153,0.35)'
                                                : 'none',
                                    }}
                                >
                                    {type}
                                </button>
                            ))}
                        </div>
                    )}
                    <div style={{ marginTop: '1rem' }}>
                        <button
                            type="button"
                            onClick={() => setLegendOpen((open) => !open)}
                            style={{
                                width: '100%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                border: 'none',
                                background: 'transparent',
                                color: 'var(--color-text-light)',
                                textTransform: 'uppercase',
                                letterSpacing: '0.3em',
                                fontSize: '0.7rem',
                                fontWeight: 600,
                                fontFamily: 'var(--font-role-body)',
                                cursor: 'pointer',
                            }}
                        >
                            Similarity Key
                            <span style={{ fontSize: '0.6rem', color: 'var(--color-text-inactive)' }}>
                                {legendOpen ? 'Hide' : 'Show'}
                            </span>
                        </button>
                        {legendOpen && (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.6rem', marginTop: '0.75rem' }}>
                                {similarityLegend.map((legend) => (
                                    <div
                                        key={legend.label}
                                        style={{
                                            border: '1px solid rgba(255,255,255,0.08)',
                                            borderRadius: '1rem',
                                            padding: '0.75rem',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            gap: '0.3rem',
                                            background: 'rgba(255,255,255,0.03)',
                                        }}
                                    >
                                        <span className={`similarity-pill ${legend.className}`}>{legend.label}</span>
                                        <span
                                            style={{
                                                fontSize: '0.65rem',
                                                textTransform: 'uppercase',
                                                letterSpacing: '0.3em',
                                                color: 'var(--color-text-inactive)',
                                            }}
                                        >
                                            {legend.range}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
                <Divider style={{ margin: '1.5rem 0', borderColor: 'var(--color-text-inactive)' }} />
                <div style={{ maxHeight: '28rem', overflowY: 'auto', paddingRight: '0.5rem' }}>
                    <Stack spacing={3}>
                        {filteredSuggestions.map((suggestion) => (
                            <Box
                                key={suggestion.title}
                                style={{ borderRadius: '1rem', border: '1px solid var(--color-accent-secondary)', background: 'rgba(255,255,255,0.05)', padding: '1.25rem', fontSize: '1rem', color: 'var(--color-text-light)' }}
                            >
                                <Typography style={{ color: 'var(--color-text-light)', fontFamily: 'var(--font-role-body)', fontSize: '1.1rem' }}>{suggestion.title}</Typography>
                                <Stack
                                    direction="row"
                                    alignItems="center"
                                    justifyContent="space-between"
                                    style={{ marginTop: '1rem', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.2em', color: 'var(--color-text-inactive)' }}
                                >
                                    <Stack direction="row" spacing={1.5}>
                                        <Button
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
                                        >
                                            Source
                                        </Button>
                                        <Button
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
                                            onClick={() => handleInsert(suggestion)}
                                        >
                                            Insert
                                        </Button>
                                    </Stack>
                                    <Chip
                                        label={`Similarity ${suggestion.similarity}%`}
                                        size="small"
                                        className={`similarity-pill ${getSimilarityClass(suggestion.similarity)}`}
                                    />
                                </Stack>
                            </Box>
                        ))}
                    </Stack>
                </div>
            </Paper>
        </div>
    </div>
    );
};

export default Writer;
