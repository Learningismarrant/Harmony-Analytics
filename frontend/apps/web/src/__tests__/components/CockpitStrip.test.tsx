/**
 * CockpitStrip — unit tests
 *
 * The component normalises two different schema shapes (backend vs frontend)
 * before rendering. We test both variants plus edge cases.
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { CockpitStrip } from "@/components/vessel/CockpitStrip";

// ── Fixtures ──────────────────────────────────────────────────────────────────

/** Backend schema: uses _index suffix and full_diagnosis */
const backendDashboard = {
  harmony_metrics: {
    performance_index: 82,
    cohesion_index: 67,
    stability_index: 91,
    risk_level: "LOW",
  },
  full_diagnosis: {
    crew_type: "High Performance Crew",
    recommended_action: "Maintain current structure",
    early_warning: "",
  },
  weather_trend: {
    status: "improving",
    average: 4.2,
  },
};

/** Frontend schema: uses plain names and diagnosis */
const frontendDashboard = {
  harmony_metrics: {
    performance: 55,
    cohesion: 40,
    data_quality: 30,
    risk_level: "HIGH",
  },
  diagnosis: {
    label: "Fragile Team",
    recommendations: ["Add resilience training"],
    early_warning: "Burnout risk detected",
  },
  weather_trend: "degrading",
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("CockpitStrip", () => {
  describe("loading state (no dashboard)", () => {
    it("renders skeleton placeholders when dashboard is undefined", () => {
      const { container } = render(
        <CockpitStrip dashboard={undefined} />,
      );
      // Skeleton divs have animate-pulse class
      expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
    });

    it("renders skeleton placeholders when dashboard is null", () => {
      const { container } = render(
        <CockpitStrip dashboard={null} />,
      );
      expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
    });
  });

  describe("backend schema (performance_index, full_diagnosis)", () => {
    it("renders the three metric bars with correct labels", () => {
      render(<CockpitStrip dashboard={backendDashboard} />);
      expect(screen.getByText("Performance")).toBeInTheDocument();
      expect(screen.getByText("Cohesion")).toBeInTheDocument();
      expect(screen.getByText("Stability")).toBeInTheDocument();
    });

    it("renders performance value as integer", () => {
      render(<CockpitStrip dashboard={backendDashboard} />);
      expect(screen.getByText("82")).toBeInTheDocument();
    });

    it("renders risk level badge", () => {
      render(<CockpitStrip dashboard={backendDashboard} />);
      expect(screen.getByText("LOW")).toBeInTheDocument();
    });

    it("renders weather status with icon", () => {
      render(<CockpitStrip dashboard={backendDashboard} />);
      expect(screen.getByText(/improving/)).toBeInTheDocument();
    });

    it("renders weather average", () => {
      render(<CockpitStrip dashboard={backendDashboard} />);
      expect(screen.getByText("(4.2/5)")).toBeInTheDocument();
    });

    it("renders crew type from full_diagnosis", () => {
      render(<CockpitStrip dashboard={backendDashboard} />);
      expect(screen.getByText("High Performance Crew")).toBeInTheDocument();
    });

    it("renders recommended action", () => {
      render(<CockpitStrip dashboard={backendDashboard} />);
      expect(screen.getByText("Maintain current structure")).toBeInTheDocument();
    });

    it("does NOT render early warning section when warning is empty", () => {
      render(<CockpitStrip dashboard={backendDashboard} />);
      expect(screen.queryByText(/⚠/)).not.toBeInTheDocument();
    });
  });

  describe("frontend schema (performance, diagnosis)", () => {
    it("renders performance from plain field", () => {
      render(<CockpitStrip dashboard={frontendDashboard} />);
      expect(screen.getByText("55")).toBeInTheDocument();
    });

    it("renders HIGH risk badge", () => {
      render(<CockpitStrip dashboard={frontendDashboard} />);
      expect(screen.getByText("HIGH")).toBeInTheDocument();
    });

    it("renders weather status from string value", () => {
      render(<CockpitStrip dashboard={frontendDashboard} />);
      expect(screen.getByText(/degrading/)).toBeInTheDocument();
    });

    it("renders crew type from diagnosis.label", () => {
      render(<CockpitStrip dashboard={frontendDashboard} />);
      expect(screen.getByText("Fragile Team")).toBeInTheDocument();
    });

    it("renders first recommendation from recommendations array", () => {
      render(<CockpitStrip dashboard={frontendDashboard} />);
      expect(screen.getByText("Add resilience training")).toBeInTheDocument();
    });

    it("renders early warning when present", () => {
      render(<CockpitStrip dashboard={frontendDashboard} />);
      expect(screen.getByText(/Burnout risk detected/)).toBeInTheDocument();
    });
  });

  describe("fTeamScore prop", () => {
    it("renders F_team section when fTeamScore is provided", () => {
      render(<CockpitStrip dashboard={backendDashboard} fTeamScore={73} />);
      expect(screen.getByText("73")).toBeInTheDocument();
      expect(screen.getByText("F_team")).toBeInTheDocument();
    });

    it("prefers fTeamScore prop over dashboard f_team_global", () => {
      render(
        <CockpitStrip
          dashboard={{ ...backendDashboard, f_team_global: 50 }}
          fTeamScore={90}
        />,
      );
      expect(screen.getByText("90")).toBeInTheDocument();
      expect(screen.queryByText("50")).not.toBeInTheDocument();
    });

    it("does not render F_team section when no score is available", () => {
      render(<CockpitStrip dashboard={backendDashboard} />);
      expect(screen.queryByText("F_team")).not.toBeInTheDocument();
    });
  });
});
