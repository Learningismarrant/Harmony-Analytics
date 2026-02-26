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
  it("renders test name and description", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={jest.fn()} />,
    );
    expect(getByText("Big Five Personality")).toBeTruthy();
    expect(getByText("Measures your OCEAN profile.")).toBeTruthy();
  });

  it("shows estimated duration for likert type", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={jest.fn()} />,
    );
    expect(getByText(/~15 min/)).toBeTruthy();
  });

  it("shows points per question", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={jest.fn()} />,
    );
    expect(getByText(/5 pts\/question/)).toBeTruthy();
  });
});

describe("TestCard — completed state", () => {
  it("shows 'Completed' badge when isCompleted", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={true} onPress={jest.fn()} />,
    );
    expect(getByText("Completed")).toBeTruthy();
  });

  it("hides 'Start test' button when completed", () => {
    const { queryByText } = render(
      <TestCard test={TEST} isCompleted={true} onPress={jest.fn()} />,
    );
    expect(queryByText("Start test")).toBeNull();
  });
});

describe("TestCard — not completed state", () => {
  it("shows 'Start test' button when not completed", () => {
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={jest.fn()} />,
    );
    expect(getByText("Start test")).toBeTruthy();
  });

  it("calls onPress when 'Start test' is pressed", () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <TestCard test={TEST} isCompleted={false} onPress={onPress} />,
    );
    fireEvent.press(getByText("Start test"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });
});

describe("TestCard — unknown type fallback", () => {
  it("renders fallback icon for unknown test_type", () => {
    const unknown = { ...TEST, test_type: "unknown" as TestInfoOut["test_type"] };
    expect(() =>
      render(<TestCard test={unknown} isCompleted={false} onPress={jest.fn()} />),
    ).not.toThrow();
  });
});
