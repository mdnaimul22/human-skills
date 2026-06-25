import { useState, useRef, useCallback, useEffect } from 'react';
import { ThemeProvider } from '@/components/layout/theme-provider';
import { UserMenu } from '@/components/layout/user-menu';
import {
  LayoutDashboard,
  Star,
  X,
  Shield,
  Globe,
  Terminal,
  RefreshCw,
  Minus,
  Maximize2,
  Minimize2
} from 'lucide-react';

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      <PanelContent />
    </ThemeProvider>
  );
}

/* ── Sidebar nav items ─────────────────────────────────────── */
const NAV_ITEMS = [
  { id: 'service-1', label: 'Service 1', icon: LayoutDashboard },
  { id: 'service-2', label: 'Service 2', icon: Globe },
  { id: 'service-3', label: 'Service 3', icon: Star },
] as const;

type NavId = (typeof NAV_ITEMS)[number]['id'];

/* ── Panel Content ─────────────────────────────────────────── */
function PanelContent() {
  const [activeNav, setActiveNav] = useState<NavId>('service-1');

  // Sidebar Collapse State
  const [isCollapsed, setIsCollapsed] = useState(() => {
    try { return localStorage.getItem('ext-sidebar-collapsed') === 'true'; } catch { return false; }
  });
  
  // Floating Window State
  const [isMaximized, setIsMaximized] = useState(false);
  const [viewMode, setViewMode] = useState<'normal' | 'bubble' | 'sidebar-only'>('normal');
  const [bounds, setBounds] = useState({
    x: 20,
    y: 20,
    width: 1000,
    height: 700
  });

  const windowRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const dragMoved = useRef(false);
  const isResizing = useRef(false);

  // Helper: calculate bottom-left default position
  const getDefaultPosition = (_w: number, h: number) => ({
    x: 0,
    y: window.innerHeight - h,
  });

  // Initialize bounds on first load
  useEffect(() => {
    const w = Math.min(1000, window.innerWidth - 100);
    const h = Math.min(700, window.innerHeight - 100);
    const pos = getDefaultPosition(w, h);
    setBounds({
      x: pos.x,
      y: pos.y,
      width: w,
      height: h
    });
  }, []);

  const toggleCollapse = () => {
    setIsCollapsed(c => {
      const next = !c;
      try { localStorage.setItem('ext-sidebar-collapsed', String(next)); } catch {}
      return next;
    });
  };


  const handleSidebarToggle = () => {
    if (viewMode === 'sidebar-only') {
      // Reset position to bottom-left default when restoring
      setBounds(prev => ({ ...prev, ...getDefaultPosition(prev.width, prev.height) }));
      setViewMode('normal');
      setIsCollapsed(false);
    } else {
      toggleCollapse();
    }
  };

  /* ── Drag & Resize Handlers ──────────────────────────────── */
  const handleHeaderMouseDown = useCallback((e: React.MouseEvent) => {
    if (isMaximized) return;
    e.preventDefault();
    isDragging.current = true;
    dragMoved.current = false;
    
    const startX = e.clientX;
    const startY = e.clientY;
    const startLeft = bounds.x;
    const startTop = bounds.y;

    document.body.style.userSelect = 'none';

    function onMouseMove(ev: MouseEvent) {
      if (!isDragging.current) return;
      dragMoved.current = true;
      setBounds(prev => ({
        ...prev,
        x: startLeft + (ev.clientX - startX),
        y: Math.max(0, startTop + (ev.clientY - startY)) // Prevent dragging above screen
      }));
    }

    function onMouseUp() {
      isDragging.current = false;
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, [bounds, isMaximized]);

  const handleResizeMouseDown = useCallback((e: React.MouseEvent, direction: 'right' | 'bottom' | 'br') => {
    if (isMaximized) return;
    e.preventDefault();
    e.stopPropagation();
    isResizing.current = true;
    
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = bounds.width;
    const startHeight = bounds.height;

    document.body.style.userSelect = 'none';
    if (direction === 'right') document.body.style.cursor = 'col-resize';
    if (direction === 'bottom') document.body.style.cursor = 'row-resize';
    if (direction === 'br') document.body.style.cursor = 'nwse-resize';

    function onMouseMove(ev: MouseEvent) {
      if (!isResizing.current) return;
      setBounds(prev => ({
        ...prev,
        width: direction.includes('right') || direction === 'br' ? Math.max(400, startWidth + (ev.clientX - startX)) : prev.width,
        height: direction.includes('bottom') || direction === 'br' ? Math.max(300, startHeight + (ev.clientY - startY)) : prev.height,
      }));
    }

    function onMouseUp() {
      isResizing.current = false;
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, [bounds, isMaximized]);


  if (viewMode === 'bubble') {
    // Bubble sits at bottom-center by default
    const bubbleX = (window.innerWidth / 2) - 18; // 18 = half of 36px (w-9)
    const bubbleY = window.innerHeight - 44; // 36px button + 8px margin from bottom
    return (
      <div className="w-screen h-screen bg-transparent relative overflow-hidden font-sans pointer-events-none">
        <button
          className="absolute w-9 h-9 bg-[var(--color-primary)] rounded-full flex items-center justify-center shadow-lg cursor-pointer pointer-events-auto transition-transform hover:scale-110 active:scale-95 z-50 outline-none"
          style={{ left: bubbleX, top: bubbleY }}
          onMouseDown={handleHeaderMouseDown}
          onClick={(e) => {
            e.stopPropagation();
            if (!dragMoved.current) {
              // Reset position to bottom-left default so the window doesn't open off-screen
              setBounds(prev => ({
                ...prev,
                ...getDefaultPosition(prev.width, prev.height),
              }));
              setViewMode('normal');
            }
          }}
          title="Restore Workspace"
        >
          <Shield className="w-4 h-4 text-[var(--color-primary-foreground)]" />
        </button>
      </div>
    );
  }

  const effectiveWidth = viewMode === 'sidebar-only' ? 64 : bounds.width;
  const effectiveCollapsed = viewMode === 'sidebar-only' ? true : isCollapsed;

  return (
    <div className="w-screen h-screen relative overflow-hidden font-sans pointer-events-none bg-transparent">
      
      {/* ── Floating Window ─────────────────────────────────── */}
      <div
        ref={windowRef}
        className={`absolute pointer-events-auto bg-[var(--color-bg)] rounded-xl shadow-2xl shadow-black/50 border border-[var(--color-border)] flex flex-col overflow-hidden transition-[border-radius,width] duration-200 ${
          isMaximized ? 'inset-0 !rounded-none !border-none !w-full !h-full' : ''
        }`}
        style={!isMaximized ? { left: bounds.x, top: bounds.y, width: effectiveWidth, height: bounds.height } : {}}
      >
        
        {/* Resize Handles */}
        {!isMaximized && viewMode === 'normal' && (
          <>
            <div onMouseDown={(e) => handleResizeMouseDown(e, 'right')} className="absolute top-0 right-0 w-2 h-full cursor-col-resize z-50 hover:bg-blue-500/10 transition-colors" />
            <div onMouseDown={(e) => handleResizeMouseDown(e, 'bottom')} className="absolute bottom-0 left-0 w-full h-2 cursor-row-resize z-50 hover:bg-blue-500/10 transition-colors" />
            <div onMouseDown={(e) => handleResizeMouseDown(e, 'br')} className="absolute bottom-0 right-0 w-4 h-4 cursor-nwse-resize z-50 hover:bg-blue-500/20 transition-colors" />
          </>
        )}

        {/* ── Window Body: Sidebar + Content in one flex row ──── */}
        <div className="flex-1 flex min-h-0 bg-[var(--color-bg)]">
          
          {/* Sidebar */}
          <aside className={`flex-shrink-0 bg-[var(--color-surface)] border-r border-[var(--color-border)] flex flex-col transition-all duration-300 ${viewMode === 'sidebar-only' ? 'w-full' : (effectiveCollapsed ? 'w-14' : 'w-56')}`}>
            
            {/* Sidebar Header — "⚡ App" + collapse button (same row height as content header) */}
            <div 
              className={`h-14 border-b border-[var(--color-border)] flex items-center shrink-0 ${viewMode === 'sidebar-only' ? 'cursor-move' : ''} ${effectiveCollapsed ? 'justify-center' : 'px-3'}`}
              onMouseDown={viewMode === 'sidebar-only' ? handleHeaderMouseDown : undefined}
            >
              {!effectiveCollapsed && (
                <span className="text-base font-bold text-[var(--color-text)] truncate pl-1 flex-1">⚡ App</span>
              )}
               <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSidebarToggle();
                  }}
                  className="flex w-9 h-9 items-center justify-center rounded-md border border-transparent hover:border-[var(--color-border)] hover:bg-[var(--color-primary-light)] text-[var(--color-text-secondary)] transition-all cursor-pointer outline-none"
                  title={effectiveCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <rect width="18" height="18" x="3" y="3" rx="2" />
                    <path d="M9 3v18" />
                    <path d={effectiveCollapsed ? "m14 9 3 3-3 3" : "m17 15-3-3 3-3"} />
                  </svg>
                </button>
            </div>

            {/* Nav Items */}
            <nav className={`flex-1 space-y-1 overflow-y-auto ${effectiveCollapsed ? 'p-2' : 'p-3'}`}>
              {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveNav(id)}
                  className={`w-full flex items-center py-2 rounded-md text-sm font-medium transition-all cursor-pointer outline-none ${
                    activeNav === id
                      ? 'bg-[var(--color-primary-light)] text-[var(--color-primary)]'
                      : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg)] hover:text-[var(--color-text)]'
                  } ${effectiveCollapsed ? 'justify-center px-0 gap-0' : 'px-3 gap-3'}`}
                  title={effectiveCollapsed ? label : undefined}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {!effectiveCollapsed && <span className="truncate">{label}</span>}
                </button>
              ))}
            </nav>

            {/* Bottom Theme Panel */}
            <div className="border-t border-[var(--color-border)] p-2 shrink-0">
              <UserMenu collapsed={effectiveCollapsed} />
            </div>
          </aside>

          {/* Main Content Column */}
          {viewMode === 'normal' && (
            <div className="flex-1 flex flex-col min-w-0">
              {/* Content Header — same row height as sidebar header, draggable */}
              <header 
                onMouseDown={handleHeaderMouseDown}
                className={`h-14 px-4 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] select-none shrink-0 ${!isMaximized ? 'cursor-move' : ''}`}
              >
                {/* Page title + subtitle */}
                <div className="flex flex-col justify-center min-w-0">
                  <span className="text-sm font-bold tracking-tight capitalize text-[var(--color-text)] truncate">{activeNav.replace('-', ' ')}</span>
                  <span className="text-[11px] text-[var(--color-text-muted)] truncate">Ready-made extension scaffold</span>
                </div>

                {/* Window Controls */}
                <div className="flex items-center gap-1.5" onMouseDown={e => e.stopPropagation()}>
                  <button
                    onClick={() => setViewMode('sidebar-only')}
                    className="p-1.5 rounded-md hover:bg-[var(--color-input)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer outline-none"
                    title="Minimize to Sidebar"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setIsMaximized(!isMaximized)}
                    className="p-1.5 rounded-md hover:bg-[var(--color-input)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer outline-none"
                    title={isMaximized ? "Restore" : "Maximize"}
                  >
                    {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    onClick={() => setViewMode('bubble')}
                    className="p-1.5 rounded-md hover:bg-red-500 hover:text-white text-[var(--color-text-muted)] transition-colors cursor-pointer outline-none"
                    title="Minimize to Bubble"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </header>

              {/* Scrollable Content Area */}
              <main className="flex-1 overflow-y-auto p-6 text-[var(--color-text)]">
                {activeNav === 'service-1' && <ServicePage title="Service 1" description="Connect your first service logic here. This is a ready-made extension scaffold." />}
                {activeNav === 'service-2' && <ServicePage title="Service 2" description="Connect your second service logic here. Extend with any API or feature." />}
                {activeNav === 'service-3' && <ServicePage title="Service 3" description="Connect your third service logic here. Add more services as needed." />}
              </main>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

/* ── Service Page (Generic Placeholder) ──────────────────────── */
function ServicePage({ title, description }: { title: string; description: string }) {
  const cards = [
    { label: 'Status', value: 'Ready', icon: Terminal, color: 'var(--color-success)' },
    { label: 'Sync', value: 'Idle', icon: RefreshCw, color: 'var(--color-warning)' },
    { label: 'Security', value: 'Protected', icon: Shield, color: 'var(--color-primary)' },
  ];

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[var(--color-border-hover)] transition-colors shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">{label}</span>
              <Icon className="w-4 h-4" style={{ color }} />
            </div>
            <p className="text-lg font-bold">{value}</p>
          </div>
        ))}
      </div>

      {/* Info Card */}
      <div className="p-6 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] shadow-sm">
        <h2 className="text-base font-bold mb-2">{title}</h2>
        <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">{description}</p>
      </div>
    </div>
  );
}
