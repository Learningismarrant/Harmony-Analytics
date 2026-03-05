import React from "react";
import { Animated } from "react-native";
import { render, fireEvent } from "@testing-library/react-native";
import { SwipePairCard } from "./SwipePairCard";
import type { ForcedChoiceOption } from "@harmony/types";

const LEFT_OPTION: ForcedChoiceOption = {
  side: "left",
  ipip_id: "C1_5",
  domain: "C",
  facet: "C1",
  score_weight: 1,
  text: { fr: "Je mène mes missions avec succès.", en: "I complete my missions." },
};

const RIGHT_OPTION: ForcedChoiceOption = {
  side: "right",
  ipip_id: "A3_76",
  domain: "A",
  facet: "A3",
  score_weight: 1,
  text: { fr: "J'anticipe les besoins.", en: "I anticipate needs." },
};

/** Fait en sorte que Animated.timing appelle son callback immédiatement. */
beforeEach(() => {
  jest.spyOn(Animated, "timing").mockImplementation(
    (value: Animated.Value | Animated.ValueXY, config: Animated.TimingAnimationConfig) =>
      ({
        start: (cb?: Animated.EndCallback) => {
          // Force la valeur finale et déclenche le callback sans délai
          if ("setValue" in value) {
            (value as Animated.Value).setValue(config.toValue as number);
          }
          cb?.({ finished: true });
        },
        stop: () => {},
        reset: () => {},
      }) as Animated.CompositeAnimation,
  );
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("SwipePairCard — rendu", () => {
  it("affiche le texte français des deux options", () => {
    const { getByText } = render(
      <SwipePairCard
        leftOption={LEFT_OPTION}
        rightOption={RIGHT_OPTION}
        selectedSide={undefined}
        onChoose={jest.fn()}
        pairIndex={0}
      />,
    );
    expect(getByText("Je mène mes missions avec succès.")).toBeTruthy();
    expect(getByText("J'anticipe les besoins.")).toBeTruthy();
  });

  it("affiche les labels A et B", () => {
    const { getAllByText } = render(
      <SwipePairCard
        leftOption={LEFT_OPTION}
        rightOption={RIGHT_OPTION}
        selectedSide={undefined}
        onChoose={jest.fn()}
        pairIndex={0}
      />,
    );
    expect(getAllByText("A").length).toBeGreaterThan(0);
    expect(getAllByText("B").length).toBeGreaterThan(0);
  });

  it("affiche le séparateur 'ou'", () => {
    const { getByText } = render(
      <SwipePairCard
        leftOption={LEFT_OPTION}
        rightOption={RIGHT_OPTION}
        selectedSide={undefined}
        onChoose={jest.fn()}
        pairIndex={0}
      />,
    );
    expect(getByText("ou")).toBeTruthy();
  });

  it("ne plante pas quand selectedSide est déjà défini", () => {
    expect(() =>
      render(
        <SwipePairCard
          leftOption={LEFT_OPTION}
          rightOption={RIGHT_OPTION}
          selectedSide="left"
          onChoose={jest.fn()}
          pairIndex={0}
        />,
      ),
    ).not.toThrow();
  });
});

describe("SwipePairCard — interaction (tap)", () => {
  it("appelle onChoose('left') au tap sur l'option A", () => {
    const onChoose = jest.fn();
    const { getByText } = render(
      <SwipePairCard
        leftOption={LEFT_OPTION}
        rightOption={RIGHT_OPTION}
        selectedSide={undefined}
        onChoose={onChoose}
        pairIndex={0}
      />,
    );
    fireEvent.press(getByText("Je mène mes missions avec succès."));
    expect(onChoose).toHaveBeenCalledWith("left");
    expect(onChoose).toHaveBeenCalledTimes(1);
  });

  it("appelle onChoose('right') au tap sur l'option B", () => {
    const onChoose = jest.fn();
    const { getByText } = render(
      <SwipePairCard
        leftOption={LEFT_OPTION}
        rightOption={RIGHT_OPTION}
        selectedSide={undefined}
        onChoose={onChoose}
        pairIndex={0}
      />,
    );
    fireEvent.press(getByText("J'anticipe les besoins."));
    expect(onChoose).toHaveBeenCalledWith("right");
    expect(onChoose).toHaveBeenCalledTimes(1);
  });

  it("ne déclenche onChoose qu'une seule fois par tap", () => {
    const onChoose = jest.fn();
    const { getByText } = render(
      <SwipePairCard
        leftOption={LEFT_OPTION}
        rightOption={RIGHT_OPTION}
        selectedSide={undefined}
        onChoose={onChoose}
        pairIndex={0}
      />,
    );
    fireEvent.press(getByText("Je mène mes missions avec succès."));
    fireEvent.press(getByText("J'anticipe les besoins."));
    expect(onChoose).toHaveBeenCalledTimes(2);
  });
});
