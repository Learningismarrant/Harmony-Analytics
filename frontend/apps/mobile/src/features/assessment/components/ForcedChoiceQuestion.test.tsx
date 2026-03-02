import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { ForcedChoiceQuestion } from "./ForcedChoiceQuestion";
import type { QuestionOut } from "@harmony/types";

const Q_FORCED: QuestionOut = {
  id: 5,
  test_id: 3,
  text: "P01",
  question_type: "tirt",
  trait: "C_vs_A",
  options: [
    {
      side: "left",
      ipip_id: "C1_5",
      domain: "C",
      facet: "C1",
      score_weight: 1,
      text: {
        fr: "Je mène mes missions avec succès.",
        en: "I complete my missions successfully.",
      },
    },
    {
      side: "right",
      ipip_id: "A3_76",
      domain: "A",
      facet: "A3",
      score_weight: 1,
      text: {
        fr: "J'anticipe les besoins de mes collègues.",
        en: "I anticipate my colleagues' needs.",
      },
    },
  ],
};

const Q_NO_OPTIONS: QuestionOut = {
  id: 6,
  test_id: 3,
  text: "P02",
  question_type: "tirt",
  trait: null,
  options: null,
};

describe("ForcedChoiceQuestion — rendering", () => {
  it("renders the French text of both options", () => {
    const { getByText } = render(
      <ForcedChoiceQuestion question={Q_FORCED} selectedValue={undefined} onSelect={jest.fn()} />,
    );
    expect(getByText("Je mène mes missions avec succès.")).toBeTruthy();
    expect(getByText("J'anticipe les besoins de mes collègues.")).toBeTruthy();
  });

  it("does not show domain labels during test passation (prevents respondent bias)", () => {
    const { queryByText } = render(
      <ForcedChoiceQuestion question={Q_FORCED} selectedValue={undefined} onSelect={jest.fn()} />,
    );
    expect(queryByText(/Conscientiousness/)).toBeNull();
    expect(queryByText(/Agreeableness/)).toBeNull();
  });

  it("renders fallback when options is null", () => {
    const { getByText } = render(
      <ForcedChoiceQuestion question={Q_NO_OPTIONS} selectedValue={undefined} onSelect={jest.fn()} />,
    );
    expect(getByText("Options unavailable")).toBeTruthy();
  });

  it("renders without crashing when an option is already selected", () => {
    expect(() =>
      render(
        <ForcedChoiceQuestion question={Q_FORCED} selectedValue="left" onSelect={jest.fn()} />,
      ),
    ).not.toThrow();
  });
});

describe("ForcedChoiceQuestion — interaction", () => {
  it("calls onSelect with (questionId, 'left') when left card is pressed", () => {
    const onSelect = jest.fn();
    const { getByText } = render(
      <ForcedChoiceQuestion question={Q_FORCED} selectedValue={undefined} onSelect={onSelect} />,
    );
    fireEvent.press(getByText("Je mène mes missions avec succès."));
    expect(onSelect).toHaveBeenCalledWith(5, "left");
  });

  it("calls onSelect with (questionId, 'right') when right card is pressed", () => {
    const onSelect = jest.fn();
    const { getByText } = render(
      <ForcedChoiceQuestion question={Q_FORCED} selectedValue={undefined} onSelect={onSelect} />,
    );
    fireEvent.press(getByText("J'anticipe les besoins de mes collègues."));
    expect(onSelect).toHaveBeenCalledWith(5, "right");
  });

  it("calls onSelect exactly once per press", () => {
    const onSelect = jest.fn();
    const { getByText } = render(
      <ForcedChoiceQuestion question={Q_FORCED} selectedValue={undefined} onSelect={onSelect} />,
    );
    fireEvent.press(getByText("Je mène mes missions avec succès."));
    fireEvent.press(getByText("J'anticipe les besoins de mes collègues."));
    expect(onSelect).toHaveBeenCalledTimes(2);
  });
});
