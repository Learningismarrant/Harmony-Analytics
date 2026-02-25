/**
 * CampaignPanel — unit tests
 *
 * We mock @tanstack/react-query, @harmony/api so no real HTTP calls are made.
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockUseQuery = jest.fn();
const mockUseMutation = jest.fn();
const mockUseQueryClient = jest.fn(() => ({ invalidateQueries: jest.fn() }));

jest.mock("@tanstack/react-query", () => ({
  useQuery: (...args: unknown[]) => mockUseQuery(...args),
  useMutation: (...args: unknown[]) => mockUseMutation(...args),
  useQueryClient: () => mockUseQueryClient(),
}));

jest.mock("@harmony/api", () => ({
  recruitmentApi: {
    getCampaigns: jest.fn(),
    getMatching: jest.fn(),
    createCampaign: jest.fn(),
    reject: jest.fn(),
  },
  queryKeys: {
    recruitment: {
      campaigns: () => ["recruitment", "campaigns"],
      matching: (id: number) => ["recruitment", "matching", id],
    },
  },
}));

import { CampaignPanel } from "./CampaignPanel";

// ── Fixtures ──────────────────────────────────────────────────────────────────

const campaign1 = {
  id: 1,
  yacht_id: 10,
  title: "Deckhand Summer",
  position: "Deckhand",
  candidate_count: 3,
  is_archived: false,
  invite_token: "inv-tok-abc",
};

const campaign2 = {
  id: 2,
  yacht_id: 10,
  title: "Captain Search",
  position: "Captain",
  candidate_count: 1,
  is_archived: false,
  invite_token: "inv-tok-xyz",
};

const candidateA = {
  crew_profile_id: 100,
  name: "Alice Martin",
  location: "Monaco",
  experience_years: 5,
  test_status: "completed" as const,
  is_pipeline_pass: true,
  filtered_at: null,
  profile_fit: {
    g_fit: 88,
    fit_label: "Excellent",
    overall_centile: 88,
    centile_by_competency: {},
    safety_level: "LOW",
    safety_flags: [],
  },
  team_integration: {
    available: true,
    y_success: 91,
    success_label: "Strong",
    p_ind: 80,
    f_team: 0.85,
    f_env: 0.78,
    f_lmx: 0.92,
    team_delta: 3.5,
    confidence: "HIGH" as const,
    reason: null,
  },
  is_hired: false,
  is_rejected: false,
  application_status: "pending",
  rejected_reason: null,
};

const candidateB = {
  crew_profile_id: 101,
  name: "Bob Durand",
  location: "Cannes",
  experience_years: 3,
  test_status: "completed" as const,
  is_pipeline_pass: true,
  filtered_at: null,
  profile_fit: {
    g_fit: 72,
    fit_label: "Good",
    overall_centile: 72,
    centile_by_competency: {},
    safety_level: "MEDIUM",
    safety_flags: ["leadership_gap"],
  },
  team_integration: {
    available: true,
    y_success: 68,
    success_label: "Moderate",
    p_ind: 60,
    f_team: 0.65,
    f_env: 0.58,
    f_lmx: 0.70,
    team_delta: -1.2,
    confidence: "LOW" as const,
    reason: null,
  },
  is_hired: false,
  is_rejected: false,
  application_status: "pending",
  rejected_reason: null,
};

// ── helpers ───────────────────────────────────────────────────────────────────

function defaultProps(overrides = {}) {
  return {
    yachtId: 10,
    activeCampaignId: null,
    onSelectCampaign: jest.fn(),
    simulatingFor: null,
    onSimulateCandidate: jest.fn(),
    ...overrides,
  };
}

function setupQueries({
  campaigns = [campaign1, campaign2],
  candidates = [] as typeof candidateA[],
  campaignsLoading = false,
  matchingLoading = false,
} = {}) {
  mockUseQuery.mockImplementation(({ queryKey }: { queryKey: string[] }) => {
    if (queryKey[0] === "recruitment" && queryKey[1] === "campaigns") {
      return { data: campaigns, isLoading: campaignsLoading };
    }
    if (queryKey[0] === "recruitment" && queryKey[1] === "matching") {
      return { data: candidates, isLoading: matchingLoading };
    }
    return { data: undefined, isLoading: false };
  });

  mockUseMutation.mockReturnValue({
    mutate: jest.fn(),
    isPending: false,
  });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  mockUseQueryClient.mockReturnValue({ invalidateQueries: jest.fn() });
});

describe("CampaignPanel", () => {
  describe("campaign list", () => {
    it("renders campaign tabs filtered by yacht_id", () => {
      const otherYachtCampaign = { ...campaign1, id: 99, yacht_id: 999 };
      setupQueries({ campaigns: [campaign1, campaign2, otherYachtCampaign] });

      render(<CampaignPanel {...defaultProps()} />);

      expect(screen.getByText("Deckhand")).toBeInTheDocument();
      expect(screen.getByText("Captain")).toBeInTheDocument();
      // Campaign from different yacht should not appear
      expect(screen.getAllByRole("button").filter(
        (b) => b.textContent?.includes("Deckhand") || b.textContent?.includes("Captain")
      ).length).toBe(2);
    });

    it("shows 'No campaigns' empty state when list is empty", () => {
      setupQueries({ campaigns: [] });
      render(<CampaignPanel {...defaultProps()} />);
      expect(screen.getByText(/No campaigns for this vessel/)).toBeInTheDocument();
    });

    it("shows loading skeletons while campaigns load", () => {
      setupQueries({ campaignsLoading: true, campaigns: [] });
      const { container } = render(<CampaignPanel {...defaultProps()} />);
      expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
    });

    it("calls onSelectCampaign with campaign id when a tab is clicked", () => {
      setupQueries();
      const onSelectCampaign = jest.fn();
      render(<CampaignPanel {...defaultProps({ onSelectCampaign })} />);

      fireEvent.click(screen.getByText("Deckhand"));
      expect(onSelectCampaign).toHaveBeenCalledWith(1);
    });

    it("calls onSelectCampaign with null to deselect active campaign", () => {
      setupQueries();
      const onSelectCampaign = jest.fn();
      render(
        <CampaignPanel
          {...defaultProps({ activeCampaignId: 1, onSelectCampaign })}
        />,
      );

      // Clicking the already-active tab deselects it
      fireEvent.click(screen.getByText("Deckhand"));
      expect(onSelectCampaign).toHaveBeenCalledWith(null);
    });
  });

  describe("empty campaign state", () => {
    it("renders 'Select a campaign' prompt when activeCampaignId is null", () => {
      setupQueries();
      render(<CampaignPanel {...defaultProps({ activeCampaignId: null })} />);
      expect(
        screen.getByText(/Select a campaign to see candidates/),
      ).toBeInTheDocument();
    });
  });

  describe("candidate list", () => {
    it("renders candidates sorted by y_success desc", () => {
      setupQueries({ candidates: [candidateB, candidateA] });

      render(
        <CampaignPanel
          {...defaultProps({ activeCampaignId: 1 })}
        />,
      );

      const names = screen.getAllByText(/Alice|Bob/).map((el) => el.textContent);
      expect(names[0]).toContain("Alice");
      expect(names[1]).toContain("Bob");
    });

    it("renders fit score and y_success for each candidate", () => {
      setupQueries({ candidates: [candidateA] });
      render(<CampaignPanel {...defaultProps({ activeCampaignId: 1 })} />);
      expect(screen.getByText("88")).toBeInTheDocument(); // g_fit (Profile Fit cell)
      // y_success is rendered as "91<span>%</span>" — find it via the surrounding text
      expect(screen.getByText(/91/)).toBeInTheDocument();
    });

    it("renders positive f_team_delta in green", () => {
      setupQueries({ candidates: [candidateA] });
      render(<CampaignPanel {...defaultProps({ activeCampaignId: 1 })} />);
      // Label and value are separate elements; value element carries the color class
      const deltaEl = screen.getByText("+3.5");
      expect(deltaEl.className).toContain("text-emerald-500");
    });

    it("renders negative f_team_delta in red", () => {
      setupQueries({ candidates: [candidateB] });
      render(<CampaignPanel {...defaultProps({ activeCampaignId: 1 })} />);
      const deltaEl = screen.getByText("-1.2");
      expect(deltaEl.className).toContain("text-red-500");
    });

    it("calls onSimulateCandidate when Simulate is clicked", () => {
      setupQueries({ candidates: [candidateA] });
      const onSimulateCandidate = jest.fn();
      render(
        <CampaignPanel
          {...defaultProps({ activeCampaignId: 1, onSimulateCandidate })}
        />,
      );

      fireEvent.click(screen.getByText(/Simulate/));
      expect(onSimulateCandidate).toHaveBeenCalledWith(100, 1);
    });

    it("shows 'Simulating…' when isSimulating is true for that candidate", () => {
      setupQueries({ candidates: [candidateA] });
      render(
        <CampaignPanel
          {...defaultProps({ activeCampaignId: 1, simulatingFor: 100 })}
        />,
      );
      expect(screen.getByText("Simulating…")).toBeInTheDocument();
    });

    it("renders safety_flags as warning badges", () => {
      setupQueries({ candidates: [candidateB] });
      render(<CampaignPanel {...defaultProps({ activeCampaignId: 1 })} />);
      expect(screen.getByText(/leadership_gap/)).toBeInTheDocument();
    });

    it("renders empty state when no candidates", () => {
      setupQueries({ candidates: [] });
      render(<CampaignPanel {...defaultProps({ activeCampaignId: 1 })} />);
      expect(screen.getByText(/No candidates yet/)).toBeInTheDocument();
    });
  });

  describe("invite link", () => {
    it("shows invite token when active campaign is selected", () => {
      setupQueries({ candidates: [] });
      render(
        <CampaignPanel {...defaultProps({ activeCampaignId: 1 })} />,
      );
      expect(screen.getByText("inv-tok-abc")).toBeInTheDocument();
    });
  });

  describe("new campaign form", () => {
    it("shows form when '+ New' is clicked", () => {
      setupQueries();
      render(<CampaignPanel {...defaultProps()} />);
      fireEvent.click(screen.getByText("+ New"));
      expect(screen.getByPlaceholderText(/Campaign title/)).toBeInTheDocument();
    });

    it("hides form when cancel (✕) is clicked", () => {
      setupQueries();
      render(<CampaignPanel {...defaultProps()} />);
      fireEvent.click(screen.getByText("+ New"));
      // Cancel is rendered as ✕ button in the form header
      fireEvent.click(screen.getByText("✕"));
      expect(
        screen.queryByPlaceholderText(/Campaign title/),
      ).not.toBeInTheDocument();
    });

    it("Launch button is disabled when title is too short", () => {
      setupQueries();
      render(<CampaignPanel {...defaultProps()} />);
      fireEvent.click(screen.getByText("+ New"));
      const launchBtn = screen.getByRole("button", { name: /Launch campaign/ });
      expect(launchBtn).toBeDisabled();
    });
  });
});
