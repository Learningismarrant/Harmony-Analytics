import React from "react";
import { render } from "@testing-library/react-native";
import { TirtResultDetail } from "./TirtResultDetail";
import type { TirtDetail } from "@harmony/types";

const FULL_DETAIL: TirtDetail = {
  O: { z_score: 0.45, percentile: 67.3 },
  C: { z_score: 1.18, percentile: 88.1 },
  E: { z_score: 0.3, percentile: 61.8 },
  A: { z_score: 0.55, percentile: 70.9 },
  N: { z_score: -1.12, percentile: 13.2 },
  reliability_index: 0.87,
};

const PARTIAL_DETAIL: TirtDetail = {
  C: { z_score: 1.0, percentile: 84.0 },
  reliability_index: 0.72,
};

describe("TirtResultDetail — rendering", () => {
  it("renders all domain labels when all domains are present", () => {
    const { getByText } = render(<TirtResultDetail tirtDetail={FULL_DETAIL} />);
    expect(getByText("Openness")).toBeTruthy();
    expect(getByText("Conscientiousness")).toBeTruthy();
    expect(getByText("Extraversion")).toBeTruthy();
    expect(getByText("Agreeableness")).toBeTruthy();
    expect(getByText("Neuroticism")).toBeTruthy();
  });

  it("displays percentile rounded to integer (P67, P88, etc.)", () => {
    const { getByText } = render(<TirtResultDetail tirtDetail={FULL_DETAIL} />);
    expect(getByText("P67")).toBeTruthy(); // O = 67.3 → P67
    expect(getByText("P88")).toBeTruthy(); // C = 88.1 → P88
    expect(getByText("P13")).toBeTruthy(); // N = 13.2 → P13
  });

  it("displays z-score with sign prefix for positive values", () => {
    const { getByText } = render(<TirtResultDetail tirtDetail={FULL_DETAIL} />);
    expect(getByText("z = +0.45")).toBeTruthy(); // O
    expect(getByText("z = +1.18")).toBeTruthy(); // C
  });

  it("displays z-score with negative sign for negative values", () => {
    const { getByText } = render(<TirtResultDetail tirtDetail={FULL_DETAIL} />);
    expect(getByText("z = -1.12")).toBeTruthy(); // N
  });

  it("shows 'Reliable' badge when reliability_index >= 0.80", () => {
    const { getByText } = render(<TirtResultDetail tirtDetail={FULL_DETAIL} />);
    expect(getByText("Reliable")).toBeTruthy();
  });

  it("shows 'Low reliability' badge when reliability_index < 0.80", () => {
    const { getByText } = render(<TirtResultDetail tirtDetail={PARTIAL_DETAIL} />);
    expect(getByText("Low reliability")).toBeTruthy();
  });

  it("does not render absent domain rows", () => {
    const { queryByText } = render(<TirtResultDetail tirtDetail={PARTIAL_DETAIL} />);
    expect(queryByText("Openness")).toBeNull();
    expect(queryByText("Extraversion")).toBeNull();
    expect(queryByText("Agreeableness")).toBeNull();
    expect(queryByText("Neuroticism")).toBeNull();
  });

  it("renders only the present domain in partial detail", () => {
    const { getByText } = render(<TirtResultDetail tirtDetail={PARTIAL_DETAIL} />);
    expect(getByText("Conscientiousness")).toBeTruthy();
    expect(getByText("P84")).toBeTruthy();
  });
});
