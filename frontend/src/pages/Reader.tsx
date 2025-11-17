import { NavLink } from 'react-router-dom';

const Reader = () => (
    <div className="space-y-6 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="safelaw-subnav">
                {[
                    { label: 'Writing', href: '/writer' },
                    { label: 'Reading', href: '/reader' },
                ].map((tab) => (
                    <NavLink key={tab.href} to={tab.href} className={({ isActive }) => (isActive ? 'active' : undefined)}>
                        {tab.label}
                    </NavLink>
                ))}
            </div>
        </div>

        <section className="safelaw-surface safelaw-gradient p-8">
            <h1 className="safelaw-heading text-3xl font-semibold mb-4">Reading Workspace</h1>
            <p className="text-slate-200">
                GP-TSM plug-in here, add drag-and-drop functionality for case bundles and highlight chains.
            </p>
        </section>
    </div>
);

export default Reader;
