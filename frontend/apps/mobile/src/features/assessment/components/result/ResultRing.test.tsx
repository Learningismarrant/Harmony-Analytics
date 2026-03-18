import React from "react";
import { render } from "@testing-library/react-native";
import { ResultRing } from "./ResultRing";

describe("ResultRing — score display", () => {
  it("shows the score value", () => {
    const { getByText } = render(<ResultRing score={85} />);
    expect(getByText("85")).toBeTruthy();
  });

  it("shows '/ 100' suffix", () => {
    const { getByText } = render(<ResultRing score={60} />);
    expect(getByText("/ 100")).toBeTruthy();
  });
});

describe("ResultRing — level thresholds", () => {
  it("score >= 75 → Excellent", () => {
    const { getByText } = render(<ResultRing score={75} />);
    expect(getByText("Excellent")).toBeTruthy();
  });

  it("score 55–74 → Good", () => {
    const { getByText } = render(<ResultRing score={55} />);
    expect(getByText("Good")).toBeTruthy();
  });

  it("score < 55 → In progress", () => {
    const { getByText } = render(<ResultRing score={40} />);
    expect(getByText("In progress")).toBeTruthy();
  });

  it("score 100 → Excellent", () => {
    const { getByText } = render(<ResultRing score={100} />);
    expect(getByText("Excellent")).toBeTruthy();
  });

  it("score 0 → In progress", () => {
    const { getByText } = render(<ResultRing score={0} />);
    expect(getByText("In progress")).toBeTruthy();
  });
});
