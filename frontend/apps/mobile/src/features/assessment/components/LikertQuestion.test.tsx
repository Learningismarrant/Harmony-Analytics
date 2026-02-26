import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { LikertQuestion } from "./LikertQuestion";
import type { QuestionOut } from "@harmony/types";

const Q: QuestionOut = {
  id: 1,
  text: "How engaged are you at work?",
  options: ["Not at all", "Slightly", "Moderately", "Very", "Extremely"],
};

const Q_NO_OPTIONS: QuestionOut = {
  id: 2,
  text: "Describe your leadership style.",
  options: null,
};

describe("LikertQuestion", () => {
  it("renders all provided options", () => {
    const { getByText } = render(
      <LikertQuestion question={Q} selectedValue={undefined} onSelect={jest.fn()} />,
    );
    expect(getByText("Not at all")).toBeTruthy();
    expect(getByText("Slightly")).toBeTruthy();
    expect(getByText("Extremely")).toBeTruthy();
  });

  it("falls back to DEFAULT_OPTIONS when options is null", () => {
    const { getByText } = render(
      <LikertQuestion question={Q_NO_OPTIONS} selectedValue={undefined} onSelect={jest.fn()} />,
    );
    expect(getByText("Strongly disagree")).toBeTruthy();
    expect(getByText("Strongly agree")).toBeTruthy();
  });

  it("calls onSelect with (questionId, '1-based index string') when pressed", () => {
    const onSelect = jest.fn();
    const { getByText } = render(
      <LikertQuestion question={Q} selectedValue={undefined} onSelect={onSelect} />,
    );
    fireEvent.press(getByText("Moderately")); // index 2 → value "3"
    expect(onSelect).toHaveBeenCalledWith(1, "3");
  });

  it("calls onSelect with index '1' for the first option", () => {
    const onSelect = jest.fn();
    const { getByText } = render(
      <LikertQuestion question={Q} selectedValue={undefined} onSelect={onSelect} />,
    );
    fireEvent.press(getByText("Not at all"));
    expect(onSelect).toHaveBeenCalledWith(1, "1");
  });

  it("renders without errors when an option is already selected", () => {
    expect(() =>
      render(<LikertQuestion question={Q} selectedValue="2" onSelect={jest.fn()} />),
    ).not.toThrow();
  });
});
