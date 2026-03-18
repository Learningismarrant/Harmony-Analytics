import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { TestCard } from "./TestCard";
import type { TestInfoOut } from "@harmony/types";

const TEST: TestInfoOut = {
  id: 1,
  name: "Big Five Personality",
  description: "Measures your OCEAN profile.",
  test_type: "likert",
  max_score_per_question: 5,
};

describe("TestCard — content", () => {
  it("renders test name uppercased and description", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={jest.fn()} />,
    );
    expect(getByText("BIG FIVE PERSONALITY")).toBeTruthy();
    expect(getByText("Measures your OCEAN profile.")).toBeTruthy();
  });

  it("shows estimated duration for likert type", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={jest.fn()} />,
    );
    expect(getByText("~15 MIN")).toBeTruthy();
  });

  it("shows focus label for likert type", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={jest.fn()} />,
    );
    expect(getByText("SOFT SKILLS")).toBeTruthy();
  });
});

describe("TestCard — completed state", () => {
  it("shows 'COMPLÉTÉ' badge when isCompleted", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={true} onPress={jest.fn()} />,
    );
    expect(getByText("COMPLÉTÉ")).toBeTruthy();
  });

  it("hides 'DÉMARRER' button when completed", () => {
    const { queryByText } = render(
      <TestCard test={TEST} isCompleted={true} onPress={jest.fn()} />,
    );
    expect(queryByText("DÉMARRER")).toBeNull();
  });
});

describe("TestCard — not completed state", () => {
  it("shows 'DÉMARRER' button when not completed", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={jest.fn()} />,
    );
    expect(getByText("DÉMARRER")).toBeTruthy();
  });

  it("calls onPress when 'DÉMARRER' is pressed", () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={onPress} />,
    );
    fireEvent.press(getByText("DÉMARRER"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });
});

describe("TestCard — unknown type fallback", () => {
  it("renders without crashing for unknown test_type", () => {
    const unknown = { ...TEST, test_type: "unknown" as TestInfoOut["test_type"] };
    expect(() =>
      render(<TestCard test={unknown} isCompleted={false} onPress={jest.fn()} />),
    ).not.toThrow();
  });
});
