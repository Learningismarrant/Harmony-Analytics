import React from "react";
import { render } from "@testing-library/react-native";
import { CalibTraitBars } from "./CalibTraitBars";
import type { CalibTraitScoreOut } from "@harmony/types";

const TRAITS: CalibTraitScoreOut[] = [
  { trait: "agreeableness", label: "Agréabilité", score: 75, n_items: 10 },
  { trait: "conscientiousness", label: "Conscienciosité", score: 55, n_items: 10 },
  { trait: "openness", label: "Ouverture", score: 30, n_items: 10 },
];

describe("CalibTraitBars — renders all trait labels", () => {
  it("renders all trait labels", () => {
    const { getByText } = render(<CalibTraitBars traits={TRAITS} />);
    expect(getByText("Agréabilité")).toBeTruthy();
    expect(getByText("Conscienciosité")).toBeTruthy();
    expect(getByText("Ouverture")).toBeTruthy();
  });

  it("affiche le score de chaque trait", () => {
    const { getByText } = render(<CalibTraitBars traits={TRAITS} />);
    expect(getByText("75")).toBeTruthy();
    expect(getByText("55")).toBeTruthy();
    expect(getByText("30")).toBeTruthy();
  });
});

describe("CalibTraitBars — applies green color for score >= 70", () => {
  it("applies green color for score >= 70", () => {
    // Score 75 → vert #2E8A5C
    const { getByText } = render(<CalibTraitBars traits={TRAITS} />);
    const scoreText = getByText("75");
    expect(scoreText.props.style).toMatchObject({ color: "#2E8A5C" });
  });

  it("applies amber color for score in [40, 70)", () => {
    const { getByText } = render(<CalibTraitBars traits={TRAITS} />);
    const scoreText = getByText("55");
    expect(scoreText.props.style).toMatchObject({ color: "#9A7030" });
  });

  it("applies red color for score < 40", () => {
    const { getByText } = render(<CalibTraitBars traits={TRAITS} />);
    const scoreText = getByText("30");
    expect(scoreText.props.style).toMatchObject({ color: "#883838" });
  });
});

describe("CalibTraitBars — état vide", () => {
  it("affiche un message si aucun trait", () => {
    const { getByText } = render(<CalibTraitBars traits={[]} />);
    expect(getByText("Aucun trait disponible.")).toBeTruthy();
  });
});
