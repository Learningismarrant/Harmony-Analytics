"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { recruitmentApi, vesselApi } from "@harmony/api";
import type { CampaignOut, YachtPosition } from "@harmony/types";
import { SliderField } from "./SliderField";

const POSITIONS: YachtPosition[] = [
  "Captain",
  "First Mate",
  "Bosun",
  "Deckhand",
  "Chief Engineer",
  "2nd Engineer",
  "Chief Stewardess",
  "Stewardess",
  "Chef",
];

export interface NewCampaignFormProps {
  yachtId: number;
  onCreated: (campaign: CampaignOut) => void;
  onCancel: () => void;
}

export function NewCampaignForm({ yachtId, onCreated, onCancel }: NewCampaignFormProps) {
  // ── Campaign basics ──────────────────────────────────────
  const [title, setTitle]       = useState("");
  const [position, setPosition] = useState<string>(POSITIONS[3]);

  // ── JD-R Resources (R_yacht) ─────────────────────────────
  const [salaryIndex,   setSalaryIndex]   = useState(0.5);
  const [restDays,      setRestDays]      = useState(0.5);
  const [cabinRatio,    setCabinRatio]    = useState(0.5);

  // ── JD-R Demands (D_yacht) ───────────────────────────────
  const [charterIntensity,     setCharterIntensity]     = useState(0.5);
  const [managementPressure,   setManagementPressure]   = useState(0.5);

  // ── Captain leadership vector (F_lmx) ────────────────────
  const [autonomy,  setAutonomy]  = useState(0.5);
  const [feedback,  setFeedback]  = useState(0.5);
  const [structure, setStructure] = useState(0.5);

  const mutation = useMutation({
    mutationFn: async () => {
      const campaign = await recruitmentApi.createCampaign({
        title, position, yacht_id: yachtId,
      });
      // Update vessel environment (fire-and-forget — doesn't block campaign UX)
      vesselApi.updateEnvironment(yachtId, {
        salary_index:             salaryIndex,
        rest_days_ratio:          restDays,
        private_cabin_ratio:      cabinRatio,
        charter_intensity:        charterIntensity,
        management_pressure:      managementPressure,
        captain_autonomy_given:   autonomy,
        captain_feedback_style:   feedback,
        captain_structure_imposed: structure,
      }).catch(() => {/* best-effort */});
      return campaign;
    },
    onSuccess: (campaign) => onCreated(campaign),
  });

  const inputCls = "w-full bg-bg-primary border border-bg-border rounded px-2 py-1.5 \
text-xs text-text-primary placeholder:text-muted \
focus:outline-none focus:border-brand-primary transition-colors";

  const sectionCls = "text-xs font-semibold text-muted uppercase tracking-wider pt-2 pb-1 \
border-t border-bg-border";

  return (
    <div className="border-b border-bg-border bg-bg-elevated flex flex-col max-h-[70vh]">
      {/* Sticky header */}
      <div className="flex items-center justify-between px-3 py-2 shrink-0">
        <p className="text-xs font-semibold text-text-primary">New campaign</p>
        <button onClick={onCancel} className="text-muted hover:text-text-primary text-xs">✕</button>
      </div>

      {/* Scrollable body */}
      <div className="overflow-y-auto px-3 pb-3 space-y-2.5 flex-1">

        {/* ── Poste ─────────────────────────────────────────── */}
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Campaign title (min. 5 chars)"
          className={inputCls}
        />
        <select
          value={position}
          onChange={(e) => setPosition(e.target.value)}
          className={inputCls}
        >
          {POSITIONS.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        {/* ── Ressources yacht (R_yacht) ─────────────────────── */}
        <p className={sectionCls}>Vessel resources</p>
        <SliderField
          label="Compensation"
          value={salaryIndex}
          onChange={setSalaryIndex}
          leftLabel="Modest"
          rightLabel="Excellent"
        />
        <SliderField
          label="Rest days"
          value={restDays}
          onChange={setRestDays}
          leftLabel="Scarce"
          rightLabel="Generous"
        />
        <SliderField
          label="Private space"
          value={cabinRatio}
          onChange={setCabinRatio}
          leftLabel="Shared"
          rightLabel="Private cabin"
        />

        {/* ── Demandes yacht (D_yacht) ───────────────────────── */}
        <p className={sectionCls}>Vessel demands</p>
        <SliderField
          label="Charter intensity"
          value={charterIntensity}
          onChange={setCharterIntensity}
          leftLabel="Light"
          rightLabel="Intense"
        />
        <SliderField
          label="Management pressure"
          value={managementPressure}
          onChange={setManagementPressure}
          leftLabel="Relaxed"
          rightLabel="Demanding"
        />

        {/* ── Vecteur capitaine (F_lmx) ─────────────────────── */}
        <p className={sectionCls}>Captain leadership</p>
        <SliderField
          label="Autonomy given"
          value={autonomy}
          onChange={setAutonomy}
          leftLabel="Directive"
          rightLabel="Full autonomy"
        />
        <SliderField
          label="Feedback style"
          value={feedback}
          onChange={setFeedback}
          leftLabel="Silent"
          rightLabel="Active coach"
        />
        <SliderField
          label="Structure imposed"
          value={structure}
          onChange={setStructure}
          leftLabel="Flexible"
          rightLabel="Rigid process"
        />
      </div>

      {/* Sticky footer */}
      <div className="flex gap-2 px-3 py-2 border-t border-bg-border shrink-0">
        <button
          onClick={() => mutation.mutate()}
          disabled={title.trim().length < 5 || mutation.isPending}
          className="btn-primary text-xs py-1.5 px-3 flex-1 justify-center disabled:opacity-40"
        >
          {mutation.isPending ? "Creating…" : "Launch campaign"}
        </button>
      </div>
    </div>
  );
}
