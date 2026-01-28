import { useState, useCallback, useRef } from 'react';
import { NavLink } from 'react-router-dom';
import { Box } from '@mui/material';
import { useAuth } from '../context/AuthContext';

const Reader = () => {
    const [isDragging, setIsDragging] = useState(false);
    const [droppedFiles, setDroppedFiles] = useState<File[]>([]);
    const [textContent, setTextContent] = useState('');
    const [selectedText, setSelectedText] = useState('');
    const [selectionStart, setSelectionStart] = useState<number | null>(null);
    const [selectionEnd, setSelectionEnd] = useState<number | null>(null);
    const [summarizations, setSummarizations] = useState<Array<{
        start: number;
        end: number;
        originalText: string;
        summarizedText: string;
    }>>([]);
    const [isSummarizing, setIsSummarizing] = useState(false);
    const [editMode, setEditMode] = useState(true);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const contentEditableRef = useRef<HTMLDivElement>(null);
    const { user } = useAuth();

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

    const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setTextContent(e.target.value);
        // Clear selection when text changes
        setSelectedText('');
        setSelectionStart(null);
        setSelectionEnd(null);
        // Clear summarizations when text changes significantly
        if (summarizations.length > 0) {
            setSummarizations([]);
            setEditMode(true);
        }
    };

    const handleTextSelect = () => {
        const textarea = textareaRef.current;
        if (!textarea) return;

        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selected = textarea.value.substring(start, end);

        if (selected.length > 0) {
            setSelectionStart(start);
            setSelectionEnd(end);
            setSelectedText(selected);
        } else {
            setSelectionStart(null);
            setSelectionEnd(null);
            setSelectedText('');
        }
    };

    const handleContentEditableSelect = () => {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
            setSelectedText('');
            setSelectionStart(null);
            setSelectionEnd(null);
            return;
        }

        const range = selection.getRangeAt(0);
        const selectedText_ = range.toString();
        
        if (selectedText_.length > 0) {
            // Calculate start and end positions in the original text
            const preRange = range.cloneRange();
            preRange.selectNodeContents(contentEditableRef.current!);
            preRange.setEnd(range.startContainer, range.startOffset);
            const start = preRange.toString().length;
            const end = start + selectedText_.length;

            setSelectionStart(start);
            setSelectionEnd(end);
            setSelectedText(selectedText_);
        } else {
            setSelectionStart(null);
            setSelectionEnd(null);
            setSelectedText('');
        }
    };

    // Helper function to find highlighted word positions
    const findHighlightedWords = (originalText: string, summarizedText: string): Array<{ start: number; end: number }> => {
        const highlights: Array<{ start: number; end: number }> = [];
        
        // Extract words from both texts (handling punctuation)
        const wordRegex = /\b\w+\b/g;
        const originalMatches = [...originalText.matchAll(wordRegex)];
        const summarizedMatches = [...summarizedText.matchAll(wordRegex)];
        
        // Create a set of summarized words (lowercase for comparison)
        const summarizedWords = new Set(summarizedMatches.map(m => m[0].toLowerCase()));
        
        // Find which original words are in the summarized version
        originalMatches.forEach((match) => {
            const word = match[0];
            const wordLower = word.toLowerCase();
            
            // Check if this word is in the summarized text
            if (summarizedWords.has(wordLower)) {
                highlights.push({
                    start: match.index!,
                    end: match.index! + word.length,
                });
            }
        });
        
        return highlights;
    };

    const handleSummarize = async () => {
        if (!selectedText || !user) {
            alert('Please select text to summarize and ensure you are logged in.');
            return;
        }

        setIsSummarizing(true);
        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/api/summarize-highlight`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: selectedText,
                    user_id: user.id,
                    original_text: textContent,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            
            // Find which words from the summarized text should be highlighted
            const highlightRanges = findHighlightedWords(selectedText, data.summarization);
            
            // Store highlights for each identified word
            if (selectionStart !== null && selectionEnd !== null) {
                // Adjust highlight positions to be relative to the full text
                highlightRanges.forEach((range) => {
                    setSummarizations((prev) => [
                        ...prev,
                        {
                            start: selectionStart + range.start,
                            end: selectionStart + range.end,
                            originalText: selectedText.substring(range.start, range.end),
                            summarizedText: data.summarization,
                        },
                    ]);
                });
                // Switch to view mode to see highlights
                setEditMode(false);
            }

            // Clear selection after summarization
            setSelectedText('');
            setSelectionStart(null);
            setSelectionEnd(null);
        } catch (error) {
            console.error('Error summarizing text:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to summarize text. Please check that the backend server is running and the database table exists.';
            alert(`Error: ${errorMessage}`);
        } finally {
            setIsSummarizing(false);
        }
    };

    // Render text with highlights
    const renderTextWithHighlights = () => {
        if (!textContent) return null;

        // Sort summarizations by start position
        const sortedSummarizations = [...summarizations].sort((a, b) => a.start - b.start);
        
        // Create array of text segments with their highlight status
        const segments: Array<{ text: string; isHighlighted: boolean }> = [];
        let lastIndex = 0;

        sortedSummarizations.forEach((summ) => {
            // Add text before highlight
            if (summ.start > lastIndex) {
                segments.push({
                    text: textContent.substring(lastIndex, summ.start),
                    isHighlighted: false,
                });
            }
            // Add highlighted text
            segments.push({
                text: textContent.substring(summ.start, summ.end),
                isHighlighted: true,
            });
            lastIndex = summ.end;
        });

        // Add remaining text
        if (lastIndex < textContent.length) {
            segments.push({
                text: textContent.substring(lastIndex),
                isHighlighted: false,
            });
        }

        return segments.map((segment, index) => (
            <span
                key={index}
                style={{
                    backgroundColor: segment.isHighlighted ? '#FF8C42' : 'transparent',
                    color: segment.isHighlighted ? '#000' : 'inherit',
                }}
            >
                {segment.text}
            </span>
        ));
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

            {/* Text Input and Highlighting Section */}
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
                    Text Summarization
                </Box>

                <Box
                    component="p"
                    sx={{
                        color: 'var(--color-text-inactive)',
                        fontSize: '0.875rem',
                        marginBottom: '1.5rem',
                    }}
                >
                    Paste your text below, highlight the text you want to summarize, and click the summarize button.
                    Summarized text will appear highlighted in orange.
                </Box>

                {/* Mode Toggle */}
                {summarizations.length > 0 && (
                    <Box sx={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                        <Box
                            component="button"
                            onClick={() => setEditMode(true)}
                            sx={{
                                padding: '0.5rem 1rem',
                                background: editMode ? 'var(--color-accent-primary)' : 'rgba(255, 255, 255, 0.1)',
                                color: editMode ? 'var(--color-bg-page)' : 'var(--color-text-light)',
                                border: 'none',
                                borderRadius: '0.5rem',
                                cursor: 'pointer',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                            }}
                        >
                            Edit Mode
                        </Box>
                        <Box
                            component="button"
                            onClick={() => setEditMode(false)}
                            sx={{
                                padding: '0.5rem 1rem',
                                background: !editMode ? 'var(--color-accent-primary)' : 'rgba(255, 255, 255, 0.1)',
                                color: !editMode ? 'var(--color-bg-page)' : 'var(--color-text-light)',
                                border: 'none',
                                borderRadius: '0.5rem',
                                cursor: 'pointer',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                            }}
                        >
                            View Highlights
                        </Box>
                    </Box>
                )}

                {/* Text Display Area with Highlights */}
                <Box
                    sx={{
                        position: 'relative',
                        marginBottom: '1rem',
                    }}
                >
                    {/* View Mode: ContentEditable with highlights */}
                    {!editMode && summarizations.length > 0 ? (
                        <Box
                            component="div"
                            ref={contentEditableRef}
                            contentEditable={false}
                            onMouseUp={handleContentEditableSelect}
                            onKeyUp={handleContentEditableSelect}
                            suppressContentEditableWarning
                            sx={{
                                minHeight: '200px',
                                maxHeight: '400px',
                                overflow: 'auto',
                                padding: '1rem',
                                background: 'rgba(255, 255, 255, 0.05)',
                                borderRadius: '0.5rem',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                whiteSpace: 'pre-wrap',
                                wordWrap: 'break-word',
                                fontFamily: 'monospace',
                                fontSize: '0.875rem',
                                lineHeight: 1.6,
                                color: 'var(--color-text-light)',
                                cursor: 'text',
                                '&::selection': {
                                    backgroundColor: 'rgba(100, 100, 100, 0.5)',
                                    color: 'var(--color-text-light)',
                                },
                            }}
                        >
                            {renderTextWithHighlights()}
                        </Box>
                    ) : (
                        /* Edit Mode: Textarea for input and selection */
                        <Box
                            component="textarea"
                            ref={textareaRef}
                            value={textContent}
                            onChange={handleTextChange}
                            onSelect={handleTextSelect}
                            onMouseUp={handleTextSelect}
                            onKeyUp={handleTextSelect}
                            placeholder="Paste or type your text here, then highlight the text you want to summarize..."
                            sx={{
                                width: '100%',
                                minHeight: '200px',
                                maxHeight: '400px',
                                padding: '1rem',
                                background: 'rgba(255, 255, 255, 0.05)',
                                borderRadius: '0.5rem',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                color: 'var(--color-text-light)',
                                fontFamily: 'monospace',
                                fontSize: '0.875rem',
                                lineHeight: 1.6,
                                resize: 'vertical',
                                outline: 'none',
                                '&::selection': {
                                    backgroundColor: 'rgba(100, 100, 100, 0.5)', // Darker grey for selection
                                    color: 'var(--color-text-light)',
                                },
                                '&:focus': {
                                    borderColor: 'var(--color-accent-primary)',
                                },
                            }}
                        />
                    )}
                </Box>

                {/* Selection Info and Summarize Button */}
                {selectedText && (
                    <Box
                        sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: '1rem',
                            marginBottom: '1rem',
                            padding: '1rem',
                            background: 'rgba(255, 255, 255, 0.03)',
                            borderRadius: '0.5rem',
                        }}
                    >
                        <Box sx={{ flex: 1 }}>
                            <Box
                                component="p"
                                sx={{
                                    fontSize: '0.875rem',
                                    color: 'var(--color-text-inactive)',
                                    marginBottom: '0.25rem',
                                }}
                            >
                                Selected text ({selectedText.length} characters):
                            </Box>
                            <Box
                                component="p"
                                sx={{
                                    fontSize: '0.75rem',
                                    color: 'var(--color-text-light)',
                                    fontStyle: 'italic',
                                    maxHeight: '3rem',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                }}
                            >
                                "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"
                            </Box>
                        </Box>
                        <Box
                            component="button"
                            onClick={handleSummarize}
                            disabled={isSummarizing || !selectedText}
                            sx={{
                                background: isSummarizing || !selectedText 
                                    ? 'rgba(196, 98, 60, 0.5)' 
                                    : 'var(--color-accent-primary)',
                                color: 'var(--color-bg-page)',
                                border: 'none',
                                borderRadius: '0.5rem',
                                padding: '0.75rem 1.5rem',
                                fontWeight: 600,
                                fontSize: '0.875rem',
                                cursor: isSummarizing || !selectedText ? 'not-allowed' : 'pointer',
                                transition: 'opacity 0.2s',
                                '&:hover': {
                                    opacity: isSummarizing || !selectedText ? 1 : 0.9,
                                },
                            }}
                        >
                            {isSummarizing ? 'Summarizing...' : 'Summarize Highlighted Text'}
                        </Box>
                    </Box>
                )}

                {/* Instructions */}
                {!selectedText && (
                    <Box
                        sx={{
                            padding: '1rem',
                            background: 'rgba(255, 255, 255, 0.02)',
                            borderRadius: '0.5rem',
                            border: '1px dashed rgba(255, 255, 255, 0.1)',
                        }}
                    >
                        <Box
                            component="p"
                            sx={{
                                fontSize: '0.875rem',
                                color: 'var(--color-text-inactive)',
                                margin: 0,
                            }}
                        >
                            💡 Tip: Select text in the text area above to highlight it for summarization. 
                            The selection will appear in a darker grey color.
                        </Box>
                    </Box>
                )}
            </Box>
        </Box>
    );
};

export default Reader;