/**
 * Sidebar — unit tests
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockLogout = jest.fn();
const mockPathname = jest.fn(() => "/dashboard");

jest.mock("next/navigation", () => ({
  usePathname: () => mockPathname(),
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

jest.mock("@/features/auth/store", () => ({
  useAuthStore: (selector?: (s: { name: string | null; logout: () => void }) => unknown) => {
    const state = { name: "Captain Jack", logout: mockLogout };
    // Sidebar calls useAuthStore() with no selector — return full state object
    return selector ? selector(state) : state;
  },
}));

import { Sidebar } from "./Sidebar";

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  mockPathname.mockReturnValue("/dashboard");
});

describe("Sidebar", () => {
  it("renders the Harmony logo text", () => {
    render(<Sidebar />);
    expect(screen.getByText("Harmony")).toBeInTheDocument();
  });

  it("renders the Fleet nav item", () => {
    render(<Sidebar />);
    expect(screen.getByText("Fleet")).toBeInTheDocument();
  });

  it("Fleet link points to /dashboard", () => {
    render(<Sidebar />);
    const link = screen.getByRole("link", { name: /Fleet/ });
    expect(link).toHaveAttribute("href", "/dashboard");
  });

  it("shows active styles when pathname starts with /dashboard", () => {
    mockPathname.mockReturnValue("/dashboard");
    render(<Sidebar />);
    const link = screen.getByRole("link", { name: /Fleet/ });
    expect(link.className).toContain("text-brand-primary");
  });

  it("shows inactive styles when on a different route", () => {
    mockPathname.mockReturnValue("/vessel/1");
    render(<Sidebar />);
    const link = screen.getByRole("link", { name: /Fleet/ });
    expect(link.className).toContain("text-muted");
  });

  it("renders the user's name", () => {
    render(<Sidebar />);
    expect(screen.getByText("Captain Jack")).toBeInTheDocument();
  });

  it("calls logout when Sign out is clicked", () => {
    render(<Sidebar />);
    fireEvent.click(screen.getByText("Sign out"));
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});
