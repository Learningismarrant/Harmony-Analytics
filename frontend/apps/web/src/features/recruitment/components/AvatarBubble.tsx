"use client";

export function AvatarBubble({ name }: { name: string }) {
  return (
    <div className="w-8 h-8 rounded-full bg-brand-primary/15 border border-brand-primary/25
                    flex items-center justify-center shrink-0">
      <span className="text-brand-primary text-sm font-semibold">
        {name.charAt(0).toUpperCase()}
      </span>
    </div>
  );
}
