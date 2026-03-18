import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import { InstructionsView } from "./InstructionsView";

describe("InstructionsView — content", () => {
  it("renders the test name in uppercase", () => {
    const { getByText } = render(
      <InstructionsView data={{ name: "Big Five" }} onStart={jest.fn()} />,
    );
    expect(getByText("BIG FIVE")).toBeTruthy();
  });

  it("shows fallback title when name is not provided", () => {
    const { getByText } = render(<InstructionsView data={{}} onStart={jest.fn()} />);
    expect(getByText("BRIEFING DE MISSION")).toBeTruthy();
  });

  it("shows 25 MINUTES for tirt type", () => {
    const { getByText } = render(
      <InstructionsView data={{ test_type: "tirt" }} onStart={jest.fn()} />,
    );
    expect(getByText("25 MINUTES")).toBeTruthy();
  });

  it("shows 20 MINUTES for cognitive type", () => {
    const { getByText } = render(
      <InstructionsView data={{ test_type: "cognitive" }} onStart={jest.fn()} />,
    );
    expect(getByText("20 MINUTES")).toBeTruthy();
  });

  it("shows 15 MINUTES for likert type", () => {
    const { getByText } = render(
      <InstructionsView data={{ test_type: "likert" }} onStart={jest.fn()} />,
    );
    expect(getByText("15 MINUTES")).toBeTruthy();
  });

  it("shows 15 MINUTES as default when test_type is undefined", () => {
    const { getByText } = render(<InstructionsView data={{}} onStart={jest.fn()} />);
    expect(getByText("15 MINUTES")).toBeTruthy();
  });

  it("renders the custom instructions text", () => {
    const { getByText } = render(
      <InstructionsView
        data={{ instructions: "Read each question carefully." }}
        onStart={jest.fn()}
      />,
    );
    expect(getByText("Read each question carefully.")).toBeTruthy();
  });

  it("renders the privacy notice", () => {
    const { getByText } = render(<InstructionsView data={{}} onStart={jest.fn()} />);
    expect(getByText(/recrutement/)).toBeTruthy();
  });

  it("renders the launch button", () => {
    const { getByText } = render(<InstructionsView data={{}} onStart={jest.fn()} />);
    expect(getByText(/LANCER/)).toBeTruthy();
  });
});

describe("InstructionsView — interaction", () => {
  it("calls onStart when the launch button is pressed", () => {
    const onStart = jest.fn();
    const { getByText } = render(<InstructionsView data={{}} onStart={onStart} />);
    fireEvent.press(getByText(/LANCER/));
    expect(onStart).toHaveBeenCalledTimes(1);
  });
});
