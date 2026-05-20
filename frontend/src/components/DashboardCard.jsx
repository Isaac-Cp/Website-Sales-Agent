import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, MoreHorizontal } from 'lucide-react';

const DashboardCard = ({ id, children, title, className = '' }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 100 : 'auto',
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`clay-card flex h-full flex-col group p-[var(--s-6)] ${className}`}
    >
      <div className="relative z-10 mb-[var(--s-6)] flex items-center justify-between">
        <div className="flex items-center gap-[var(--s-3)]">
          <button
            {...attributes}
            {...listeners}
            aria-label={`Drag to reorder ${title}`}
            className="cursor-grab rounded-[var(--r-sm)] p-[var(--s-2)] text-[var(--muted)] transition-all hover:bg-[var(--glass-hover)] hover:text-[var(--brand)] active:cursor-grabbing has-tooltip"
          >
            <GripVertical size={18} />
            <span className="nn-tooltip">Reorder Node</span>
          </button>
          <h2 className="text-[var(--fs-xs)] font-black uppercase tracking-widest text-[var(--ink)] opacity-80 leading-[var(--lh-tight)]">{title}</h2>
        </div>
        <div className="flex items-center gap-[var(--s-1)]">
          <div className="h-1.5 w-1.5 rounded-full bg-[var(--brand)] opacity-0 transition-opacity group-hover:opacity-100 animate-pulse shadow-[0_0_8px_var(--brand)]" />
          <button className="rounded-[var(--r-sm)] p-[var(--s-2)] text-[var(--muted)] transition-all hover:bg-[var(--glass-hover)] hover:text-[var(--ink)]">
            <MoreHorizontal size={20} />
          </button>
        </div>
      </div>
      <div className="relative z-10 flex-1 overflow-hidden">{children}</div>
    </div>
  );
};

export default DashboardCard;
