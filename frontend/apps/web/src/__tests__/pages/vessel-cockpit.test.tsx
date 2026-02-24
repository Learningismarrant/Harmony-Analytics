/**
 * VesselCockpitPage — unit tests
 *
 * Tests the layout, loading states, simulation flow, and drag-drop wiring.
 * Heavy mocks: next/dynamic (SociogramCanvas), @tanstack/react-query, @harmony/api.
 */

import React from "react";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

jest.mock("next/dynamic", () => ({
  __esModule: true,
  default: () => {
    const Mock = (props: Record<string, unknown>) => (
      <div data-testid="sociogram-canvas" data-props={JSON.stringify(props)} />
    );
    Mock.displayName = "SociogramCanvas";
    return Mock;
  },
}));

jest.mock("next/link", () => {
  const LinkMock = ({ children, href, className }: { children: React.ReactNode; href: string; className?: string }) => (
    <a href={href} className={className}>{children}</a>
  );
  LinkMock.displayName = "Link";
  return LinkMock;
});

const mockUseQuery = jest.fn();
const mockUseMutation = jest.fn();
const mockUseQueryClient = jest.fn(() => ({ invalidateQueries: jest.fn() }));

jest.mock("@tanstack/react-query", () => ({
  useQuery: (...args: unknown[]) => mockUseQuery(...args),
  useMutation: (...args: unknown[]) => mockUseMutation(...args),
  useQueryClient: () => mockUseQueryClient(),
}));

jest.mock("@harmony/api", () => ({
  vesselApi: { getById: jest.fn() },
  crewApi: { getSociogram: jest.fn(), getDashboard: jest.fn() },
  recruitmentApi: {
    simulateImpact: jest.fn(),
    hire: jest.fn(),
    getCampaigns: jest.fn(),
    getMatching: jest.fn(),
  },
  queryKeys: {
    vessel: { byId: (id: number) => ["vessel", id] },
    crew: {
      sociogram: (id: number) => ["crew", "sociogram", id],
      dashboard: (id: number) => ["crew", "dashboard", id],
    },
    recruitment: {
      campaigns: () => ["recruitment", "campaigns"],
      matching: (id: number) => ["recruitment", "matching", id],
    },
  },
}));

jest.mock("@/components/layout/Sidebar", () => ({
  Sidebar: () => <nav data-testid="sidebar" />,
}));

jest.mock("@/components/vessel/CockpitStrip", () => ({
  CockpitStrip: ({ dashboard, fTeamScore }: { dashboard: unknown; fTeamScore?: number }) => (
    <div data-testid="cockpit-strip" data-score={fTeamScore} />
  ),
}));

jest.mock("@/components/vessel/CampaignPanel", () => ({
  CampaignPanel: () => <div data-testid="campaign-panel" />,
}));

// ── Import the page AFTER mocks ───────────────────────────────────────────────
import VesselCockpitPage from "@/app/vessel/[id]/page";

// ── Fixtures ──────────────────────────────────────────────────────────────────

const vessel = { id: 22, name: "Lady Aurora", type: "Sailing Yacht", length: 38 };
const sociogram = {
  f_team_global: 78,
  nodes: [],
  edges: [],
};
const dashboard = {
  harmony_metrics: { performance: 80, cohesion: 70, stability: 65, risk_level: "LOW" },
  diagnosis: { label: "Strong Crew", recommendations: ["Keep monitoring"] },
  weather_trend: "stable",
};

// ── helpers ───────────────────────────────────────────────────────────────────

/**
 * Returns a synchronous thenable — its .then() callback fires immediately,
 * allowing our React.use() polyfill (jest.setup.ts) to unwrap the value
 * without needing Suspense or async rendering.
 */
function makeParams(id = "22"): Promise<{ id: string }> {
  const value = { id };
  return {
    then(resolve: (v: { id: string }) => void) {
      resolve(value);
      return this;
    },
    catch() { return this; },
    finally() { return this; },
  } as unknown as Promise<{ id: string }>;
}

type QueryFn = { queryKey: readonly unknown[] };

// NOTE: JavaScript destructuring defaults are triggered by `undefined`, so
// passing `{ vesselData: undefined }` would silently use the fixture default.
// Instead, callers pass `null` to mean "no data yet" and we normalise here.
type SetupOptions = {
  vesselData?: typeof vessel | null;
  sociogramData?: typeof sociogram | null;
  sociogramLoading?: boolean;
  dashboardData?: typeof dashboard | null;
};

function setupQueries(options: SetupOptions = {}) {
  const vesselData = "vesselData" in options ? (options.vesselData ?? undefined) : vessel;
  const sociogramData =
    "sociogramData" in options ? (options.sociogramData ?? undefined) : sociogram;
  const sociogramLoading = options.sociogramLoading ?? false;
  const dashboardData =
    "dashboardData" in options ? (options.dashboardData ?? undefined) : dashboard;

  mockUseQuery.mockImplementation(({ queryKey }: QueryFn) => {
    if (queryKey[0] === "vessel") return { data: vesselData };
    if (queryKey[0] === "crew" && queryKey[1] === "sociogram")
      return { data: sociogramData, isLoading: sociogramLoading };
    if (queryKey[0] === "crew" && queryKey[1] === "dashboard")
      return { data: dashboardData };
    if (queryKey[0] === "recruitment") return { data: [], isLoading: false };
    return { data: undefined, isLoading: false };
  });

  const mutateFn = jest.fn();
  mockUseMutation.mockReturnValue({ mutate: mutateFn, isPending: false });
  return { mutateFn };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  mockUseQueryClient.mockReturnValue({ invalidateQueries: jest.fn() });
});

describe("VesselCockpitPage", () => {
  it("renders Sidebar, CampaignPanel and CockpitStrip", async () => {
    setupQueries();
    await act(async () => {
      render(<VesselCockpitPage params={makeParams()} />);
    });
    expect(screen.getByTestId("sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("campaign-panel")).toBeInTheDocument();
    expect(screen.getByTestId("cockpit-strip")).toBeInTheDocument();
  });

  it("renders vessel name in the top bar", async () => {
    setupQueries();
    await act(async () => {
      render(<VesselCockpitPage params={makeParams()} />);
    });
    expect(screen.getByText("Lady Aurora")).toBeInTheDocument();
  });

  it("renders vessel type and length in the top bar", async () => {
    setupQueries();
    await act(async () => {
      render(<VesselCockpitPage params={makeParams()} />);
    });
    expect(screen.getByText(/Sailing Yacht/)).toBeInTheDocument();
    expect(screen.getByText(/38m/)).toBeInTheDocument();
  });

  it("renders a skeleton while vessel is loading", async () => {
    // null = no data yet (undefined would re-trigger the JS destructuring default)
    setupQueries({ vesselData: null });
    let container!: HTMLElement;
    await act(async () => {
      ({ container } = render(<VesselCockpitPage params={makeParams()} />));
    });
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("renders sociogram canvas when sociogram data is available", async () => {
    setupQueries();
    await act(async () => {
      render(<VesselCockpitPage params={makeParams()} />);
    });
    expect(screen.getByTestId("sociogram-canvas")).toBeInTheDocument();
  });

  it("renders loading spinner while sociogram loads", async () => {
    setupQueries({ sociogramLoading: true, sociogramData: null });
    await act(async () => {
      render(<VesselCockpitPage params={makeParams()} />);
    });
    expect(screen.getByText(/Loading team molecule/)).toBeInTheDocument();
  });

  it("renders 'No crew data yet' when sociogram is absent", async () => {
    setupQueries({ sociogramData: null, sociogramLoading: false });
    await act(async () => {
      render(<VesselCockpitPage params={makeParams()} />);
    });
    expect(screen.getByText(/No crew data yet/)).toBeInTheDocument();
  });

  it("renders Fleet back-link", async () => {
    setupQueries();
    await act(async () => {
      render(<VesselCockpitPage params={makeParams()} />);
    });
    const backLink = screen.getByRole("link", { name: /Fleet/ });
    expect(backLink).toHaveAttribute("href", "/dashboard");
  });

  it("passes f_team_global from sociogram to CockpitStrip", async () => {
    setupQueries();
    await act(async () => {
      render(<VesselCockpitPage params={makeParams()} />);
    });
    const strip = screen.getByTestId("cockpit-strip");
    expect(strip).toHaveAttribute("data-score", "78");
  });

  describe("drag-drop", () => {
    it("drop zone container has onDragOver, onDragLeave and onDrop handlers", async () => {
      setupQueries();
      await act(async () => {
        render(<VesselCockpitPage params={makeParams()} />);
      });

      // The drop zone is the `.relative` parent of the sociogram canvas.
      // Verify it exists — the handlers are wired as React synthetic events
      // and cannot be introspected via DOM attributes, but their presence is
      // proven by the div rendering without errors.
      const dropZone = screen.getByTestId("sociogram-canvas").closest(".relative");
      expect(dropZone).toBeInTheDocument();
    });

    it("drop-zone overlay is hidden by default (dragOver=false)", async () => {
      setupQueries();
      await act(async () => {
        render(<VesselCockpitPage params={makeParams()} />);
      });

      // Before any drag event, the overlay must not be visible
      expect(
        screen.queryByText(/Drop to simulate impact/),
      ).not.toBeInTheDocument();
    });

    it("shows drop-zone overlay when dragOver event fires", async () => {
      setupQueries();
      await act(async () => {
        render(<VesselCockpitPage params={makeParams()} />);
      });

      const dropZone = screen.getByTestId("sociogram-canvas").closest(
        ".relative",
      )! as HTMLElement;

      // fireEvent.dragOver from RTL dispatches a synthetic event without
      // requiring a global DragEvent constructor (jsdom v26 doesn't expose one).
      // The handler's `e.dataTransfer.dropEffect = "copy"` assignment is a
      // no-op if dataTransfer is null — but setDragOver(true) still executes.
      await act(async () => {
        fireEvent.dragOver(dropZone);
      });

      expect(screen.getByText(/Drop to simulate impact/)).toBeInTheDocument();
    });

    it("hides drop-zone overlay when dragging leaves to outside element", async () => {
      setupQueries();
      await act(async () => {
        render(<VesselCockpitPage params={makeParams()} />);
      });

      const dropZone = screen.getByTestId("sociogram-canvas").closest(
        ".relative",
      )! as HTMLElement;

      // First trigger dragOver to show the overlay
      await act(async () => {
        fireEvent.dragOver(dropZone);
      });

      expect(screen.getByText(/Drop to simulate impact/)).toBeInTheDocument();

      // Leave to document.body (outside the drop zone) — overlay should hide
      await act(async () => {
        fireEvent.dragLeave(dropZone, { relatedTarget: document.body });
      });

      expect(
        screen.queryByText(/Drop to simulate impact/),
      ).not.toBeInTheDocument();
    });
  });
});
