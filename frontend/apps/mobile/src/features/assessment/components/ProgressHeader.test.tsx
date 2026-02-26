import React from "react";
import { render } from "@testing-library/react-native";
import { ProgressHeader } from "./ProgressHeader";

describe("ProgressHeader", () => {
  it("shows completed / total counts", () => {
    const { getByText } = render(<ProgressHeader completed={2} total={5} />);
    expect(getByText("2 / 5")).toBeTruthy();
  });

  it("shows completion message when all tests are done", () => {
    const { getByText } = render(<ProgressHeader completed={3} total={3} />);
    expect(getByText(/All tests completed/)).toBeTruthy();
  });

  it("shows remaining count when not done", () => {
    const { getByText } = render(<ProgressHeader completed={1} total={4} />);
    expect(getByText(/3 test\(s\) remaining/)).toBeTruthy();
  });

  it("does not throw with zero total", () => {
    expect(() => render(<ProgressHeader completed={0} total={0} />)).not.toThrow();
  });
});
