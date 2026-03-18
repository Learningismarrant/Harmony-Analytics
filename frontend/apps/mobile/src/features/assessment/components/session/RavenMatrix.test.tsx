import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { RavenMatrix } from "./RavenMatrix";
import type { RavenMatrixConfig } from "@harmony/types";

// ── Fixture ───────────────────────────────────────────────────────────────────

const mockConfig: RavenMatrixConfig = {
  matrix: [
    [
      { shape: "circle", size: 1, fill: "empty", count: 1 },
      { shape: "circle", size: 2, fill: "empty", count: 1 },
      { shape: "circle", size: 3, fill: "empty", count: 1 },
    ],
    [
      { shape: "square", size: 1, fill: "full", count: 1 },
      { shape: "square", size: 2, fill: "full", count: 1 },
      { shape: "square", size: 3, fill: "full", count: 1 },
    ],
    [
      { shape: "triangle", size: 1, fill: "half", count: 1 },
      { shape: "triangle", size: 2, fill: "half", count: 1 },
      null, // case manquante [2][2]
    ],
  ],
  answer_options: [
    { id: "A", shape: "circle",   size: 3, fill: "empty", count: 1 },
    { id: "B", shape: "triangle", size: 3, fill: "half",  count: 1 },
    { id: "C", shape: "diamond",  size: 3, fill: "full",  count: 1 },
    { id: "D", shape: "triangle", size: 2, fill: "half",  count: 1 },
    { id: "E", shape: "square",   size: 3, fill: "full",  count: 1 },
    { id: "F", shape: "triangle", size: 3, fill: "empty", count: 1 },
  ],
  difficulty: 1,
  rule: "shape_distribution",
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("RavenMatrix — rendu", () => {
  it("rend la grille 3x3 sans crash", () => {
    const { getByTestId } = render(
      <RavenMatrix
        config={mockConfig}
        selectedAnswer={undefined}
        onSelect={jest.fn()}
      />,
    );
    expect(getByTestId("raven-matrix")).toBeTruthy();
  });

  it("affiche 6 options de réponse", () => {
    const { getByTestId } = render(
      <RavenMatrix
        config={mockConfig}
        selectedAnswer={undefined}
        onSelect={jest.fn()}
      />,
    );
    // Vérifie que chaque option A–F est présente par son testID
    ["A", "B", "C", "D", "E", "F"].forEach((id) => {
      expect(getByTestId(`raven-option-${id}`)).toBeTruthy();
    });
  });

  it("rend sans crash si matrix contient des null", () => {
    // La fixture elle-même contient un null en [2][2] — ce test valide ce cas
    expect(() =>
      render(
        <RavenMatrix
          config={mockConfig}
          selectedAnswer={undefined}
          onSelect={jest.fn()}
        />,
      ),
    ).not.toThrow();
  });

  it("snapshot basique", () => {
    const { toJSON } = render(
      <RavenMatrix
        config={mockConfig}
        selectedAnswer={undefined}
        onSelect={jest.fn()}
      />,
    );
    expect(toJSON()).toMatchSnapshot();
  });
});

describe("RavenMatrix — interaction", () => {
  it("appelle onSelect avec l'id correct au tap", () => {
    const onSelect = jest.fn();
    const { getByTestId } = render(
      <RavenMatrix
        config={mockConfig}
        selectedAnswer={undefined}
        onSelect={onSelect}
      />,
    );
    fireEvent.press(getByTestId("raven-option-C"));
    expect(onSelect).toHaveBeenCalledWith("C");
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it("appelle onSelect avec 'A' au tap sur la première option", () => {
    const onSelect = jest.fn();
    const { getByTestId } = render(
      <RavenMatrix
        config={mockConfig}
        selectedAnswer={undefined}
        onSelect={onSelect}
      />,
    );
    fireEvent.press(getByTestId("raven-option-A"));
    expect(onSelect).toHaveBeenCalledWith("A");
  });

  it("ne déclenche pas onSelect si disabled=true", () => {
    const onSelect = jest.fn();
    const { getByTestId } = render(
      <RavenMatrix
        config={mockConfig}
        selectedAnswer={undefined}
        onSelect={onSelect}
        disabled={true}
      />,
    );
    fireEvent.press(getByTestId("raven-option-B"));
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("met en évidence l'option sélectionnée (selectedAnswer prop)", () => {
    // Vérifie que le composant accepte la prop sans crash et que l'option est
    // rendue (la bordure teak est appliquée via style — testable par accessibilityState)
    const { getByTestId } = render(
      <RavenMatrix
        config={mockConfig}
        selectedAnswer="E"
        onSelect={jest.fn()}
      />,
    );
    const optionE = getByTestId("raven-option-E");
    // accessibilityState.selected doit être true pour l'option sélectionnée
    expect(optionE.props.accessibilityState?.selected).toBe(true);
  });

  it("les options non sélectionnées ont selected=false", () => {
    const { getByTestId } = render(
      <RavenMatrix
        config={mockConfig}
        selectedAnswer="E"
        onSelect={jest.fn()}
      />,
    );
    // "A" n'est pas sélectionné
    const optionA = getByTestId("raven-option-A");
    expect(optionA.props.accessibilityState?.selected).toBe(false);
  });
});
