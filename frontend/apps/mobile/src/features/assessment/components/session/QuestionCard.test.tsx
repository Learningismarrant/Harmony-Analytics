import React from "react";
import { render } from "@testing-library/react-native";
import { Animated } from "react-native";
import { QuestionCard } from "./QuestionCard";

describe("QuestionCard", () => {
  const defaultProps = {
    questionText: "How do you handle pressure at work?",
    questionNumber: 3,
    totalQuestions: 20,
  };

  it("renders the question text", () => {
    const { getByText } = render(<QuestionCard {...defaultProps} />);
    expect(getByText("How do you handle pressure at work?")).toBeTruthy();
  });

  it("renders the progress badge (questionNumber / totalQuestions)", () => {
    const { getByText } = render(<QuestionCard {...defaultProps} />);
    expect(getByText("3 / 20")).toBeTruthy();
  });

  it("renders without errors when animatedStyle is an Animated interpolation", () => {
    const slideAnim = new Animated.Value(0);
    const animatedStyle = {
      opacity: slideAnim.interpolate({ inputRange: [0, 1], outputRange: [1, 0] }),
      transform: [{ translateX: slideAnim.interpolate({ inputRange: [0, 1], outputRange: [0, 20] }) }],
    };
    expect(() =>
      render(<QuestionCard {...defaultProps} animatedStyle={animatedStyle} />),
    ).not.toThrow();
  });

  it("renders without animatedStyle prop", () => {
    expect(() =>
      render(<QuestionCard questionText="Single question" questionNumber={1} totalQuestions={1} />),
    ).not.toThrow();
  });
});
