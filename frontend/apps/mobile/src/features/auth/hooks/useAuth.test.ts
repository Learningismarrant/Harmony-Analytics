import { renderHook } from "@testing-library/react-native";
import { useAuth } from "./useAuth";
import { useAuthStore } from "../store";

jest.mock("@harmony/api", () => ({
  setAccessToken: jest.fn(),
  clearAccessToken: jest.fn(),
}));

jest.mock("../lib", () => ({
  saveRefreshToken: jest.fn(),
  clearRefreshToken: jest.fn(),
}));

beforeEach(() => {
  useAuthStore.setState({
    isAuthenticated: false,
    isRestoringSession: false,
    role: null,
    crewProfileId: null,
    name: null,
  });
});

it("delegates to useAuthStore — returns current state", () => {
  useAuthStore.setState({
    isAuthenticated: true,
    role: "candidate",
    crewProfileId: 5,
    name: "Alice",
    isRestoringSession: false,
  });

  const { result } = renderHook(() => useAuth());

  expect(result.current.isAuthenticated).toBe(true);
  expect(result.current.role).toBe("candidate");
  expect(result.current.crewProfileId).toBe(5);
  expect(result.current.name).toBe("Alice");
});

it("exposes login and logout actions", () => {
  const { result } = renderHook(() => useAuth());
  expect(typeof result.current.login).toBe("function");
  expect(typeof result.current.logout).toBe("function");
});
