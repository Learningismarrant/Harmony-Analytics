/**
 * Login page — unit tests
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
const mockGet = jest.fn(() => null); // searchParams.get

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: mockGet }),
}));

jest.mock("next/link", () => {
  const LinkMock = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
  LinkMock.displayName = "Link";
  return LinkMock;
});

const mockLogin = jest.fn();
jest.mock("@/features/auth/store", () => ({
  useAuthStore: (selector: (s: { login: jest.Mock }) => unknown) =>
    selector({ login: mockLogin }),
}));

const mockAuthLogin = jest.fn();
jest.mock("@harmony/api", () => ({
  authApi: {
    login: (...args: unknown[]) => mockAuthLogin(...args),
  },
}));

import LoginPage from "@/app/(auth)/login/page";

// ── helpers ───────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  mockGet.mockReturnValue(null);
});

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("LoginPage", () => {
  it("renders email and password inputs", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("renders Sign in button", () => {
    render(<LoginPage />);
    expect(screen.getByRole("button", { name: /Sign in/ })).toBeInTheDocument();
  });

  it("renders Create account link", () => {
    render(<LoginPage />);
    expect(screen.getByText("Create account")).toBeInTheDocument();
  });

  it("shows loading state while submitting", async () => {
    mockAuthLogin.mockReturnValue(new Promise(() => {})); // never resolves

    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText("Email"), "test@test.com");
    await userEvent.type(screen.getByLabelText("Password"), "password123");
    fireEvent.click(screen.getByRole("button", { name: /Sign in/ }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Signing in/ })).toBeDisabled();
    });
  });

  it("calls authApi.login with email and password on submit", async () => {
    mockAuthLogin.mockResolvedValue({
      access_token: "at",
      refresh_token: "rt",
      role: "employer",
      user_id: 1,
      profile_id: 2,
    });

    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText("Email"), "captain@sea.com");
    await userEvent.type(screen.getByLabelText("Password"), "secure42");
    fireEvent.click(screen.getByRole("button", { name: /Sign in/ }));

    await waitFor(() => {
      expect(mockAuthLogin).toHaveBeenCalledWith("captain@sea.com", "secure42");
    });
  });

  it("calls store login and redirects to /dashboard on success", async () => {
    mockAuthLogin.mockResolvedValue({
      access_token: "at",
      refresh_token: "rt",
      role: "employer",
      user_id: 1,
      profile_id: 2,
    });

    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText("Email"), "a@b.com");
    await userEvent.type(screen.getByLabelText("Password"), "pass");
    fireEvent.click(screen.getByRole("button", { name: /Sign in/ }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("redirects to ?next param URL on success", async () => {
    mockGet.mockReturnValue("/vessel/5");
    mockAuthLogin.mockResolvedValue({
      access_token: "at",
      refresh_token: "rt",
      role: "employer",
      user_id: 1,
      profile_id: 2,
    });

    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText("Email"), "a@b.com");
    await userEvent.type(screen.getByLabelText("Password"), "pass");
    fireEvent.click(screen.getByRole("button", { name: /Sign in/ }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/vessel/5");
    });
  });

  it("shows error message on failed login", async () => {
    mockAuthLogin.mockRejectedValue(new Error("401"));

    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText("Email"), "bad@bad.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrong");
    fireEvent.click(screen.getByRole("button", { name: /Sign in/ }));

    await waitFor(() => {
      expect(
        screen.getByText("Invalid email or password."),
      ).toBeInTheDocument();
    });
  });

  it("re-enables submit button after error", async () => {
    mockAuthLogin.mockRejectedValue(new Error("401"));

    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText("Email"), "bad@bad.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrong");
    fireEvent.click(screen.getByRole("button", { name: /Sign in/ }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Sign in/ }),
      ).not.toBeDisabled();
    });
  });
});
