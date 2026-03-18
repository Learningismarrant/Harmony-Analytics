import React from "react";
import { Animated } from "react-native";
import { render, fireEvent } from "@testing-library/react-native";
import { AssessmentSuccess } from "./AssessmentSuccess";

beforeEach(() => {
  jest.spyOn(Animated, "sequence").mockReturnValue({
    start: jest.fn(),
    stop: jest.fn(),
    reset: jest.fn(),
  });
  jest.spyOn(Animated, "spring").mockReturnValue({
    start: jest.fn(),
    stop: jest.fn(),
    reset: jest.fn(),
  });
  jest.spyOn(Animated, "timing").mockReturnValue({
    start: jest.fn(),
    stop: jest.fn(),
    reset: jest.fn(),
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("AssessmentSuccess — content", () => {
  it("renders the mission title", () => {
    const { getByText } = render(<AssessmentSuccess onExit={jest.fn()} />);
    expect(getByText("MISSION ACCOMPLIE")).toBeTruthy();
  });

  it("renders the security badge", () => {
    const { getByText } = render(<AssessmentSuccess onExit={jest.fn()} />);
    expect(getByText("Données sécurisées")).toBeTruthy();
  });

  it("renders the sync badge", () => {
    const { getByText } = render(<AssessmentSuccess onExit={jest.fn()} />);
    expect(getByText("Synchro. immédiate")).toBeTruthy();
  });

  it("renders the exit button", () => {
    const { getByText } = render(<AssessmentSuccess onExit={jest.fn()} />);
    expect(getByText("RETOUR AU CENTRE")).toBeTruthy();
  });
});

describe("AssessmentSuccess — interaction", () => {
  it("calls onExit when the button is pressed", () => {
    const onExit = jest.fn();
    const { getByText } = render(<AssessmentSuccess onExit={onExit} />);
    fireEvent.press(getByText("RETOUR AU CENTRE"));
    expect(onExit).toHaveBeenCalledTimes(1);
  });
});
