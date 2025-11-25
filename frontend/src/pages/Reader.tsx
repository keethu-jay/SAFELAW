import { useState, useCallback } from 'react';
import { NavLink } from 'react-router-dom';
import { Box } from '@mui/material';

const Reader = () => {
    const [isDragging, setIsDragging] = useState(false);
    const [droppedFiles, setDroppedFiles] = useState<File[]>([]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDragEnter = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            setDroppedFiles((prev) => [...prev, ...files]);
        }
    }, []);

    const removeFile = (index: number) => {
        setDroppedFiles((prev) => prev.filter((_, i) => i !== index));
    };

    const getFileExtension = (filename: string) => {
        const ext = filename.split('.').pop()?.toUpperCase();
        return ext || 'FILE';
    };

    return (
        <Box sx={{ color: 'var(--color-text-light)', fontFamily: 'var(--font-family-base)' }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                <Box sx={{ background: 'var(--color-bg-card)', borderRadius: '999px', padding: '0.35rem' }}>
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
                </Box>
            </Box>

            {/* Hero Section */}
            <Box
                component="section"
                sx={{
                    background: 'linear-gradient(135deg, #1C2A3D 0%, #091325 100%)',
                    borderRadius: '2rem',
                    padding: '3rem',
                    marginTop: '2rem',
                    textAlign: 'center',
                }}
            >
                <Box
                    sx={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '4rem',
                        height: '4rem',
                        borderRadius: '1rem',
                        background: 'linear-gradient(135deg, #C4623C 0%, #9A4D2F 100%)',
                        marginBottom: '1.5rem',
                    }}
                >
                    <svg
                        width="32"
                        height="32"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="white"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                        <polyline points="10 9 9 9 8 9" />
                    </svg>
                </Box>

                <Box
                    component="h1"
                    sx={{
                        fontFamily: 'var(--font-role-heading)',
                        fontWeight: 700,
                        fontSize: '2.25rem',
                        marginBottom: '1rem',
                        background: 'linear-gradient(90deg, #ffffff 0%, #94a3b8 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                    }}
                >
                    GPTSM Document Summarizer
                </Box>

                <Box
                    component="p"
                    sx={{
                        color: 'var(--color-text-inactive)',
                        fontSize: '1.125rem',
                        maxWidth: '600px',
                        margin: '0 auto',
                        lineHeight: 1.6,
                    }}
                >
                    Powered by AI, GPTSM analyzes your case files and generates concise,
                    actionable summaries. Helping you extract key insights.
                </Box>
            </Box>

            {/* File Upload Section */}
            <Box
                component="section"
                sx={{
                    background: 'var(--color-bg-card)',
                    borderRadius: '2rem',
                    padding: '2.5rem',
                    marginTop: '1.5rem',
                }}
            >
                <Box
                    component="h2"
                    sx={{
                        fontFamily: 'var(--font-role-heading)',
                        fontWeight: 600,
                        fontSize: '1.25rem',
                        marginBottom: '1.25rem',
                    }}
                >
                    Upload Case Files
                </Box>

                {/* File Drop Zone */}
                <Box
                    onDragOver={handleDragOver}
                    onDragEnter={handleDragEnter}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    sx={{
                        border: `2px dashed ${isDragging ? 'var(--color-accent-primary)' : 'rgba(255, 255, 255, 0.2)'}`,
                        borderRadius: '1rem',
                        padding: '3rem 2rem',
                        textAlign: 'center',
                        backgroundColor: isDragging ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.02)',
                        transition: 'all 0.2s ease',
                        cursor: 'pointer',
                    }}
                >
                    <Box sx={{ marginBottom: '1rem' }}>
                        <svg
                            width="48"
                            height="48"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke={isDragging ? 'var(--color-accent-primary)' : 'rgba(255, 255, 255, 0.5)'}
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            style={{ margin: '0 auto', display: 'block' }}
                        >
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="17 8 12 3 7 8" />
                            <line x1="12" y1="3" x2="12" y2="15" />
                        </svg>
                    </Box>
                    <Box
                        component="p"
                        sx={{
                            color: isDragging ? 'var(--color-accent-primary)' : 'var(--color-text-light)',
                            fontWeight: 500,
                            marginBottom: '0.5rem',
                        }}
                    >
                        {isDragging ? 'Drop your files here' : 'Drag & drop case files here'}
                    </Box>
                    <Box
                        component="p"
                        sx={{
                            color: 'var(--color-text-inactive)',
                            fontSize: '0.875rem',
                        }}
                    >
                        Supports PDF, DOCX, HTML, TXT, and more
                    </Box>
                </Box>

                {/* Dropped Files List */}
                {droppedFiles.length > 0 && (
                    <Box sx={{ marginTop: '1.5rem' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                            <Box
                                component="h3"
                                sx={{ fontSize: '1rem', fontWeight: 600 }}
                            >
                                Uploaded Files ({droppedFiles.length})
                            </Box>
                            <Box
                                component="button"
                                sx={{
                                    background: 'var(--color-accent-primary)',
                                    color: 'var(--color-bg-page)',
                                    border: 'none',
                                    borderRadius: '0.5rem',
                                    padding: '0.5rem 1.25rem',
                                    fontWeight: 600,
                                    fontSize: '0.875rem',
                                    cursor: 'pointer',
                                    transition: 'opacity 0.2s',
                                }}
                            >
                                Summarize All
                            </Box>
                        </Box>
                        <Box component="ul" sx={{ listStyle: 'none', padding: 0, margin: 0 }}>
                            {droppedFiles.map((file, index) => (
                                <Box
                                    component="li"
                                    key={`${file.name}-${index}`}
                                    sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        borderRadius: '0.5rem',
                                        padding: '0.75rem 1rem',
                                        marginBottom: '0.5rem',
                                    }}
                                >
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <Box
                                            component="span"
                                            sx={{
                                                background: 'rgba(16, 185, 129, 0.2)',
                                                color: 'var(--color-accent-primary)',
                                                padding: '0.25rem 0.5rem',
                                                borderRadius: '0.25rem',
                                                fontSize: '0.75rem',
                                                fontWeight: 600,
                                                textTransform: 'uppercase',
                                                minWidth: '3rem',
                                                textAlign: 'center',
                                            }}
                                        >
                                            {getFileExtension(file.name)}
                                        </Box>
                                        <Box component="span" sx={{ fontSize: '0.875rem' }}>
                                            {file.name}{' '}
                                            <Box component="span" sx={{ color: 'var(--color-text-inactive)' }}>
                                                ({(file.size / 1024).toFixed(1)} KB)
                                            </Box>
                                        </Box>
                                    </Box>
                                    <Box
                                        component="button"
                                        onClick={() => removeFile(index)}
                                        sx={{
                                            background: 'transparent',
                                            border: 'none',
                                            color: 'var(--color-text-inactive)',
                                            cursor: 'pointer',
                                            padding: '0.25rem',
                                            fontSize: '1.25rem',
                                            lineHeight: 1,
                                        }}
                                        aria-label="Remove file"
                                    >
                                        ×
                                    </Box>
                                </Box>
                            ))}
                        </Box>
                    </Box>
                )}
            </Box>
        </Box>
    );
};

export default Reader;