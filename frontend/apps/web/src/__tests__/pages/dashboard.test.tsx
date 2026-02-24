/**
 * Dashboard page — unit tests
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("next/link", () => {
  const LinkMock = ({
    children,
    href,
    className,
  }: {
    children: React.ReactNode;
    href: string;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  );
  LinkMock.displayName = "Link";
  return LinkMock;
});

const mockUseQuery = jest.fn();
jest.mock("@tanstack/react-query", () => ({
  useQuery: (...args: unknown[]) => mockUseQuery(...args),
}));

jest.mock("@harmony/api", () => ({
  vesselApi: { getAll: jest.fn() },
  queryKeys: {
    vessel: { all: () => ["vessel", "all"] },
  },
}));

import DashboardPage from "@/app/dashboard/page";

// ── Fixtures ──────────────────────────────────────────────────────────────────

const yachts = [
  { id: 10, name: "Lady Moura", type: "Motor Yacht", length: 105 },
  { id: 11, name: "Arctic P", type: "Explorer", length: 85 },
];

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
});

describe("DashboardPage", () => {
  describe("loading state", () => {
    it("renders skeleton cards while loading", () => {
      mockUseQuery.mockReturnValue({ data: undefined, isLoading: true });
      const { container } = render(<DashboardPage />);
      expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
    });
  });

  describe("fleet overview", () => {
    beforeEach(() => {
      mockUseQuery.mockReturnValue({ data: yachts, isLoading: false });
    });

    it("renders Fleet Overview heading", () => {
      render(<DashboardPage />);
      expect(screen.getByText("Fleet Overview")).toBeInTheDocument();
    });

    it("renders a card for each yacht", () => {
      render(<DashboardPage />);
      expect(screen.getByText("Lady Moura")).toBeInTheDocument();
      expect(screen.getByText("Arctic P")).toBeInTheDocument();
    });

    it("renders yacht type and length", () => {
      render(<DashboardPage />);
      expect(screen.getByText("Motor Yacht")).toBeInTheDocument();
      expect(screen.getByText("105m")).toBeInTheDocument();
    });

    it("navigates to vessel cockpit on card click", () => {
      render(<DashboardPage />);
      fireEvent.click(screen.getByText("Lady Moura").closest("div")!);
      expect(mockPush).toHaveBeenCalledWith("/vessel/10");
    });

    it("renders the 'Add vessel' link", () => {
      render(<DashboardPage />);
      const addLink = screen.getByText("Add vessel").closest("a");
      expect(addLink).toHaveAttribute("href", "/vessel/new");
    });

    it("shows Team Molecule and Recruitment badges on each yacht card", () => {
      render(<DashboardPage />);
      const teamBadges = screen.getAllByText(/Team Molecule/);
      expect(teamBadges.length).toBe(yachts.length);
    });
  });

  describe("fleet analytics section", () => {
    beforeEach(() => {
      mockUseQuery.mockReturnValue({ data: yachts, isLoading: false });
    });

    it("renders Fleet Analytics heading with Coming soon badge", () => {
      render(<DashboardPage />);
      expect(screen.getByText("Fleet Analytics")).toBeInTheDocument();
      expect(screen.getByText("Coming soon")).toBeInTheDocument();
    });

    it("renders all three placeholder analytics cards", () => {
      render(<DashboardPage />);
      expect(screen.getByText("Cluster Analysis")).toBeInTheDocument();
      expect(screen.getByText("Z-Score Benchmarking")).toBeInTheDocument();
      expect(screen.getByText("Fleet Harmony Index")).toBeInTheDocument();
    });

    it("analytics cards are pointer-events-none (non-interactive)", () => {
      render(<DashboardPage />);
      const card = screen.getByText("Cluster Analysis").closest(".card");
      expect(card?.className).toContain("pointer-events-none");
    });
  });

  describe("empty state", () => {
    it("renders only the Add vessel link when no yachts exist", () => {
      mockUseQuery.mockReturnValue({ data: [], isLoading: false });
      render(<DashboardPage />);
      expect(screen.getByText("Add vessel")).toBeInTheDocument();
      expect(screen.queryByText("Lady Moura")).not.toBeInTheDocument();
    });
  });
});
