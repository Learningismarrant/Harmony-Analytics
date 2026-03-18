import React from "react";
import { render } from "@testing-library/react-native";
import { AssessmentHeader } from "./AssessmentHeader";

describe("AssessmentHeader", () => {
  it("renders without crashing", () => {
    expect(() => render(<AssessmentHeader current={0} total={10} />)).not.toThrow();
  });

  it("renders with current at last question", () => {
    expect(() => render(<AssessmentHeader current={9} total={10} />)).not.toThrow();
  });

  it("renders when current equals total - 1 (100% fill)", () => {
    expect(() => render(<AssessmentHeader current={4} total={5} />)).not.toThrow();
  });

  it("renders with total = 1 without divide by zero crash", () => {
    expect(() => render(<AssessmentHeader current={0} total={1} />)).not.toThrow();
  });
});
