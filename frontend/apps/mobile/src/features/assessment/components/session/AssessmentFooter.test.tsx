import React from "react";
import { render } from "@testing-library/react-native";
import { AssessmentFooter } from "./AssessmentFooter";

describe("AssessmentFooter", () => {
  it("renders the brand name", () => {
    const { getByText } = render(<AssessmentFooter />);
    expect(getByText("HARMONY ASSESSMENT SYSTEM")).toBeTruthy();
  });

  it("renders the engine version", () => {
    const { getByText } = render(<AssessmentFooter />);
    expect(getByText("SECURE ENGINE v1.0")).toBeTruthy();
  });

  it("renders without crashing", () => {
    expect(() => render(<AssessmentFooter />)).not.toThrow();
  });
});
