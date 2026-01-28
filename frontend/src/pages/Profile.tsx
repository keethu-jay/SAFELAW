import React, { useState, useEffect } from 'react';
import { Box, Paper, Stack, Typography, Divider, Button, CircularProgress } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import LogoutIcon from '@mui/icons-material/Logout';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabaseClient';

// Helper function to format relative time
const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
    if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    if (diffInSeconds < 604800) {
        const days = Math.floor(diffInSeconds / 86400);
        if (days === 1) return 'Yesterday';
        return `${days} days ago`;
    }
    if (diffInSeconds < 2592000) {
        const weeks = Math.floor(diffInSeconds / 604800);
        return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
    }
    const months = Math.floor(diffInSeconds / 2592000);
    return `${months} month${months > 1 ? 's' : ''} ago`;
};

interface ProfileData {
    full_name: string | null;
    role: string | null;
}

interface ActivityItem {
    id: string;
    file: string;
    time: string;
    type: string;
}

interface DocumentItem {
    id: string;
    name: string;
    opened: string;
}

interface ProcessingItem {
    id: string;
    name: string;
    status: string;
    progress: number;
}

const Profile: React.FC = () => {
    const { logout, user } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [profileData, setProfileData] = useState<ProfileData>({ full_name: null, role: null });
    const [lastEdits, setLastEdits] = useState<ActivityItem[]>([]);
    const [lastOpenedFiles, setLastOpenedFiles] = useState<DocumentItem[]>([]);
    const [filesInProcessing, setFilesInProcessing] = useState<ProcessingItem[]>([]);
    const [userEmail, setUserEmail] = useState<string>('');

    useEffect(() => {
        const fetchProfileData = async () => {
            if (!user) {
                setLoading(false);
                return;
            }

            try {
                setUserEmail(user.email || '');

                // Fetch user profile
                const { data: profile, error: profileError } = await supabase
                    .from('profiles')
                    .select('full_name, role')
                    .eq('id', user.id)
                    .single();

                if (profileError) {
                    console.error('Error fetching profile:', profileError);
                } else {
                    setProfileData({
                        full_name: profile?.full_name || 'User',
                        role: profile?.role || 'Legal User',
                    });
                }

                // Fetch recent activity (last edits)
                const { data: activities, error: activitiesError } = await supabase
                    .from('user_activity')
                    .select('id, action_type, document_name, description, created_at')
                    .eq('user_id', user.id)
                    .order('created_at', { ascending: false })
                    .limit(5);

                if (!activitiesError && activities) {
                    setLastEdits(
                        activities
                            .filter((a) => a.action_type === 'EDIT' || a.action_type === 'CREATE')
                            .map((a) => ({
                                id: a.id,
                                file: a.document_name || a.description || 'Untitled Document',
                                time: formatRelativeTime(a.created_at),
                                type: a.action_type,
                            }))
                    );
                }

                // Fetch last opened files (recent documents)
                const { data: documents, error: documentsError } = await supabase
                    .from('documents')
                    .select('id, title, updated_at')
                    .eq('owner_id', user.id)
                    .order('updated_at', { ascending: false })
                    .limit(5);

                if (!documentsError && documents) {
                    setLastOpenedFiles(
                        documents.map((doc) => ({
                            id: doc.id,
                            name: doc.title || 'Untitled Document',
                            opened: formatRelativeTime(doc.updated_at),
                        }))
                    );
                }

                // Fetch files in processing
                // First get user's documents
                const { data: userDocuments } = await supabase
                    .from('documents')
                    .select('id')
                    .eq('owner_id', user.id);

                if (userDocuments && userDocuments.length > 0) {
                    const documentIds = userDocuments.map((doc) => doc.id);
                    const { data: processing, error: processingError } = await supabase
                        .from('processing_queue')
                        .select('id, document_id, status, progress_percent, time_estimate')
                        .in('document_id', documentIds)
                        .in('status', ['queued', 'processing'])
                        .order('created_at', { ascending: false })
                        .limit(5);

                    if (!processingError && processing) {
                        // Get document titles
                        const docIds = processing.map((p) => p.document_id);
                        const { data: docs } = await supabase
                            .from('documents')
                            .select('id, title')
                            .in('id', docIds);

                        const docMap = new Map(docs?.map((d) => [d.id, d.title]) || []);

                        setFilesInProcessing(
                            processing.map((item) => ({
                                id: item.id,
                                name: docMap.get(item.document_id) || 'Untitled Document',
                                status: item.status.charAt(0).toUpperCase() + item.status.slice(1),
                                progress: item.progress_percent || 0,
                            }))
                        );
                    }
                }
            } catch (error) {
                console.error('Error fetching profile data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchProfileData();
    }, [user]);

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    if (loading) {
        return (
            <Box
                sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    minHeight: '400px',
                    color: 'var(--color-text-light)',
                }}
            >
                <CircularProgress sx={{ color: 'var(--color-accent-primary)' }} />
            </Box>
        );
    }

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
                                {profileData.full_name || 'User'}
                            </Typography>
                            <Typography
                                style={{
                                    color: 'var(--color-text-inactive)',
                                    fontSize: '0.9rem',
                                    letterSpacing: '0.1em',
                                    textTransform: 'uppercase',
                                }}
                            >
                                {profileData.role || 'Legal User'}
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
                                {lastEdits.length === 0 ? (
                                    <Typography
                                        style={{
                                            color: 'var(--color-text-inactive)',
                                            fontSize: '0.875rem',
                                            fontStyle: 'italic',
                                        }}
                                    >
                                        No recent edits
                                    </Typography>
                                ) : (
                                    lastEdits.map((edit) => (
                                        <Box
                                            key={edit.id}
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
                                    ))
                                )}
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
                                {lastOpenedFiles.length === 0 ? (
                                    <Typography
                                        style={{
                                            color: 'var(--color-text-inactive)',
                                            fontSize: '0.875rem',
                                            fontStyle: 'italic',
                                        }}
                                    >
                                        No documents opened yet
                                    </Typography>
                                ) : (
                                    lastOpenedFiles.map((file) => (
                                        <Box
                                            key={file.id}
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
                                    ))
                                )}
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
                                {filesInProcessing.length === 0 ? (
                                    <Typography
                                        style={{
                                            color: 'var(--color-text-inactive)',
                                            fontSize: '0.875rem',
                                            fontStyle: 'italic',
                                        }}
                                    >
                                        No files currently processing
                                    </Typography>
                                ) : (
                                    filesInProcessing.map((file) => (
                                        <Box
                                            key={file.id}
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
                                    ))
                                )}
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
                                {profileData.role || 'Legal User'}
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
                                Member Since
                            </Typography>
                            <Typography
                                style={{
                                    color: 'var(--color-text-light)',
                                    fontFamily: 'var(--font-role-body)',
                                }}
                            >
                                {user?.created_at ? formatRelativeTime(user.created_at) : 'Recently'}
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
                                {userEmail || 'No email available'}
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
