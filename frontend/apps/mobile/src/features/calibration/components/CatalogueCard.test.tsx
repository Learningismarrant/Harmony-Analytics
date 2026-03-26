import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { CatalogueCard } from "./CatalogueCard";
import type { CalibCatalogueOut, CalibSessionOut } from "@harmony/types";

const CATALOGUE: CalibCatalogueOut = {
  id: 1,
  name: "IPIP-50",
  description: "Mesure de personnalité Big Five.",
  test_type: "likert",
  n_questions: 50,
  status: "ALPHA",
  license: "IPIP",
};

const SESSION_IN_PROGRESS: CalibSessionOut = {
  id: 10,
  calibrator_id: 1,
  catalogue_id: 1,
  status: "in_progress",
  started_at: "2026-03-21T10:00:00Z",
  completed_at: null,
};

const SESSION_COMPLETED: CalibSessionOut = {
  id: 10,
  calibrator_id: 1,
  catalogue_id: 1,
  status: "completed",
  started_at: "2026-03-21T10:00:00Z",
  completed_at: "2026-03-21T10:20:00Z",
};

describe("CatalogueCard — renders catalogue name", () => {
  it("renders catalogue name", () => {
    const { getByText } = render(
      <CatalogueCard catalogue={CATALOGUE} session={null} onPress={jest.fn()} />,
    );
    expect(getByText("IPIP-50")).toBeTruthy();
  });

  it("affiche la description", () => {
    const { getByText } = render(
      <CatalogueCard catalogue={CATALOGUE} session={null} onPress={jest.fn()} />,
    );
    expect(getByText("Mesure de personnalité Big Five.")).toBeTruthy();
  });

  it("affiche le nombre de questions", () => {
    const { getByText } = render(
      <CatalogueCard catalogue={CATALOGUE} session={null} onPress={jest.fn()} />,
    );
    expect(getByText("50 QUESTIONS")).toBeTruthy();
  });
});

describe("CatalogueCard — shows Commencer button when no session", () => {
  it("shows Commencer button when no session", () => {
    const { getByText } = render(
      <CatalogueCard catalogue={CATALOGUE} session={null} onPress={jest.fn()} />,
    );
    expect(getByText("COMMENCER")).toBeTruthy();
  });

  it("appelle onPress quand COMMENCER est pressé", () => {
    const onPress = jest.fn();
    const { getByTestId } = render(
      <CatalogueCard catalogue={CATALOGUE} session={null} onPress={onPress} />,
    );
    fireEvent.press(getByTestId("catalogue-card-1"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });
});

describe("CatalogueCard — shows Reprendre when session in progress", () => {
  it("shows Reprendre when session in progress", () => {
    const { getByText } = render(
      <CatalogueCard catalogue={CATALOGUE} session={SESSION_IN_PROGRESS} onPress={jest.fn()} />,
    );
    expect(getByText("REPRENDRE")).toBeTruthy();
  });

  it("n'affiche pas COMMENCER si session en cours", () => {
    const { queryByText } = render(
      <CatalogueCard catalogue={CATALOGUE} session={SESSION_IN_PROGRESS} onPress={jest.fn()} />,
    );
    expect(queryByText("COMMENCER")).toBeNull();
  });
});

describe("CatalogueCard — shows Complété badge when session completed", () => {
  it("shows Complété badge when session completed", () => {
    const { getByText } = render(
      <CatalogueCard catalogue={CATALOGUE} session={SESSION_COMPLETED} onPress={jest.fn()} />,
    );
    expect(getByText("COMPLÉTÉ")).toBeTruthy();
  });

  it("n'affiche pas COMMENCER si session complétée", () => {
    const { queryByText } = render(
      <CatalogueCard catalogue={CATALOGUE} session={SESSION_COMPLETED} onPress={jest.fn()} />,
    );
    expect(queryByText("COMMENCER")).toBeNull();
  });
});

describe("CatalogueCard — badge étalon", () => {
  it("affiche le badge ÉTALON si status=ETALON", () => {
    const etalon = { ...CATALOGUE, status: "ETALON" };
    const { getByText } = render(
      <CatalogueCard catalogue={etalon} session={null} onPress={jest.fn()} />,
    );
    expect(getByText("ÉTALON")).toBeTruthy();
  });

  it("affiche ALPHA si is_etalon=false", () => {
    const { getByText } = render(
      <CatalogueCard catalogue={CATALOGUE} session={null} onPress={jest.fn()} />,
    );
    expect(getByText("ALPHA")).toBeTruthy();
  });
});
