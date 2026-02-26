import { act } from "@testing-library/react-native";
import { useAuthStore } from "./store";
import { setAccessToken, clearAccessToken } from "@harmony/api";
import { saveRefreshToken, clearRefreshToken } from "./lib";

jest.mock("@harmony/api", () => ({
  setAccessToken: jest.fn(),
  clearAccessToken: jest.fn(),
}));

jest.mock("./lib", () => ({
  saveRefreshToken: jest.fn().mockResolvedValue(undefined),
  clearRefreshToken: jest.fn().mockResolvedValue(undefined),
}));

const RESET: Parameters<typeof useAuthStore.setState>[0] = {
  isAuthenticated: false,
  isRestoringSession: true,
  role: null,
  crewProfileId: null,
  name: null,
};

beforeEach(() => {
  useAuthStore.setState(RESET);
  jest.clearAllMocks();
});

describe("initial state", () => {
  it("starts unauthenticated with isRestoringSession = true", () => {
    const { isAuthenticated, isRestoringSession, role } = useAuthStore.getState();
    expect(isAuthenticated).toBe(false);
    expect(isRestoringSession).toBe(true);
    expect(role).toBeNull();
  });
});

describe("login", () => {
  it("sets auth fields and calls setAccessToken + saveRefreshToken", async () => {
    await act(async () => {
      await useAuthStore.getState().login({
        accessToken: "access_tok",
        refreshToken: "refresh_tok",
        role: "candidate",
        crewProfileId: 42,
        name: "Alice",
      });
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.role).toBe("candidate");
    expect(state.crewProfileId).toBe(42);
    expect(state.name).toBe("Alice");
    expect(state.isRestoringSession).toBe(false);
    expect(setAccessToken).toHaveBeenCalledWith("access_tok");
    expect(saveRefreshToken).toHaveBeenCalledWith("refresh_tok");
  });

  it("skips saveRefreshToken when no refreshToken provided", async () => {
    await act(async () => {
      await useAuthStore.getState().login({
        accessToken: "tok",
        role: "candidate",
        crewProfileId: null,
        name: "Bob",
      });
    });

    expect(saveRefreshToken).not.toHaveBeenCalled();
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });
});

describe("logout", () => {
  it("clears all auth fields and calls clearAccessToken + clearRefreshToken", async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      role: "candidate",
      crewProfileId: 7,
      name: "Alice",
    });

    await act(async () => {
      await useAuthStore.getState().logout();
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.role).toBeNull();
    expect(state.crewProfileId).toBeNull();
    expect(state.name).toBeNull();
    expect(state.isRestoringSession).toBe(false);
    expect(clearAccessToken).toHaveBeenCalled();
    expect(clearRefreshToken).toHaveBeenCalled();
  });
});

describe("setRestoringSession / setAuthenticated", () => {
  it("setRestoringSession updates the flag", () => {
    useAuthStore.getState().setRestoringSession(false);
    expect(useAuthStore.getState().isRestoringSession).toBe(false);
  });

  it("setAuthenticated updates the flag", () => {
    useAuthStore.getState().setAuthenticated(true);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });
});
