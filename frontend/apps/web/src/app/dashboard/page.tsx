"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { vesselApi, queryKeys } from "@harmony/api";

export default function DashboardPage() {
  const router = useRouter();
  const { data: yachts, isLoading } = useQuery({
    queryKey: queryKeys.vessel.all(),
    queryFn: () => vesselApi.getAll(),
  });

  return (
    <div className="p-6 max-w-5xl space-y-8">

      {/* ── Fleet overview ────────────────────────────────────────────────── */}
      <div>
        <div className="mb-5">
          <h1 className="text-2xl font-semibold">Fleet Overview</h1>
          <p className="text-muted text-sm mt-1">
            Select a vessel to open its cockpit — team molecule, metrics and
            recruitment in one view.
          </p>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="card h-32 animate-pulse bg-bg-elevated" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {yachts?.map((yacht) => (
              <div
                key={yacht.id}
                onClick={() => router.push(`/vessel/${yacht.id}`)}
                className="card group hover:border-brand-primary/40 hover:shadow-brand-glow
                           transition-all duration-200 cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h2 className="font-semibold group-hover:text-brand-primary transition-colors">
                      {yacht.name}
                    </h2>
                    <p className="text-xs text-muted mt-0.5">{yacht.type}</p>
                  </div>
                  <span className="text-muted text-xs">{yacht.length}m</span>
                </div>
                <div className="flex gap-2 mt-4">
                  <span className="badge badge-info text-xs">◉ Team Molecule</span>
                  <span className="badge badge-info text-xs">⊕ Recruitment</span>
                </div>
              </div>
            ))}

            <Link
              href="/vessel/new"
              className="card border-dashed flex flex-col items-center justify-center
                         h-32 text-muted hover:text-brand-primary hover:border-brand-primary/40
                         transition-all duration-200"
            >
              <span className="text-2xl mb-1">+</span>
              <span className="text-sm">Add vessel</span>
            </Link>
          </div>
        )}
      </div>

      {/* ── Fleet analytics (future) ──────────────────────────────────────── */}
      <div>
        <div className="mb-4 flex items-center gap-3">
          <h2 className="text-lg font-semibold">Fleet Analytics</h2>
          <span className="badge badge-info text-xs">Coming soon</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              icon: "⊞",
              title: "Cluster Analysis",
              desc: "Group vessels and crew by psychometric similarity. Identify outliers and high-performing clusters.",
            },
            {
              icon: "Z",
              title: "Z-Score Benchmarking",
              desc: "Compare each vessel's F_team and cohesion scores against the fleet average.",
            },
            {
              icon: "◎",
              title: "Fleet Harmony Index",
              desc: "Aggregate stability, attrition risk and performance across the whole fleet.",
            },
          ].map(({ icon, title, desc }) => (
            <div
              key={title}
              className="card opacity-50 pointer-events-none select-none"
            >
              <p className="text-2xl mb-2 text-muted">{icon}</p>
              <h3 className="font-medium text-sm mb-1">{title}</h3>
              <p className="text-xs text-muted leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
